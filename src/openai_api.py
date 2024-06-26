from openai import OpenAI

class GPTApi:
    """
    GPT API Class
    """
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-3.5-turbo"  # 设置默认模型

    def set_model(self, model: str):
        """设置模型"""
        self.model = model

    def query(self, 
            messages, 
            temperature = 0.5, 
            max_tokens = 100,
            model = None,
            full = False,
            timeout = 30) -> str:
        
        if not model:
            model = self.model

        response = self.client.chat.completions.create(
                model = model,
                messages = messages,
                temperature = temperature,
                max_tokens = max_tokens,
                timeout = timeout
            )
        if full:
            return response
        else:
            return response.choices[0].message.content


    def query_stream(self, 
            messages, 
            temperature = 0.5, 
            max_tokens = 100,
            model = None,
            full = False,
            timeout = 30):

        if not model:
            model = self.model
        
        response = self.client.chat.completions.create(
            model = model,
            messages = messages,
            temperature = temperature,
            max_tokens = max_tokens,
            stream=True,
            timeout = timeout
        )

        if full:
            for chunk in response:
                yield chunk
        
        else:
            for chunk in response:
                word = chunk["choices"][0].get("delta", {}).get("content")
                if word:
                    yield word 


    def get_embedding(self, text, model="text-embedding-3-large"):
        text = text.replace("\n", " ")
        return self.client.embeddings.create(input = [text], model=model).data[0].embedding
    

class WisperApi:

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def transcribe(self, audio_file, model = "whisper-1", response_format = "srt"):
        transcript = self.client.audio.transcriptions.create(
            file = audio_file,
            model = model,
            response_format = response_format
        )
        return transcript


    def transcribe_timestamp(self, audio_file, model = "whisper-1", 
                             response_format = "verbose_json", 
                             timestamp_granularities = ["word"]):
        transcript = self.client.audio.transcriptions.create(
            file = audio_file,
            model = model,
            response_format = response_format,
            timestamp_granularities = timestamp_granularities
        )
        return transcript





# ---------- TEST CODE ------------

# from config import DockerConfig
# cfg = DockerConfig()
# audio_file = open(r"C:\Users\lucyc\Desktop\aaaa.mp3", "rb")
# api = WisperApi(api_key=cfg("OPENAI_API_KEY_PETER"))
# transcript = api.transcribe(audio_file)
# print(transcript)