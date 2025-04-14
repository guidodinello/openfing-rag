from DTO.TranscriberConfig import TranscriberConfig
import Logic.WhisperTranscriber as WhisperTranscriber

class WhisperTranscriber():
    def __init__(self, config: TranscriberConfig):
        pass

    def set_config(self, config: TranscriberConfig):
        self.__config = config
        self.__model = WhisperTranscriber.load_model(config.model_size.value, device=self.device)
        self.__model.eval()

    @property
    def get_device(self) -> str:
        return self.__config.device


    def transcribe(self) -> dict:
        return self.__model.transcribe(
            audio_path=self.__config.output_dir,
            language=self.__config.language,
            task=self.__config.task,
            fp16=self.__config.device == "cuda"
        )