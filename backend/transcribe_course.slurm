#!/bin/bash
#SBATCH --job-name=transcribe
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

echo "=== Transcribing Files By Size ==="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $HOSTNAME"
echo "GPU: $CUDA_VISIBLE_DEVICES"
echo "Started: $(date)"
echo "=================================="



# Ensure container exists
CONTAINER_PATH="$HOME/transcriber-workspace/uv-container.sif"
if [ ! -f "$CONTAINER_PATH" ]; then
    echo "❌ Container not found at $CONTAINER_PATH"
    echo "Creating workspace and pulling container..."
    mkdir -p "$HOME/transcriber-workspace"
    cd "$HOME/transcriber-workspace" || exit
    singularity pull uv-container.sif docker://ghcr.io/astral-sh/uv:python3.12-bookworm
    echo "✅ Container downloaded"
else
    echo "✅ Container found at $CONTAINER_PATH"
fi

cat "$HOME/tesis/backend/.env"

mkdir -p "/scratch/$USER/audio_files" "/scratch/$USER/models_cache" "/scratch/$USER/transcriptions"

cp -r "$HOME/audio_files_upload/." "/scratch/$USER/audio_files/" 2>/dev/null && {
    echo "✅ Copied files"
}

ls -la "$HOME/audio_files_upload/**/*"

echo "=== GPU Information ==="
nvidia-smi
echo ""

echo "=== Running Transcription ==="
singularity exec --nv --writable-tmpfs \
    --bind "$HOME/tesis/backend:/workspace" \
    --bind "/scratch/$USER:/scratch/$USER" \
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
uv run openchat-transcriber transcribe-by-size --largest-first --max-size 10_000
"

echo "=== Results Summary ==="
echo "Transcription files created:"
find "/scratch/$USER/transcriptions" -name "*.json" -exec ls -la {} \;

echo ""
echo "Total transcription files:"
find "/scratch/$USER/transcriptions" -name "*.json" | wc -l


echo ""
echo "=== Moving transcription files to HOME ==="

if [ -d "/scratch/$USER/transcriptions" ]; then
    mkdir -p "$HOME/transcriptions/"
    rsync -av "/scratch/$USER/transcriptions/" "$HOME/transcriptions/"
    echo "✅ Moved all transcription files to HOME"
    ls -la "$HOME/transcriptions/"
else
    echo "❌ No transcription directory found at /scratch/$USER/transcriptions"
fi

echo "=== Moved Summary ==="
echo "Transcription files moved:"
find "$HOME/transcriptions/" -name "*.json" -exec ls -la {} \;
echo ""
echo "Total transcription files:"
find "$HOME/transcriptions/" -name "*.json" | wc -l

echo "Finished: $(date)"
