import os
from pathlib import Path
from Constants.Constants import TMP_DOWNLOAD_FOLDER, VIDEO_EXTENSION
from Logic.Transcriber import Transcriber
from Logic.DTO import WhisperModelSize
from Logic.DTO import WhisperModelLanguage

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

    def __get_video_path(self, course_acronym:str, class_number:int,model_size:str)->Path:
        """Generate the path where the video will be saved."""
        class_number_string = f"{class_number:02d}"
        filename = f"{course_acronym}_{class_number_string}.{VIDEO_EXTENSION}"
        return Path(TMP_DOWNLOAD_FOLDER) / course_acronym / filename
    
    def __get_output_path(self, course_acronym:str, class_number:int,model_size:str)->Path:
        """Generate the path where the transcription will be saved as a Path object."""
        class_number_string = f"{class_number:02d}"
        filename = f"{course_acronym}_{class_number_string}.json"
        return Path("../tmp") / course_acronym / filename