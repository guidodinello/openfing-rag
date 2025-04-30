#!/bin/bash

TMP_DOWNLOAD_FOLDER="../../tmp"
acronyms_path="../ScrapInfo/CoursesAcronyms.json"
scrapinfo_dir="../ScrapInfo"
openfing_url="https://open.fing.edu.uy/media"

download_video() {
  local acronym="$1"
  local class="$2"
  local padded_class
  printf -v padded_class "%02d" "$class"
  local output_file="$TMP_DOWNLOAD_FOLDER/${acronym}/${acronym}_${padded_class}.mp4"

  mkdir -p "$TMP_DOWNLOAD_FOLDER"
  curl --silent --show-error --location "$openfing_url/$acronym/${acronym}_${padded_class}.mp4" \
    --output "$output_file"

  echo "Saved to $output_file"
}

transcribe_video() {
  local acronym="$1"
  local class="$2"
  local padded_class
  printf -v padded_class "%02d" "$class"
  local video_path="$TMP_DOWNLOAD_FOLDER/${acronym}/${acronym}_${padded_class}.mp4"

  if [ ! -f "$video_path" ]; then
    echo "Video file not found: $video_path"
    return 1
  fi

  echo "Running Whisper transcription for $video_path..."
  whisper "$video_path" --language Spanish --model medium --output_dir $video_path
}

# Check for jq
if ! command -v jq &>/dev/null; then
  echo "jq is required but not installed. Exiting."
  exit 1
fi

# Read acronyms and reverse order
acronyms=$(jq -r 'keys_unsorted | reverse[]' "$acronyms_path")

for acronym_key in $acronyms; do
  class_numbers_path="$scrapinfo_dir/${acronym_key}.json"
  if [ ! -f "$class_numbers_path" ]; then
    echo "File not found: $class_numbers_path"
    continue
  fi

  class_numbers=$(jq -r '.[]' "$class_numbers_path")

  for class_number in $class_numbers; do
    echo "Downloading $acronym_key class $class_number"
    download_video "$acronym_key" "$class_number"

    echo "Transcribing $acronym_key class $class_number"
    transcribe_video "$acronym_key" "$class_number"

    echo "Done with $acronym_key class $class_number"
  done
done

echo "All downloads, transcriptions, and deletions completed."
