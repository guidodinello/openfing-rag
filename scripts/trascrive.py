import os
import json
from pathlib import Path
from faster_whisper import WhisperModel

# Configuration
COURSES_JSON = "firstPart.json"
INPUT_BASE_DIR = "E:\\"
OUTPUT_BASE_DIR = "videos"
WHISPER_MODEL_SIZE = "small"


def transcribe_class(wav_path, language="es"):
    """Transcribe audio file using Whisper model."""
    model = WhisperModel(
        WHISPER_MODEL_SIZE,
        compute_type="int8",
        num_workers=4,
        cpu_threads=4
    )
    
    segments, *info = model.transcribe(str(wav_path), language=language)
    
    results = []
    for segment in segments:
        results.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip()
        })
    return results

def process_file(file_path):
    """Process a single file and save transcription to JSON in output directory"""
    try:
        # Get relative path from input base directory
        rel_path = os.path.relpath(file_path, INPUT_BASE_DIR)
        
        # Create output path with same structure in output directory
        output_path = Path(OUTPUT_BASE_DIR) / Path(rel_path).with_suffix('.json')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"Processing: {file_path}")
        
        # Transcribe the file
        transcription = transcribe_class(file_path)
        
        # Save results to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(transcription, f, ensure_ascii=False, indent=2)
            
        print(f"Saved transcription to: {output_path}")
        
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")

def process_directory(directory):
    """Process all files in the given directory"""
    for filename in os.listdir(directory):
        try:
            print(filename)
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                process_file(file_path)
            else:
                process_directory(file_path)
        except:
            print(f"Error processing {filename}: {str(e)}")

def main():
    """Main function to orchestrate the transcription pipeline."""
    # Create output directory if it doesn't exist
    
    process_directory(INPUT_BASE_DIR)
    print("🎉 Todo listo.")

if __name__ == "__main__":
    main()