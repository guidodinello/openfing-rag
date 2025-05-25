#!/bin/bash

COURSES_JSON="secondPart.json"
COURSES_JSON="thierdPart.json"
BASE_URL="https://open.fing.edu.uy/media"
OUTPUT_BASE_DIR="videos"
WHISPER_MODEL="$(pwd)/whisper.cpp/models/ggml-small.bin"
WHISPER_EXEC="whisper.cpp/build/bin/whisper-cli"
THREADS=8

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
    OUTPUT="${FILENAME}_small"
    JSON_OUTPUT="$DEST_DIR/$OUTPUT.json"

    # Si ya existe el JSON, saltar todo
    if [ -f "$JSON_OUTPUT" ]; then
        echo "Ya existe transcripción para $FILENAME. Saltando todo..."
        continue
    fi

    # Si ya existe el WAV, saltar descarga y conversión
    if [ -f "$WAV_PATH" ]; then
        echo "Ya procesado: $WAV_PATH, omitiendo descarga y conversión"
    else
        mkdir -p "$DEST_DIR"
        # Si ya existe el MP4, saltar descarga
        if [ -f "$VIDEO_PATH" ]; then
            echo "Ya descargado: $VIDEO_PATH"
        else
            echo "Descargando $VIDEO_PATH"
            wget -q -O "$VIDEO_PATH" "$BASE_URL/$COURSE/$FILENAME.mp4" || { echo "Error descargando $VIDEO_PATH"; rm -f "$VIDEO_PATH"; continue; }
        fi
        # Verificar si el archivo es realmente un video válido
        if ! ffprobe -v error "$VIDEO_PATH" > /dev/null 2>&1; then
            echo "Error: $VIDEO_PATH no es un archivo de video válido. Eliminando..."
            echo "Error: $VIDEO_PATH no es un archivo de video válido. Eliminando..." >> "$DEST_DIR/error.log"
            rm -f "$VIDEO_PATH"
            continue
        fi
        echo "Convirtiendo $VIDEO_PATH a WAV..."
        ffmpeg -nostdin -y -i "$VIDEO_PATH" -ar 16000 -ac 1 -c:a pcm_s16le "$WAV_PATH" || { echo "Error convirtiendo $VIDEO_PATH a WAV"; rm -f "$WAV_PATH"; continue; }
    fi

    echo "Transcribiendo $WAV_PATH..."
    "$WHISPER_EXEC" \
        -m "$WHISPER_MODEL" \
        -f "$WAV_PATH" \
        -t "$THREADS" \
        --language Spanish \
        --output-json \
        -of "$DEST_DIR/$OUTPUT" || { echo "Error transcribiendo $WAV_PATH"; continue; }

    echo "Limpiando archivos temporales..."
    rm -f "$VIDEO_PATH"
    rm -f "$WAV_PATH"
done
