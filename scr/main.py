from basic_tools import *
from config import DockerConfig
from media import Media
from openai_api import GPTApi, WisperApi
from subtitle import SubtitleWriter, SubtitleDecoder
from memo import Memo
import os
import json
import time 

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
        self.memo.update("TaskInfo", "Task_Progress", {"percentage": 0})
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
            audio_pice = self.media.get_audio_pice(20)
            if not audio_pice:
                break
            
            with open(audio_pice, "rb") as audio_file:
                data = self.wis.transcribe_timestamp(audio_file)
            
            data_list = self.memo.obj_update("TaskData", "subtitle_timestamp")
            data_list += [
                { "text": data.text, "word": data.words}
            ]
                
            self.update_progress()
        
        self.save()
        self.memo.clean()

    def save(self):
        file_path = self.media.infile.nfile(ext="json")
        with open(file_path(), "w") as f:
            json.dump(self.memo("TaskData", "subtitle_timestamp"), f)



class SubtitleGenerator:

    def __init__(self, cfg: DockerConfig, gpt: GPTApi, wis: WisperApi, memo: Memo):
        # 启动传入的参数
        self.start_args = os.sys.argv[1:]
        if len(self.start_args) < 1:
            self.input_file = None
        else:
            self.input_file = FilePath(self.start_args[0]) # we only need the first arg

        self.cfg = cfg
        self.gpt = gpt
        self.wis = wis
        self.memo = memo

    def run(self):
        if self.memo.exist():
            # there have a task not finish
            # do this task First
            self.memo.load()
            print("[SubtitleGenerator] : Have a task not finish.")
            print("    | Task_Type : {}".format(self.memo("TaskInfo", "Task_Type")))
            print("    | Task_Name : {}".format(self.memo("TaskInfo", "Task_Name")))
            print("    | Task_Date : {}".format(self.memo("TaskInfo", "Task_Date")))
            print("    | Task_File : {}".format(self.memo("TaskInfo", "Task_File")))
            print("    | Task_Progress : {}%".format(str(self.memo("TaskInfo", "Task_Progress"))))

            if FilePath(self.memo("TaskInfo", "Task_File")).exist():
                print("[SubtitleGenerator] : Status Check Passed.")
            else:
                print("[SubtitleGenerator] : Status Check Failed.")
                print("[SubtitleGenerator] : Make sure the 'Task_File' is exist.")
                print("[SubtitleGenerator] : Type Enter to Exit And Try Again.")
                input()
                return
            
            if self.memo("TaskInfo", "Task_Type") == "toSubtitleTimestampFile":
                media = Media(FilePath(self.memo("TaskInfo", "Task_File")), SystemCmd())
                task = AudioToSubtitleTimestamp(self.cfg, self.gpt, self.wis, self.memo, media)
                task.continue_task()
                task.run()
                return
        else:
            # 初始化任务 Info
            self.memo.add_section("TaskInfo")
            self.memo.add_section("TaskData")

        if self.input_file.file_ext in ["mp4", "avi", "mkv", "flv", "mov", "wmv", "mp3", "wav"]:
            # Task 1: Transfer audio to subtitle
            media = Media(self.input_file, SystemCmd())
            task = AudioToSubtitleTimestamp(self.cfg, self.gpt, self.wis, self.memo, media)
            task.init_task()
            task.run()
            return

        elif self.input_file.file_ext in ["json"]:
            pass
        else:
            print("[SubtitleGenerator] : Not support file type.")
            print("[SubtitleGenerator] : Support file type : mp4, avi, mkv, flv, mov, wmv, mp3, wav, json")
            print("[SubtitleGenerator] : Your file type : {}".format(self.input_file.file_ext))
            print("[SubtitleGenerator] : Type Enter to Exit And Try Again.")
            input()
            return


cfg = DockerConfig() # general config
gpt = GPTApi(cfg("OPENAI_API_KEY_PETER"))
wis = WisperApi(cfg("OPENAI_API_KEY_PETER"))
memo = Memo(FilePath("secure_save.json", True)) # 拖动问题bug
sg = SubtitleGenerator(cfg, gpt, wis, memo)
sg.run()

#----------------------------- Comst Function ---------------------------------


# def transfer_subtitle(path: str, lenth: str):
#     fvideo = FilePath(path)
#     video = Media(fvideo, SystemCmd())
#     data = []
#     wd = whisper_driver()
#     wd.model_load()
#     video.init_process()
#     while True:
#         print("[transfer_subtitle] : lenth")
#         temp_file = video.get_audio_pice(int(lenth))
#         if not temp_file:
#             break

#         wd.transcribe(temp_file)
#         wd.init_reader()
        
#         while True:
#             res = wd.get_sentence()
#             if res == (None, None, None):
#                 break

#             print("[{}:{}:{},{} ----> {}:{}:{},{}] {}".format(
#                 res[0][0], res[0][1], res[0][2], res[0][3], \
#                 res[1][0], res[1][1], res[1][2], res[1][3], res[2]))
            
#             data.append(res)
    
