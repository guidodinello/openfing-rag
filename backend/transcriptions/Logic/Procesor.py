import os
from pathlib import Path
from Constants.Constants import TMP_DOWNLOAD_FOLDER, VIDEO_EXTENSION
from Logic.Transcriber import Transcriber
from Logic.ElasticVectorStore import ElasticVectorStore
from Logic.DTO import WhisperModelSize
from Logic.DTO import WhisperModelLanguage
from Logic.DataAccess import DataAccess

class Procesor:
    def __init__(self) -> None:
        pass

    def update_transcription(self,course_acronym:str,class_number:int, model_size:str="base",language:str="es"):
        # if not WhisperModelSize.has_value(model_size):
        #     return False, "Model Size not valid"
        # if not WhisperModelLanguage.has_value(language):
        #     return False, "Language not valid"
        self.__file_path=self.__get_video_path(course_acronym,class_number,model_size)
        if not self.__file_path.exists():
            print(self.__file_path)
            return False, "Video Not Found In OS"
        
        self.__output_path=self.__get_output_path(course_acronym,class_number,model_size)
        self.transcriber = Transcriber(
            audio_path=self.__file_path,
            output_dir=self.__output_path,
            model_size=model_size,
            language=language
        )
        a= self.transcriber.transcribe()
        return True, "Transcription Completed"
    
    def get_transcription(self,course_acronym:str,class_number:int,model_size:str="base"):
        #Check Database
        ##
        pass
    
    def proccess_transcription(self,course_acronym:str,class_number:int,model_size:str="small"):
        file_path = self.__get_output_path(course_acronym, class_number, model_size)
        if not file_path.exists():
            return False, "Transcription file not found"

        chunks = self.make_chunks(file_path)
        self.save_chunks(chunks, course_acronym, class_number, model_size)
        
    def save_chunks(self, chunks, course_acronym, class_number, model_size):
        store = ElasticVectorStore()
        store.insert_transcription(chunks, "ML101", 1, "whisper-medium")
    
    def make_chunks(self, file_path: Path):        
        with open(file_path, "r", encoding="utf-8") as f:
            import json
            transcription_data = json.load(f)
        segments = transcription_data.get("transcription", [])
        text= transcription_data.get("text")
        chunks = []
        word_count = 0

        for segment in segments:
            chunks.append(segment)
            word_count += len(segment["text"].split())

            if word_count >= 350:
                merged_text = " ".join(seg["text"] for seg in chunks)
                chunk_start = chunks[0]["offsets"]["from"]
                chunk_end = chunks[-1]["offsets"]["to"]
                # Save chunks for vectorization and storage
                chunks.append({
                    "text": merged_text,
                    "start": chunk_start,
                    "end": chunk_end,
                    "courseName": ...,
                    "classNumber": ...,
                    "modelUsed": ...
                })

                chunks = []
                word_count = 0
        return chunks


    def __get_video_path(self, course_acronym:str, class_number:int,model_size:str)->Path:
        """Generate the path where the video will be saved."""
        class_number_string = f"{class_number:02d}"
        filename = f"{course_acronym}_{class_number_string}.{VIDEO_EXTENSION}"
        return Path(TMP_DOWNLOAD_FOLDER) / course_acronym / filename
    
    def __get_output_path(self, course_acronym:str, class_number:int,model_size:str)->Path:
        """Generate the path where the transcription will be saved as a Path object."""
        class_number_string = f"{class_number:02d}"
        filename = f"{course_acronym}_{class_number_string}_{model_size}.json"

        return Path(f"{TMP_DOWNLOAD_FOLDER}/{course_acronym}/{filename}")
    

if __name__ == "__main__":
    procesor = Procesor()
    # Example usage
    is_successful, message = procesor.proccess_transcription("ac", 1, "small")
    is_successful, message = procesor.proccess_transcription("ac", 2, "small")
    is_successful, message = procesor.proccess_transcription("ac", 3, "small")
    is_successful, message = procesor.proccess_transcription("ac", 4, "small")
    is_successful, message = procesor.proccess_transcription("ac", 5, "small")
    is_successful, message = procesor.proccess_transcription("ac", 6, "small")
    is_successful, message = procesor.proccess_transcription("ac", 7, "small")
    is_successful, message = procesor.proccess_transcription("ac", 8, "small")
    is_successful, message = procesor.proccess_transcription("ac", 9, "small")
    is_successful, message = procesor.proccess_transcription("ac", 10, "small")
    is_successful, message = procesor.proccess_transcription("ac", 11, "small")
    is_successful, message = procesor.proccess_transcription("ac", 12, "small")
    is_successful, message = procesor.proccess_transcription("ac", 13, "small")
    is_successful, message = procesor.proccess_transcription("ac", 14, "small")
    print(is_successful, message)
    
    is_successful, message