import whisper


class whisper_driver:

    def __init__(self) -> None:
        self.model = None
        self.result = None

    def model_load(self,model = "tiny.en"):
        self.model = whisper.load_model(model)
    
    def transcribe(self,file_path):
        self.result = self.model.transcribe(file_path,verbose=True)
    
    def result_print(self):
        print(self.result)