#     memory.write("subt_data", data)
#     subt_data_f = fvideo.nfile(full_name="subt_data.json")
#     with open(subt_data_f(), "w") as f:
#         json.dump(data, f)


# def transfer_subtitle_ch(path: str, background: str):
#     fsubt_data = FilePath(path)
#     fsubt_data_ch = fsubt_data.nfile(full_name="subt_data_ch.json")

#     subt_data_ch = []
#     subt_data = []
#     with open(fsubt_data(), "r") as f:
#         subt_data = json.load(f)

#     for i in range(len(subt_data)):
#         subtitle = subt_data[i][2]
#         prompt = "Please translate the English subtitles into Chinese. this subtitle is from "\
#             + background + ".\nSubtitle : " + subtitle + "."
        
#         for count in range(5):
#             try:
#                 subtitle_ch = gpt.query([{"role": "user", "content": prompt}], max_tokens=1000, temperature=0.0, timeout=30)
#                 break
#             except Exception as e:
#                 print(e)
#                 print("[transfer_subtitle_ch] : GPT API error, retrying...")
#                 continue
#         if count == 4:
#             input("[transfer_subtitle_ch] : GPT API error, please check your API key and network. Press any key to continue...")
#             exit(0)

#         print("[transfer_subtitle_ch] : {} ----> {}".format(subtitle, subtitle_ch))
#         subt_data_ch.append([subt_data[i][0], subt_data[i][1], subtitle_ch])
    
#     with open(fsubt_data_ch(), "w") as f:
#         json.dump(subt_data_ch, f)


# def data_to_subtitle(path: str):
#     fsubt_data_ch = FilePath(path)
#     fsub_ch_str = fsubt_data_ch.nfile(full_name="subt_ch.srt")

#     subt_data_ch = []
#     with open(fsubt_data_ch(), "r") as f:
#         subt_data_ch = json.load(f)
    
#     subt_writer = SubtitleWriter(files=fsub_ch_str)
#     subt_writer.open()
    
#     for subt in subt_data_ch:
#         # 这里我们进行了一点转换，subt[2]原本是一个字符串，但是我们需要将其转为列表
#         subt_writer.write_subtitle(subt[0], subt[1], [subt[2]])


# def get_text(file_path: str, text_lenth: int):
#     # 从文件中获取文本, 字符串长度为text_lenth
#     text = None
#     with open(file_path, "r", encoding="utf-8") as file:
#         text = file.read()
    
#     for i in range(0, len(text), text_lenth):
#         yield text[i : i + text_lenth]
#     yield text[i + text_lenth :]


# def purefy_subtitle(in_path: str, out_path: str, lenth: str):
#     text_in = FilePath(in_path)
#     text_out = text_in.nfile(full_name=out_path)
#     text_gen = get_text(text_in(), int(lenth))

#     prompt = "翻译‘<<>>’中的文本 到中文\n <<"

#     with open(text_out(), "w", encoding="utf-8") as file:
#         while True:
#             text = next(text_gen)
#             if not text:
#                 break
        
#             for count in range(5):
#                 try:
#                     summary = gpt.query([{"role": "user", "content": prompt + text + ">>"}], max_tokens=3500, temperature=0.0, timeout=30)
#                     break
#                 except Exception as e:
#                     print(e)
#                     print("[purefy_subtitle] : GPT API error, retrying...")
#                     continue
            
#             if count == 4:
#                 input("[purefy_subtitle] : GPT API error, please check your API key and network. Press any key to continue...")
#                 exit(0)
            
#             print("[purefy_subtitle] : {} ----> {}".format(text, summary))
#             file.write(summary + "\n")
#             file.flush()
    
#     print("[purefy_subtitle] : Done.")

# def purefy_all_dir(in_path: str, lenth: str):
#     for file in os.listdir(in_path):
#         if file.endswith(".txt"):
#             purefy_subtitle(in_path + "/" + file, 'purefy_'+file, lenth)


# #----------------------------- Command ---------------------------------

# def shelp():
#     print("[help] : command list:")
#     for cmd_name, func in command_list:
#         print(" --{:<10}-> {}".format(cmd_name, func.__name__))


# # ----------------------------- Command register ---------------------------------
# command_list = [
#     ("h", shelp),
#     ("mls", memory.ls_memory),
#     ("mdel", memory.del_memo),
#     ("mrename", memory.rename),
#     ("trans", transfer_subtitle),
#     ("ch", transfer_subtitle_ch),
#     ("dts", data_to_subtitle),
#     ("p", purefy_subtitle),
#     ("pall", purefy_all_dir),
#     ("q", exit)
# ] 
# # list of command and functions


# def command(cmd, *args):

#     for cmd_name, func in command_list:
#         if cmd_name == cmd:
#             func(*args)
#             return


# def main():

#     say_hello()
    
#     while True:
#         cmd = input(">>> ")
#         cmd = cmd.split("@")

#         if cmd[0] == "q":
#             break

#         command(cmd[0], *cmd[1:])
        
#         # try:
#         #     command(cmd[0], *cmd[1:])
#         # except Exception as e:
#         #     print("[main] : {}".format(e))
#         #     continue


# if "__main__" == __name__:
#     main()