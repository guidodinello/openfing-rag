#!/bin/bash
#SBATCH --job-name=transcribe
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32768
#SBATCH --time=1-12:00:00
#SBATCH --gres=gpu:1
#SBATCH --partition=normal
#SBATCH --qos=gpu
#SBATCH --tmp=50G
#SBATCH --mail-type=ALL
#SBATCH --mail-user=guido.dinello@fing.edu.uy

source /etc/profile.d/modules.sh

echo "=== Transcribing Files By Size ==="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $HOSTNAME"
echo "GPU: $CUDA_VISIBLE_DEVICES"
echo "Started: $(date)"
echo "Scratch space: /scratch/$USER"
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

SCRATCH_BASE="/scratch/guido.dinello"
mkdir -p "$SCRATCH_BASE/audio_files" "$SCRATCH_BASE/models_cache" "$SCRATCH_BASE/transcriptions"

echo "=== Setting up scratch workspace ==="
echo "Scratch directory: $SCRATCH_BASE"

# Copy audio files to scratch for faster I/O
if [ -d "$HOME/audio_files_upload" ]; then
    echo "Copying audio files to scratch..."
    cp -r "$HOME/audio_files_upload/." "$SCRATCH_BASE/audio_files/" 2>/dev/null && {
        echo "✅ Copied audio files to scratch"
        echo "Files in scratch:"
        ls -la "$SCRATCH_BASE/audio_files/"
    }
else
    echo "❌ No audio files found at $HOME/audio_files_upload"
    exit 1
fi

# Show environment configuration (sanitized)
echo "=== Environment Configuration ==="
echo "WHISPER__MODEL: $(grep WHISPER__MODEL "$HOME/tesis/.env" | cut -d'=' -f2)"
echo "APP__ENV: $(grep APP__ENV "$HOME/tesis/backend/.env" | cut -d'=' -f2)"
echo "WHISPER__DEVICE: $(grep WHISPER__DEVICE "$HOME/tesis/.env" | cut -d'=' -f2)"
echo ""



echo "=== GPU Information ==="
nvidia-smi
echo ""

echo "=== Running Transcription ==="
singularity exec --nv --writable-tmpfs \
    --bind "$HOME/tesis/backend:/workspace" \
    --bind "$SCRATCH_BASE:/scratch/guido.dinello" \
    ~/transcriber-workspace/uv-container.sif bash -c "
cd /workspace

echo 'Setting up environment with pyproject.toml dependencies...'
uv sync --link-mode=copy --locked --no-dev

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

echo 'Starting transcription (processing files up to 1GB):'
uv run openchat-transcriber transcribe-by-size --largest-first --max-size 1000
"

echo "=== Results Summary ==="
echo "Transcription files created in scratch:"
find "$SCRATCH_BASE/transcriptions" -name "*.json" -exec ls -la {} \;

echo ""
echo "Total transcription files:"
find "$SCRATCH_BASE/transcriptions" -name "*.json" | wc -l

echo ""
echo "=== Moving transcription files to HOME ==="

if [ -d "$SCRATCH_BASE/transcriptions" ]; then
    mkdir -p "$HOME/transcriptions/"
    rsync -av "$SCRATCH_BASE/transcriptions/" "$HOME/transcriptions/"
    echo "✅ Moved all transcription files to HOME"
    ls -la "$HOME/transcriptions/"
else
    echo "❌ No transcription directory found at $SCRATCH_BASE/transcriptions"
fi

echo "=== Cleanup scratch space ==="
echo "Cleaning up scratch files..."
rm -rf "$SCRATCH_BASE/audio_files"/*
echo "✅ Audio files cleanup completed (keeping transcriptions and models cache)"

echo "=== Final Summary ==="
echo "Transcription files in HOME:"
find "$HOME/transcriptions/" -name "*.json" -exec ls -la {} \;
echo ""
echo "Total transcription files:"
find "$HOME/transcriptions/" -name "*.json" | wc -l

echo "Finished: $(date)"
