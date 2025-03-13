param (
    [string]$SOURCE_DIR
)

$TARGET_DIRS = @("medium", "small", "tiny", "base", "large")

# Create target directories if they don't exist
foreach ($DIR in $TARGET_DIRS) {
    $TARGET_PATH = Join-Path -Path $SOURCE_DIR -ChildPath $DIR
    if (-not (Test-Path -Path $TARGET_PATH)) {
        New-Item -ItemType Directory -Path $TARGET_PATH
    }
}

# Move files to their corresponding directories
foreach ($TARGET in $TARGET_DIRS) {
    $FILES = Get-ChildItem -Path $SOURCE_DIR -Filter "*$TARGET*"
    foreach ($FILE in $FILES) {
        if ($FILE -is [System.IO.FileInfo]) {
            $DEST_PATH = Join-Path -Path $SOURCE_DIR -ChildPath $TARGET
            Move-Item -Path $FILE.FullName -Destination $DEST_PATH
        }
    }
}