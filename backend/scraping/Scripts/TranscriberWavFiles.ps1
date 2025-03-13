# Define the path to the folder containing .wav files
$audioFolderPath = "sample_data"
$transcriptionOutputFolder = "sample_data_transcribed"

# Ensure the transcription output folder exists
if (-Not (Test-Path $transcriptionOutputFolder)) {
    New-Item -ItemType Directory -Path $transcriptionOutputFolder
}

# Define the model to use
$model = "small"

$files = Get-ChildItem -Path $audioFolderPath -Filter "*.wav"
$files | ForEach-Object {
    $audioFile = $_.FullName
    $fileNameWithoutExtension = [System.IO.Path]::GetFileNameWithoutExtension($_.Name)
    $finalOutputPath = Join-Path $transcriptionOutputFolder "$fileNameWithoutExtension`_$model.txt"

    # Check if the result file already exists
    if (Test-Path $finalOutputPath) {
        Write-Host "Transcription for $fileNameWithoutExtension using model $model already exists. Skipping..."
        return
    }

    # Start measuring time
    $startTime = Get-Date

    # Construct the whisper command to transcribe the audio
    $whisperCommand = "whisper '$audioFile' --model $model --language es --output_dir '$transcriptionOutputFolder'"

    # Run the whisper command
    Invoke-Expression $whisperCommand

    # End measuring time
    $endTime = Get-Date
    $timeTaken = $endTime - $startTime

    # Rename the generated file to include the model name
    $generatedFilePath = Join-Path $transcriptionOutputFolder "$fileNameWithoutExtension.txt"
    if (Test-Path $generatedFilePath) {
        Rename-Item -Path $generatedFilePath -NewName "$fileNameWithoutExtension`_$model.txt"
    }
    $generatedFilePath = Join-Path $transcriptionOutputFolder "$fileNameWithoutExtension.json"
    if (Test-Path $generatedFilePath) {
        Rename-Item -Path $generatedFilePath -NewName "$fileNameWithoutExtension`_$model.json"
    }
    $generatedFilePath = Join-Path $transcriptionOutputFolder "$fileNameWithoutExtension.tsv"
    if (Test-Path $generatedFilePath) {
        Rename-Item -Path $generatedFilePath -NewName "$fileNameWithoutExtension`_$model.tsv"
    }
    $generatedFilePath = Join-Path $transcriptionOutputFolder "$fileNameWithoutExtension.vtt"
    if (Test-Path $generatedFilePath) {
        Rename-Item -Path $generatedFilePath -NewName "$fileNameWithoutExtension`_$model.srt"
    }
    if (Test-Path $generatedFilePath) {
        Rename-Item -Path $generatedFilePath -NewName "$fileNameWithoutExtension`_$model.srt"
    }


    # Print the output path and time taken
    Write-Host "Transcription saved to: $finalOutputPath"
    Write-Host "Time taken for transcription: $($timeTaken.TotalSeconds) seconds"
}

Write-Host "Transcription process completed."

<th class=" valorCenEncabezado valorCenEncabezado" scope="col" style="width:7%;text-overflow: clip;">Días Etapa</th>