from config import DockerConfig
from openai_api import GPTApi, WisperApi
from memo import Memo
from subtitle import SubtitleWriter
import json
import time
import math
import asyncio

'''
通用任务数据定义（每一个任务都会基于一个文件进行操作）：
在Section "TaskInfo" 中定义
TaskInfo = {
    "Task_Type": type,
    "Task_Name": name,
    "Task_Date": date,
    "Task_File": file_path,
    "Task_Progress" : float
}
在Section "TaskData" 中定义 其他的客制化数据
'''

class AudioToSubtitleTimestamp:
    """
    Task Transfer audio to subtitle with timestamp

    TaskInfo:{
        Task_Type = "toSubtitleTimestampFile"
        Task_Name = "AudioToSubtitleTimestamp_{file_name}"
        Task_Progress =  23 FLOAT
    }

    TaskData:{
        "media_split_point" = 1254.23 FLOAT,
        "subtitle_timestamp": [
            {
                "text": "paragraph 1",
                "word": <OpenAI Word Defined>
            },
            {
                "text": "paragraph 2",
                "word": <OpenAI Word Defined>
            }
        ]
    }
    """

    def __init__(self, cfg: DockerConfig, gpt: GPTApi, 
                 wis: WisperApi, memo: Memo, media: object):
        self.cfg = cfg
        self.gpt = gpt
        self.wis = wis
        self.memo = memo
        self.media = media

    def init_task(self):
        self.media.init_process()
        self.memo.update("TaskInfo", "Task_Type", "toSubtitleTimestampFile")
        self.memo.update("TaskInfo", "Task_Name", "AudioToSubtitleTimestamp_{}".format(self.media.infile()))
        self.memo.update("TaskInfo", "Task_Date", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        self.memo.update("TaskInfo", "Task_File", self.media.infile())
        self.memo.update("TaskInfo", "Task_Progress", 0)
        self.memo.update("TaskData", "media_split_point", 0)
        self.memo.update("TaskData", "subtitle_timestamp", [])
        print("[AudioToSubtitleTimestamp] : Task Init.")

    def continue_task(self):
        self.media.split_start = self.memo("TaskData", "media_split_point")
        print("[AudioToSubtitleTimestamp] : Continue Task")
    
    def update_progress(self):
        self.memo.update("TaskInfo", "Task_Progress", self.media.split_start/self.media.duration * 100)
        self.memo.update("TaskData", "media_split_point", self.media.split_start)
        print("[AudioToSubtitleTimestamp] : Progress : {}%".format(str(self.memo("TaskInfo", "Task_Progress"))))

    def run(self):

        while True:
            audio_pice = self.media.get_audio_pice(100)
            if not audio_pice:
                break
            
            with open(audio_pice, "rb") as audio_file:
                data = self.wis.transcribe_timestamp(audio_file)
            
            data_list = self.memo.obj_update("TaskData", "subtitle_timestamp")

            words = []
            for word in data.words:
                words.append({
                    "word": word["word"],
                    "start": word["start"] + self.memo("TaskData", "media_split_point"),
                    "end": word["end"] + self.memo("TaskData", "media_split_point")
                })

            data_list += [
                { "text": data.text, "word": words}
            ]
                
            self.update_progress()
        
        self.save()
        self.memo.clean()

    def save(self):
        file_path = self.media.infile.nfile(ext="json")
        with open(file_path(), "w") as f:
            json.dump(self.memo("TaskData", "subtitle_timestamp"), f)



def gpt_split_sentence(gpt: GPTApi, text: str):
    prompt = """
You are a subtitle segmenter. Your task is to segment the text enclosed in <<<>>> symbols into short sections based on semantics and pauses, with each section not exceeding 12 words and containing no punctuation. Each segmented subtitle should be presented in the following format:
---
subtitle text 1
---
subtitle text 2
---
Maintain the natural flow of the dialogue and ensure each segment can independently convey a complete meaning. Do not provide any explanations with your outputs. Do not modify any text.
    """
    usermsg = "<<<{}>>>".format(text)
    message = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": usermsg}
    ]
    response = gpt.query(message, max_tokens=4000, temperature=0.1, model="gpt-4o")
    sentences = response[4:-4].split("\n---\n")
    return sentences


