# Define the directory containing the .mp4 files
$directory = "C:\Users\damorena\_Modulos\Facu\ProyectoDeGrado\ProyectoDeGrado\DB\Opens\pln"

# Get all .mp4 files in the directory
$mp4Files = Get-ChildItem -Path $directory -Filter *.mp4

# Iterate over each .mp4 file and run the command
foreach ($file in $mp4Files) {
    $currentItemName = $file.FullName
    # Generate the output file name with .wav extension
    $outputFileName = [System.IO.Path]::ChangeExtension($currentItemName, ".wav")
    # Run the ffmpeg command to convert .mp4 to .wav
    ffmpeg -i $currentItemName -ac 1 -ar 16000 $outputFileName
}