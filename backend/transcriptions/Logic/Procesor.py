import os
from pathlib import Path
from Constants.Constants import TMP_DOWNLOAD_FOLDER, VIDEO_EXTENSION
from Logic.Transcriber import Transcriber

class Procesor:
    def __init__(self) -> None:
        pass

    def update_transcription(self,course_acronym,class_number, model_size,language="es"):
        self.file_path=self.__get_video_path(course_acronym,class_number,model_size)
        self.transcriber = Transcriber(
            audio_path=self.file_path,
            output_dir=self.file_path,
            model_size=model_size,
            language=language
        )
        self.transcriber.transcribe()
        if not self.file_path.exist():
            return False, "Video Not Found"
        
    def get_transcription(self,course_acronym,class_number,model_size):
        self.file_path=self.__get_video_path(course_acronym,class_number,model_size)
        #Check Database
        ##

    def __get_video_path(self, course_acronym, class_number,model_size):
        """Generate the path where the video will be saved."""
        class_number_string = f"{class_number:02d}"
        filename = f"{class_number_string}_{model_size}.{VIDEO_EXTENSION}"
        return Path(TMP_DOWNLOAD_FOLDER) / course_acronym / filename
    