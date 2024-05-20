from basic_tools import *
from config import DockerConfig
from media import Media
from openai_api import GPTApi, WisperApi
from memo import Memo
from core import AudioToSubtitleTimestamp, SubStampToSubtitleOriginal, SubStampToSubtitleTranslation
from subtitle import SubtitleWriter
import os


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
            
            elif self.memo("TaskInfo", "Task_Type") == "toSubtitleOriginal":
                timestamp_file = FilePath(self.memo("TaskInfo", "Task_File"))
                subwriter = SubtitleWriter(FilePath(self.memo("TaskInfo", "Task_File")).nfile(ext="srt"))
                task = SubStampToSubtitleOriginal(self.cfg, self.gpt, self.wis, self.memo, subwriter, timestamp_file)
                task.continue_task()
                task.run()
                return

            elif self.memo("TaskInfo", "Task_Type") == "toSubtitleTranslation":
                timestamp_file = FilePath(self.memo("TaskInfo", "Task_File"))
                subwriter = SubtitleWriter(FilePath(self.memo("TaskInfo", "Task_File")).nfile(ext="srt"))
                language = self.memo("TaskInfo", "Task_Language")
                task = SubStampToSubtitleTranslation(self.cfg, self.gpt, self.wis, self.memo, subwriter, timestamp_file, language)
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
            # Task 2: Transfer timestamp to subtitle
            print("[SubtitleGenerator] : Transfer timestamp to subtitle.")
            print("[SubtitleGenerator] : please choose the language you want to translate.")
            language = input("[SubtitleGenerator] : Language / [None] for Original >>")

            if language == "None" or language == "":
                timestamp_file = self.input_file
                subwriter = SubtitleWriter(self.input_file.nfile(ext="srt"))
                task = SubStampToSubtitleOriginal(self.cfg, self.gpt, self.wis, self.memo, subwriter, timestamp_file)
                task.init_task()
                task.run()
                return
            else:
                timestamp_file = self.input_file
                subwriter = SubtitleWriter(self.input_file.nfile(ext="srt"))
                task = SubStampToSubtitleTranslation(self.cfg, self.gpt, self.wis, self.memo, subwriter, timestamp_file, language)
                task.init_task()
                task.run()
                return
        
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

input() # wait for user to close the window