def euclidean_distance(vector1, vector2):
    if len(vector1) != len(vector2):
        raise ValueError("The length of two vectors must be the same.")
    
    distance = math.sqrt(sum((x - y) ** 2 for x, y in zip(vector1, vector2)))
    return distance


async def get_embedding_async(gpt, sentence):
    loop = asyncio.get_running_loop()  # 获取当前运行的事件循环
    response = await loop.run_in_executor(None, gpt.get_embedding, sentence)
    return response

async def get_embedding_list_async(gpt, sentences):
    tasks = [get_embedding_async(gpt, sentence) for sentence in sentences]
    embeddings = await asyncio.gather(*tasks)
    return embeddings


class SubStampToSubtitleOriginal:
    """
    Task Transfer subtitle timestamp to subtitle

    TaskInfo:{
        Task_Type = "toSubtitleOriginal"
        Task_Name = "SubStampToSubtitleOriginal_{file_name}"
        Task_Progress =  23 FLOAT
    }

    TaskData:{
        "paragraph_index" = 0 INT,  # 当前段落索引 来自字幕时间戳文件
        "paragraph": "xxx" STR,     # 当前段落文本 来自字幕时间戳文件
        # 以上两个变量是在 以 段落为单位颗粒度的保存

        "sentence": [] LIST,        # 由GPT进行分段的句子 
        "word_timestamp": [] LIST,  # 当前段落的单词时间戳 来自字幕时间戳文件
        "subtitle_match": [] LIST,   # 完成时间定位的字幕与其时间戳
        # 以上三个变量是在 以句子为单位颗粒度的保存
        # sentences 和 word_timestamp 是一一对应的, 匹配之后将会被逐步弹出移除
        # subtitle_match 是匹配之后的结果, 会被逐步添加，直到 sentence 和 word_timestamp 为空

        # 当subtitle_match 完成后，将会被写入到 subtitle_srt 中
    }
    """

    def __init__(self, cfg: DockerConfig, gpt: GPTApi, wis: WisperApi, 
                 memo: Memo, subwriter: SubtitleWriter, timestamp_file: object):
        self.cfg = cfg
        self.gpt = gpt
        self.wis = wis
        self.memo = memo
        self.subwriter = subwriter
        self.timestamp_file = timestamp_file
        self.timestamp = None

        self.load_timestamp()

    def load_timestamp(self):
        with open(self.timestamp_file(), "r") as f:
            self.timestamp = json.load(f)
    
    def init_task(self):
        self.memo.update("TaskInfo", "Task_Type", "toSubtitleOriginal")
        self.memo.update("TaskInfo", "Task_File", self.timestamp_file())
        self.memo.update("TaskInfo", "Task_Name", "SubStampToSubtitleOriginal_{}".format(self.memo("TaskInfo", "Task_File")))
        self.memo.update("TaskInfo", "Task_Date", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        self.memo.update("TaskInfo", "Task_Progress", 0)
        self.memo.update("TaskData", "paragraph_index", 0)
        self.memo.update("TaskData", "paragraph", "")
        self.memo.update("TaskData", "sentences", [])
        self.memo.update("TaskData", "word_timestamp", [])
        self.memo.update("TaskData", "subtitle_match", [])
        self.memo.update("TaskData", "subtitle_srt", "")
        print("[SubStampToSubtitleOriginal] : Task Init.")

    def continue_task(self):
        print("[SubStampToSubtitleOriginal] : Continue Task")

    def update_progress(self):
        self.memo.update("TaskInfo", "Task_Progress", self.memo("TaskData", "paragraph_index")/len(self.timestamp) * 100)
        print("[SubStampToSubtitleOriginal] : Progress : {}%".format(str(self.memo("TaskInfo", "Task_Progress"))))
    
    def run(self):
        
        while True:

            paragraph_index = self.memo("TaskData", "paragraph_index")
            if paragraph_index == len(self.timestamp):
                break

            print("[SubStampToSubtitleOriginal] : Processing Paragraph : {}".format(paragraph_index))
            
            if self.memo("TaskData", "paragraph") == "":
                self.memo.update("TaskData", "paragraph", self.timestamp[paragraph_index]["text"])
            
            if self.memo("TaskData", "word_timestamp") == []:
                self.memo.update("TaskData", "word_timestamp", self.timestamp[paragraph_index]["word"])
            
            if self.memo("TaskData", "sentences") == []:
                sentences = gpt_split_sentence(self.gpt, self.memo("TaskData", "paragraph"))
                self.memo.update("TaskData", "sentences", sentences)


            while True:
                if self.memo("TaskData", "sentences") == []:
                    break
                
                sentence = self.memo("TaskData", "sentences")[0]
                length = len(sentence.split(" "))

                v1 = self.gpt.get_embedding(sentence)
                word_list = self.memo("TaskData", "word_timestamp")[:length+3]

                min_dis = 9999999
                match_index = None
                match_sentence = None

                loop = asyncio.get_event_loop()

                sentence_slice = []
                for i in range(len(word_list), max(length-3,0), -1):
                    words = [x["word"] for x in word_list[:i]]
                    sentence_origin = " ".join(words)
                    sentence_slice.append(sentence_origin)
                sentence_slice.reverse()
                
                index_shift = max(length-3,0)
                embeddings = loop.run_until_complete(
                    get_embedding_list_async(self.gpt, sentence_slice))

                for i in range(len(embeddings)):
                    ii = i + index_shift
                    dis = euclidean_distance(v1, embeddings[i])

                    if dis < min_dis:
                        min_dis = dis
                        match_index = ii
                        match_sentence = i
                
                start_time = word_list[0]["start"]
                end_time = word_list[match_index]["end"]

                print("[SubStampToSubtitleOriginal] : Processing Sentence : {}".format(sentence))
                print("[SubStampToSubtitleOriginal] : Matched Words       : {}".format(sentence_slice[match_sentence]))
                
                # 将以下三个操作 合并为一个操作 原子性操作
                self.memo.obj_update("TaskData", "subtitle_match").append({
                    "text": sentence,
                    "start": start_time,
                    "end": end_time
                })
                self.memo.update("TaskData", "word_timestamp", 
                                 self.memo("TaskData", "word_timestamp")[match_index+1:])
                self.memo.obj_update("TaskData", "sentences").pop(0)
                self.memo.save()
            
            self.memo.update("TaskData", "paragraph_index", paragraph_index+1, not_save=True)
            self.memo.update("TaskData", "paragraph", "", not_save=True)
            self.memo.update("TaskData", "sentences", [], not_save=True)
            self.memo.update("TaskData", "word_timestamp", [], not_save=True)
            self.update_progress()

        self.save()
        #self.memo.clean()

    def save(self):
        self.subwriter.open()
        index = 1
        for i in self.memo("TaskData", "subtitle_match"):
            self.subwriter.write_subtitle_timestamp(index, i["start"], i["end"], [i["text"]])
            index += 1
        self.subwriter.close()



def gpt_split_sentence_translation(gpt: GPTApi, text: str, language: str):

    prompt_translation = """
You are a subtitle translator. Your task is to translate the text enclosed by <<<>>> into {}, using fluent, natural, and idiomatic {}. You may freely add, remove, or modify the translation to achieve a more ideal expression. If any annotations are needed, use parentheses for notes.
Present in the following format:
---
translated paragraph
---
""".format(language, language)

    prompt_split = """
You are a subtitle segmenter. Your task is to segment the text enclosed in <<<>>> symbols into short sections based on semantics and pauses, with each section not exceeding 12 words and containing no punctuation. Each segmented subtitle should be presented in the following format:
---
subtitle text 1
---
subtitle text 2
---
Maintain the natural flow of the dialogue and ensure each segment can independently convey a complete meaning. Do not provide any explanations with your outputs. Do not modify any text.
    """

    prompt_match = """
You are a bilingual subtitle matcher. Your task is to match the text enclosed in <<<>>> with the text enclosed in ((( ))). Ensure that the content of the two corresponds to each other.
The text enclosed in <<<>>> is already segmented with the "|" symbol. Please match each segment in ((( ))) with one segment in <<<>>>.
Make sure not to modify any text and do not miss any characters. The segments in ((( ))) do not need to be coherent or fluent.
Each segment should be presented in the following format:
---
Segment text 1 from <<<>>>
-
Segment text 1 from ((()))
---
Segment text 2 from <<<>>>

-
Segment text 2 from ((()))
---
Please do not provide any explanations and do not answer any questions.
"""

    usermsg = "<<<{}>>>".format(text)
    message = [
        {"role": "system", "content": prompt_translation},
        {"role": "user", "content": usermsg}
    ]
    response = gpt.query(message, max_tokens=4000, temperature=0.5, model="gpt-4o")
    sentences = response[4:-4]

    usermsg = "<<<{}>>>".format(sentences)
    message = [
        {"role": "system", "content": prompt_split},
        {"role": "user", "content": usermsg}
    ]
    response = gpt.query(message, max_tokens=4000, temperature=0.1, model="gpt-4o")
    sentences = response[4:-4].split("\n---\n")

    usermsg = "<<<{}>>> \n((({})))".format("|".join(sentences), text)
    message = [
        {"role": "system", "content": prompt_match},
        {"role": "user", "content": usermsg}
    ]
    response = gpt.query(message, max_tokens=4000, temperature=0.1, model="gpt-4o")
    sentences = response[4:-4].split("\n---\n")
    sentences = [x.split("\n-\n") for x in sentences]
    translation = [x[0] for x in sentences]
    match_only = [x[1] for x in sentences]

    print("DEBUG 原文: ", text)
    print("DEBUG 翻译: ", translation)
    print("DEBUG 匹配: ", match_only)
    input("DEBUG")

    return translation, match_only



class SubStampToSubtitleTranslation:
    """
    Task Transfer subtitle timestamp to subtitle

    TaskInfo:{
        Task_Type = "toSubtitleTranslation"
        Task_Name = "SubStampToSubtitleTranslation_{file_name}"
        Task_Progress =  23 FLOAT
        Task_Language = "English"
    }

    TaskData:{
        "paragraph_index" = 0 INT,  # 当前段落索引 来自字幕时间戳文件
        "paragraph": "xxx" STR,     # 当前段落文本 来自字幕时间戳文件
        # 以上两个变量是在 以 段落为单位颗粒度的保存

        "sentence": [] LIST,        # 由GPT进行分段的句子（翻译版本）
        "word_timestamp": [] LIST,  # 当前段落的单词时间戳 来自字幕时间戳文件
        "subtitle_match": [] LIST,   # 完成时间定位的字幕与其时间戳
        # 以上三个变量是在 以句子为单位颗粒度的保存
        # sentences 和 word_timestamp 是一一对应的, 匹配之后将会被逐步弹出移除
        # subtitle_match 是匹配之后的结果, 会被逐步添加，直到 sentence 和 word_timestamp 为空

        # 当subtitle_match 完成后，将会被写入到 subtitle_srt 中
    }
    """

    def __init__(self, cfg: DockerConfig, gpt: GPTApi, wis: WisperApi, memo: Memo, 
                 subwriter: SubtitleWriter, timestamp_file: object, language: str):
        self.cfg = cfg
        self.gpt = gpt
        self.wis = wis
        self.memo = memo
        self.subwriter = subwriter
        self.timestamp_file = timestamp_file
        self.timestamp = None
        self.language = language

        self.load_timestamp()

    def load_timestamp(self):
        with open(self.timestamp_file(), "r") as f:
            self.timestamp = json.load(f)
    
    def init_task(self):
        self.memo.update("TaskInfo", "Task_Type", "toSubtitleTranslation")
        self.memo.update("TaskInfo", "Task_File", self.timestamp_file())
        self.memo.update("TaskInfo", "Task_Name", "SubStampToSubtitleTranslation_{}".format(self.memo("TaskInfo", "Task_File")))
        self.memo.update("TaskInfo", "Task_Date", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        self.memo.update("TaskInfo", "Task_Progress", 0)
        self.memo.update("TaskInfo", "Task_Language", self.language)
        self.memo.update("TaskData", "paragraph_index", 0)
        self.memo.update("TaskData", "paragraph", "")
        self.memo.update("TaskData", "sentences", [])
        self.memo.update("TaskData", "match_anchor", [])
        self.memo.update("TaskData", "word_timestamp", [])
        self.memo.update("TaskData", "subtitle_match", [])
        self.memo.update("TaskData", "subtitle_srt", "")
        print("[SubStampToSubtitleTranslation] : Task Init.")

    def continue_task(self):
        print("[SubStampToSubtitleTranslation] : Continue Task")

    def update_progress(self):
        self.memo.update("TaskInfo", "Task_Progress", self.memo("TaskData", "paragraph_index")/len(self.timestamp) * 100)
        print("[SubStampToSubtitleTranslation] : Progress : {}%".format(str(self.memo("TaskInfo", "Task_Progress"))))
    
    def run(self):
        
        while True:

            paragraph_index = self.memo("TaskData", "paragraph_index")
            if paragraph_index == len(self.timestamp):
                break

            print("[SubStampToSubtitleTranslation] : Processing Paragraph : {}".format(paragraph_index))
            
            if self.memo("TaskData", "paragraph") == "":
                self.memo.update("TaskData", "paragraph", self.timestamp[paragraph_index]["text"])
            
            if self.memo("TaskData", "word_timestamp") == []:
                self.memo.update("TaskData", "word_timestamp", self.timestamp[paragraph_index]["word"])
            
            if self.memo("TaskData", "sentences") == []:
                sentence, match_anchor = gpt_split_sentence_translation(self.gpt, self.memo("TaskData", "paragraph"), self.language)
                self.memo.update("TaskData", "sentences", sentence)
                self.memo.update("TaskData", "match_anchor", match_anchor)


            while True:
                if self.memo("TaskData", "sentences") == []:
                    break
                
                sentence = self.memo("TaskData", "sentences")[0]
                match_anchor = self.memo("TaskData", "match_anchor")[0]
                length = len(match_anchor.split(" "))

                v1 = self.gpt.get_embedding(match_anchor)
                word_list = self.memo("TaskData", "word_timestamp")[:length+3]

                min_dis = 9999999
                match_index = None
                match_sentence = None

                loop = asyncio.get_event_loop()

                if not word_list:
                    input("DEBUG")
                    raise ValueError("word_list is empty")

                sentence_slice = []
                for i in range(len(word_list), max(length-3,0) , -1):
                    words = [x["word"] for x in word_list[:i]]
                    sentence_origin = " ".join(words)
                    if sentence_origin == "": continue
                    sentence_slice.append(sentence_origin)
                sentence_slice.reverse()
                
                index_shift =  max(length-3,0)
                embeddings = loop.run_until_complete(
                    get_embedding_list_async(self.gpt, sentence_slice))

                for i in range(len(embeddings)):
                    ii = i + index_shift
                    dis = euclidean_distance(v1, embeddings[i])

                    if dis < min_dis:
                        min_dis = dis
                        match_index = ii
                        match_sentence = i
                
                start_time = word_list[0]["start"]
                end_time = word_list[match_index]["end"]

                print("[SubStampToSubtitleTranslation] : Processing Sentence : {}".format(sentence))
                print("[SubStampToSubtitleTranslation] : Rebuild Words       : {}".format(match_anchor))
                print("[SubStampToSubtitleTranslation] : Matched Words       : {}".format(sentence_slice[match_sentence]))
                
                # 将以下三个操作 合并为一个操作 原子性操作
                self.memo.obj_update("TaskData", "subtitle_match").append({
                    "text": sentence,
                    "start": start_time,
                    "end": end_time
                })
                self.memo.update("TaskData", "word_timestamp", 
                                 self.memo("TaskData", "word_timestamp")[match_index+1:])
                self.memo.obj_update("TaskData", "sentences").pop(0)
                self.memo.obj_update("TaskData", "match_anchor").pop(0)
                self.memo.save()
            
            self.memo.update("TaskData", "paragraph_index", paragraph_index+1, not_save=True)
            self.memo.update("TaskData", "paragraph", "", not_save=True)
            self.memo.update("TaskData", "sentences", [], not_save=True)
            self.memo.update("TaskData", "match_anchor", [], not_save=True)
            self.memo.update("TaskData", "word_timestamp", [], not_save=True)
            self.update_progress()

        self.save()
        #self.memo.clean()

    def save(self):
        self.subwriter.open()
        index = 1
        for i in self.memo("TaskData", "subtitle_match"):
            self.subwriter.write_subtitle_timestamp(index, i["start"], i["end"], [i["text"]])
            index += 1
        self.subwriter.close()


