from datetime import datetime
from DTO import TranscriberConfig
from langchain.text_splitter import RecursiveCharacterTextSplitter
from Logic.WhisperTranscriber import WhisperTranscriber
from pathlib import Path
import Logic.WhisperTranscriber as WhisperTranscriber
# import torch
# import whisper 

initial_config= TranscriberConfig.TranscriberConfig(
        model_size=TranscriberConfig.WhisperModel.BASE,
        language="es",
        task="transcribe",
        output_dir="transcriptions",
        # device="cuda" if torch.cuda.is_available() else "cpu"
        device="cpu"
    )

class Transcriber:
    def __init__(self,audio_path:Path,output_dir:Path,model_size,language): 
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        # self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = "cpu"
        self.task= "transcribe"
        self.audio_path = audio_path
        self.output_dir = output_dir
        self.language = language
        self.model_size = model_size#TranscriberConfig.WhisperModel.BASE
        #self.config = initial_config
        pass

    def transcribe(self, audio_path: str) -> dict:
        """Transcribe audio and return text with metadata"""
        result = self.model.transcribe(audio_path)

        return {
            "text": result["text"],
            "segments": result["segments"],
            "metadata": {
                "source": Path(audio_path).name,
                ##no se si el momento en que se subio es importante
                "date_processed": datetime.now().isoformat(),
                "model": "whisper-base",
            },
        }

    def chunk_text(self, transcription: dict) -> list[dict]:
        """Split transcription into chunks with metadata"""
        texts = self.text_splitter.split_text(transcription["text"])

        chunks = []
        for i, text in enumerate(texts):
            chunks.append(
                {
                    "text": text,
                    "metadata": {
                        **transcription["metadata"],
                        "chunk_id": i,
                    },
                }
            )
        return chunks

    def transcribe_video(self, video_path,model_size="base", language="es"):
        """Transcribe a video file to text"""
        self.__config.output_dir=video_path
        self.__config.language=language
        self.__config.model_size=model_size
        self.__whisper_transcriber.set_config(self.__config)
        return self.__whisper_transcriber.transcribe()
    
