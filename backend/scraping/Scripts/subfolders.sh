#!/bin/bash

SOURCE_DIR="$1"

TARGET_DIRS=("medium" "small" "tiny" "base" "large")

# Create target directories if they don't exist
for DIR in "${TARGET_DIRS[@]}"; do
    TARGET_PATH="$SOURCE_DIR/$DIR"
    if [ ! -d "$TARGET_PATH" ]; then
        mkdir -p "$TARGET_PATH"
    fi
done

# Move files to their corresponding directories
for TARGET in "${TARGET_DIRS[@]}"; do
    FILES=$(find "$SOURCE_DIR" -maxdepth 1 -type f -name "*$TARGET*")
    for FILE in $FILES; do
        DEST_PATH="$SOURCE_DIR/$TARGET"
        mv "$FILE" "$DEST_PATH"
    done
done