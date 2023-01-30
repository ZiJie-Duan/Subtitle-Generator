import whisper


class WHISPER_DRIVER:

    def __init__(self) -> None:
        self.model = None
        self.result = None
        self.num_of_sentence = 0
        self.sentence_index = 0

    def model_load(self,model = "tiny.en"):
        self.model = whisper.load_model(model)
     
    def transcribe(self,file_path):
        self.result = self.model.transcribe(file_path,verbose=True)
    
    def get_result(self):
        return self.result

    def init_reader(self):
        self.num_of_sentence = len(self.result["segments"])
        self.sentence_index = -1
    
    def time_convert(self,time):
        hours = time // 3600
        remain = time % 3600
        min = remain // 60
        remain = remain % 60
        sec = remain // 1
        msec = remain % 1
        msec = (msec // 0.001)
        return (int(hours),int(min),int(sec),int(msec))

    def get_sentence(self):
        self.sentence_index += 1
        if self.sentence_index < self.num_of_sentence:
            return (self.time_convert(self.result["segments"][self.sentence_index]["start"]),\
                    self.time_convert(self.result["segments"][self.sentence_index]["end"]),\
                    self.result["segments"][self.sentence_index]["text"])
        else:
            return (None,None,None)
        

# wd = whisper_driver()

# wd.model_load()
# wd.transcribe(r"C:\Users\lucyc\Desktop\au.wav")

# wd.init_reader()
# senc = None
# while True:
#     senc = wd.get_sentence()
#     if senc != (None,None,None):
#         print("[{}:{}:{},{} ----> {}:{}:{},{}] {}".format(
#             senc[0][0],senc[0][1],senc[0][2],senc[0][3],\
#             senc[1][0],senc[1][1],senc[1][2],senc[1][3],\
#             senc[2]))
#     else:
#         break
        

