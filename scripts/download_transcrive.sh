#!/bin/bash
set -e

COURSES_JSON="firstPart.json"
BASE_URL="https://open.fing.edu.uy/media"
OUTPUT_BASE_DIR="videos"
WHISPER_MODEL="$(pwd)/whisper.cpp/models/ggml-small.bin"
WHISPER_EXEC="whisper.cpp/build/bin/whisper-cli"
THREADS=4

# Verificar dependencias
for cmd in jq ffmpeg wget; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "Error: $cmd no está instalado"
        exit 1
    fi
done

if [ ! -x "$WHISPER_EXEC" ]; then
    echo "Error: $WHISPER_EXEC no es ejecutable"
    exit 1
fi

jq -r 'to_entries[] | "\(.key) \(.value.classes[])"' "$COURSES_JSON" | while read -r COURSE CLS; do
    if [ "$CLS" -lt 10 ]; then
        CLS="0$CLS"
    fi

    DEST_DIR="$OUTPUT_BASE_DIR/$COURSE"
    FILENAME="${COURSE}_${CLS}"
    VIDEO_PATH="$DEST_DIR/$FILENAME.mp4"
    WAV_PATH="$DEST_DIR/$FILENAME.wav"

    mkdir -p "$DEST_DIR"

    if [ ! -f "$VIDEO_PATH" ]; then
        echo "Descargando $VIDEO_PATH"
        wget -q -O "$VIDEO_PATH" "$BASE_URL/$COURSE/$FILENAME.mp4"

        # Verificar si el archivo es realmente un video
        if ! file "$VIDEO_PATH" | grep -qE 'ISO Media|MP4'; then
            echo "Error: $VIDEO_PATH no es un archivo de video válido. Eliminando..."
            rm "$VIDEO_PATH"
            continue
        fi
    else
        echo "Ya descargado: $VIDEO_PATH"
    fi

    echo "Convirtiendo $VIDEO_PATH a WAV..."
    ffmpeg -nostdin -y -i "$VIDEO_PATH" -ar 16000 -ac 1 -c:a pcm_s16le "$WAV_PATH"

    echo "Transcribiendo $WAV_PATH..."
    "$WHISPER_EXEC" \
        -m "$WHISPER_MODEL" \
        -f "$WAV_PATH" \
        -t "$THREADS" \
        --language Spanish \
        --output-json \
        -of "$DEST_DIR/$FILENAME"

    # Eliminar archivos temporales después de la transcripción
    echo "Limpiando archivos temporales..."
    rm "$WAV_PATH"
    rm "$VIDEO_PATH"
    # Commit y push de las transcripciones

    echo "Committing transcriptions to git..."
    git add .
    git commit -m "Add transcriptions for $(date +'%Y-%m-%d')"
    git push

done