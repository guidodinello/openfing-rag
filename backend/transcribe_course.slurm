#!/bin/bash
#SBATCH --job-name=transcribe-course-direct
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16384
#SBATCH --time=3-00:00:00
#SBATCH --gres=gpu:1
#SBATCH --partition=normal
#SBATCH --qos=gpu
#SBATCH --mail-type=ALL
#SBATCH --mail-user=guido.dinello@fing.edu.uy

source /etc/profile.d/modules.sh

# Get course code from command line argument
COURSE_CODE=${1:-"ac"}

echo "=== Transcribing Course: $COURSE_CODE (Direct Bind) ==="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $HOSTNAME"
echo "GPU: $CUDA_VISIBLE_DEVICES"
echo "Started: $(date)"

# Ensure container exists
CONTAINER_PATH="~/transcriber-workspace/uv-container.sif"
if [ ! -f "$CONTAINER_PATH" ]; then
    echo "❌ Container not found at $CONTAINER_PATH"
    echo "Creating workspace and pulling container..."
    mkdir -p ~/transcriber-workspace
    cd ~/transcriber-workspace
    singularity pull uv-container.sif docker://ghcr.io/astral-sh/uv:python3.12-bookworm
    echo "✅ Container downloaded"
else
    echo "✅ Container found at $CONTAINER_PATH"
fi

# Setup environment file in the tesis backend directory
cat >~/tesis/backend/.env <<'ENVEOF'
DATABASE__USER="dummy"
DATABASE__PASSWORD="dummy"
DATABASE__DB="dummy"
DATABASE__HOST="dummy"
DATABASE__PORT=5432
HUGGINGFACE_API_KEY="dummy"
LANGSMITH_API_KEY="dummy"
LANGSMITH_TRACING=false

DEBUG=true
LOG__LEVEL="DEBUG"

TRANSCRIBER__INPUT_DIR="/scratch/guido.dinello/audio_files"
TRANSCRIBER__OUTPUT_DIR="/scratch/guido.dinello/transcriptions"
WHISPER__CACHE_DIR="/scratch/guido.dinello/models_cache"
WHISPER__MODEL="medium"
WHISPER__DEVICE="cuda"
EMBEDDINGS__MODEL="intfloat/multilingual-e5-base"
EMBEDDINGS__DIMENSION=768
EMBEDDINGS__CACHE_DIR="/scratch/guido.dinello/models_cache"
EMBEDDINGS__DEVICE="cuda"

ENVEOF

mkdir -p /scratch/$USER/audio_files/$COURSE_CODE /scratch/$USER/models_cache /scratch/$USER/transcriptions

# Copy audio files if not already there
if [ ! "$(ls -A /scratch/$USER/audio_files/$COURSE_CODE 2>/dev/null)" ]; then
    echo "Copying audio files for course $COURSE_CODE..."

    if [ -d "$HOME/audio_files_upload/$COURSE_CODE" ]; then
        echo "Found subdirectory: $HOME/audio_files_upload/$COURSE_CODE"
        cp $HOME/audio_files_upload/${COURSE_CODE}/* /scratch/$USER/audio_files/$COURSE_CODE/ 2>/dev/null && {
            echo "✅ Copied files from subdirectory"
        }
    else
        echo "❌ No audio files found for course $COURSE_CODE"
        echo "Checked:"
        echo "  - $HOME/audio_files_upload/$COURSE_CODE/"
        echo ""
        echo "Available courses in $HOME/audio_files_upload/:"
        ls -la $HOME/audio_files_upload/ | grep "^d" | awk '{print $9}' | grep -v "^\.$\|^\..$" | head -10
        exit 1
    fi
else
    echo "Audio files already in place for $COURSE_CODE"
fi

echo "Audio files to transcribe:"
ls -la /scratch/$USER/audio_files/$COURSE_CODE/

echo "=== GPU Information ==="
nvidia-smi
echo ""

echo "=== Running Transcription ==="
singularity exec --nv --writable-tmpfs \
    --bind ~/tesis/backend:/workspace \
    --bind /scratch/$USER:/scratch/$USER \
    ~/transcriber-workspace/uv-container.sif bash -c "
cd /workspace

echo 'Setting up environment with pyproject.toml dependencies...'
uv sync --link-mode=copy

echo 'Setting up CUDA library paths...'
export LD_LIBRARY_PATH=\$(uv run python -c \"
import os
try:
    import nvidia.cublas.lib
    import nvidia.cudnn.lib
    cublas_path = os.path.dirname(nvidia.cublas.lib.__file__)
    cudnn_path = os.path.dirname(nvidia.cudnn.lib.__file__)
    current_ld = os.environ.get('LD_LIBRARY_PATH', '')
    print(f'{cublas_path}:{cudnn_path}:{current_ld}')
except ImportError as e:
    print(f'Could not import nvidia libs: {e}')
    print(os.environ.get('LD_LIBRARY_PATH', ''))
\")

echo \"LD_LIBRARY_PATH: \$LD_LIBRARY_PATH\"

echo 'Testing dependencies:'
uv run python -c \"
import torch
import faster_whisper
print(f'PyTorch CUDA: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU Device: {torch.cuda.get_device_name(0)}')
    print(f'GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')
print(f'faster-whisper imported successfully')
\"

echo 'Starting transcription:'
uv run openchat-transcriber transcribe-only $COURSE_CODE
"

echo "=== Results Summary ==="
echo "Transcription files created:"
find /scratch/$USER/transcriptions -name "*.json" -exec ls -la {} \;

echo ""
echo "Total transcription files:"
find /scratch/$USER/transcriptions -name "*.json" | wc -l

# ==== MOVE FILES TO HOME DIRECTORY ====
echo ""
echo "=== Moving transcription files to ~/transcriptions/ ==="

if [ -d "/scratch/$USER/transcriptions" ]; then
    mkdir -p ~/transcriptions/
    mv /scratch/$USER/transcriptions/* ~/transcriptions/ 2>/dev/null

    echo "✅ Moved all transcription files to ~/transcriptions/"
    echo "Final directory structure:"
    ls -la ~/transcriptions/
else
    echo "❌ No transcription directory found at /scratch/$USER/transcriptions"
fi

echo "Finished: $(date)"
