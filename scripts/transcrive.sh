#!/bin/bash

# Configuration
TARGET_FOLDER="${1:-./videos}"  # Use first argument or default to ./videos
LOG_FILE="transcription_log.txt"
WHISPER_MODEL="medium"  # Using medium model for better accuracy

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to log with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to get file size in MB
get_file_size() {
    local file="$1"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        stat -f%z "$file" | awk '{print $1/1024/1024}'
    else
        # Linux
        stat --printf="%s" "$file" | awk '{print $1/1024/1024}'
    fi
}

# Function to format duration
format_duration() {
    local duration=$1
    printf "%02d:%02d:%02d" $((duration/3600)) $((duration%3600/60)) $((duration%60))
}

# Check if required tools are installed
check_dependencies() {
    local missing_deps=()
    
    if ! command -v ffmpeg &> /dev/null; then
        missing_deps+=("ffmpeg")
    fi
    
    if ! python3 -c "import faster_whisper" &> /dev/null; then
        missing_deps+=("faster-whisper (pip install faster-whisper)")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo -e "${RED}Missing dependencies:${NC}"
        printf '%s\n' "${missing_deps[@]}"
        exit 1
    fi
}

# Main script starts here
main() {
    echo -e "${BLUE}=== MP4 to M4A Transcription Script ===${NC}"
    log_message "Script started - Target folder: $TARGET_FOLDER"
    
    # Check dependencies
    check_dependencies
    
    # Check if target folder exists
    if [ ! -d "$TARGET_FOLDER" ]; then
        echo -e "${RED}Error: Folder '$TARGET_FOLDER' does not exist${NC}"
        exit 1
    fi
    
    # Change to target directory
    cd "$TARGET_FOLDER" || exit 1
    log_message "Changed to directory: $(pwd)"
    
    # Find all MP4 files
    mapfile -t mp4_files < <(find . -maxdepth 1 -name "*.mp4" -type f)
    
    if [ ${#mp4_files[@]} -eq 0 ]; then
        echo -e "${YELLOW}No MP4 files found in $TARGET_FOLDER${NC}"
        log_message "No MP4 files found"
        exit 0
    fi
    
    echo -e "${GREEN}Found ${#mp4_files[@]} MP4 file(s)${NC}"
    log_message "Found ${#mp4_files[@]} MP4 files"
    
    total_start_time=$(date +%s)
    total_original_size=0
    total_converted_size=0
    
    # Process each MP4 file
    for mp4_file in "${mp4_files[@]}"; do
        filename=$(basename "$mp4_file" .mp4)
        m4a_file="${filename}.m4a"
        transcript_file="${filename}.txt"
        
        echo -e "\n${BLUE}Processing: $mp4_file${NC}"
        log_message "Starting processing of: $mp4_file"
        
        # Get original file size
        original_size=$(get_file_size "$mp4_file")
        total_original_size=$(echo "$total_original_size + $original_size" | bc -l)
        log_message "Original MP4 size: ${original_size} MB"
        
        # Step 1: Convert MP4 to M4A
        echo -e "${YELLOW}Converting to M4A...${NC}"
        conversion_start=$(date +%s)
        
        if ffmpeg -i "$mp4_file" -vn -acodec copy "$m4a_file" -y &> /dev/null; then
            conversion_end=$(date +%s)
            conversion_time=$((conversion_end - conversion_start))
            converted_size=$(get_file_size "$m4a_file")
            total_converted_size=$(echo "$total_converted_size + $converted_size" | bc -l)
            
            echo -e "${GREEN}✓ Conversion completed in $(format_duration $conversion_time)${NC}"
            log_message "Conversion completed - Time: $(format_duration $conversion_time), M4A size: ${converted_size} MB"
        else
            echo -e "${RED}✗ Conversion failed${NC}"
            log_message "Conversion failed for: $mp4_file"
            continue
        fi
        
        # Step 2: Transcribe using faster-whisper
        echo -e "${YELLOW}Transcribing audio...${NC}"
        transcription_start=$(date +%s)
        
        # Create Python transcription script
        cat > transcribe_with_faster_whisper.py << 'PYTHON_SCRIPT'
#!/usr/bin/env python3
import sys
import os
from faster_whisper import WhisperModel

def transcribe_audio(audio_file, output_file, model_name):
    """Transcribe audio file using faster-whisper"""
    try:
        print(f"Loading {model_name} model...", file=sys.stderr)
        model = WhisperModel(model_name, device="auto", compute_type="auto")
        
        print(f"Transcribing {audio_file}...", file=sys.stderr)
        segments, info = model.transcribe(
            audio_file, 
            beam_size=5,
            best_of=5,
            temperature=0.0
        )
        
        # Write transcription with timestamps
        with open(output_file, "w", encoding="utf-8") as f:
            for segment in segments:
                f.write(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text.strip()}\n")
        
        # Output language detection info
        print(f"Language: {info.language}, Probability: {info.language_probability:.2f}")
        print(f"Duration: {info.duration:.2f}s", file=sys.stderr)
        
        return 0
        
    except Exception as e:
        print(f"Transcription error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python transcribe_with_faster_whisper.py <audio_file> <output_file> <model_name>", file=sys.stderr)
        sys.exit(1)
    
    audio_file, output_file, model_name = sys.argv[1], sys.argv[2], sys.argv[3]
    
    if not os.path.exists(audio_file):
        print(f"Error: Audio file '{audio_file}' not found", file=sys.stderr)
        sys.exit(1)
    
    sys.exit(transcribe_audio(audio_file, output_file, model_name))
PYTHON_SCRIPT
        
        # Run transcription and capture output
        transcription_output=$(python3 transcribe_with_faster_whisper.py "$m4a_file" "$transcript_file" "$WHISPER_MODEL" 2>&1)

        transcription_exit_code=$?
        transcription_end=$(date +%s)
        transcription_time=$((transcription_end - transcription_start))
        
        if [ $transcription_exit_code -eq 0 ]; then
            transcript_size=$(get_file_size "$transcript_file")
            echo -e "${GREEN}✓ Transcription completed in $(format_duration $transcription_time)${NC}"
            log_message "Transcription completed - Time: $(format_duration $transcription_time), Transcript size: ${transcript_size} MB"
        else
            echo -e "${RED}✗ Transcription failed${NC}"
            log_message "Transcription failed for: $m4a_file"
        fi
        
        # Log summary for this file
        total_file_time=$((conversion_time + transcription_time))
        log_message "File summary - Total time: $(format_duration $total_file_time), Original: ${original_size} MB, Converted: ${converted_size} MB"
    done
    
    # Final summary
    total_end_time=$(date +%s)
    total_duration=$((total_end_time - total_start_time))
    
    echo -e "\n${BLUE}=== Processing Complete ===${NC}"
    echo -e "${GREEN}Total files processed: ${#mp4_files[@]}${NC}"
    echo -e "${GREEN}Total time: $(format_duration $total_duration)${NC}"
    echo -e "${GREEN}Total original size: $(printf "%.2f" $total_original_size) MB${NC}"
    echo -e "${GREEN}Total converted size: $(printf "%.2f" $total_converted_size) MB${NC}"
    echo -e "${GREEN}Space saved: $(printf "%.2f" $(echo "$total_original_size - $total_converted_size" | bc -l)) MB${NC}"
    
    log_message "=== FINAL SUMMARY ==="
    log_message "Total files: ${#mp4_files[@]}"
    log_message "Total duration: $(format_duration $total_duration)"
    log_message "Total original size: $(printf "%.2f" $total_original_size) MB"
    log_message "Total converted size: $(printf "%.2f" $total_converted_size) MB"
    log_message "Space saved: $(printf "%.2f" $(echo "$total_original_size - $total_converted_size" | bc -l)) MB"
    log_message "Script completed successfully"
    
    # Cleanup temporary files
    rm -f temp_transcribe.py
}

# Run main function
main "$@"