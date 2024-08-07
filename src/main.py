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
    
    def task_duplication_check(self):
        self.input_file = None

    def say_hello(self):
        print("\n  SubtitleGenerator v1.2.1-alpha  \n")
    
    def print_info(self):

        program_name = "SubtitleGenerator v1.2.1-alpha"
        author = "Zijie Duan"
        description = \
"""Welcome to {program_name}
===================================

Author: {author}

{program_name} is a powerful subtitle generator that simplifies the process of creating subtitles from your media files.

How to Use:
-----------
Simply drag and drop your media files (like MP4, MP3) onto this program to get started.

Features:
---------
1. Convert media files (MP4, MP3, etc.) to timestamp files.
2. Generate subtitle files (supports bilingual) from timestamp files.

Usage:
------
- Drag and drop your MP4 or MP3 file onto this program.
- The program will generate a timestamp file for the media.
- Drag and drop the generated timestamp file onto this program again.
- The program will then generate a subtitle file (supports bilingual) based on the timestamps.

The program automatically detects the type of file and processes it accordingly, making the whole operation seamless and efficient.

Important Notes:
----------------
- If you double-click to open this program without dragging any files, this guide will be displayed.
- In the event of a program crash, a file named "secure_save.json" will be created.
- This secure save file protects your processed information from being lost, preventing unnecessary costs from OpenAI's API.
- If a crash occurs, simply double-click to reopen the program.
- The program will automatically resume the task from where it left off.

Enjoy creating subtitles with ease!
""".format(program_name=program_name, author=author)

        print(description)
    
    def get_confumation(self, message: str):
        while True:
            choice = input("[SubtitleGenerator] : {}? [Y/N] >>".format(message))
            if choice == "Y" or choice == "y":
                return True
            elif choice == "N" or choice == "n":
                return False
            else:
                print("[SubtitleGenerator] : Please input Y or N.")

    def run(self):
        self.say_hello()

        if self.memo.exist():
            # there have a task not finish
            # do this task First
            self.memo.load()
            print("[SubtitleGenerator] : Have a task not finish.")
            print("    | Task_Type : {}".format(self.memo("TaskInfo", "Task_Type")))
            print("    | Task_Name : {}".format(self.memo("TaskInfo", "Task_Name")))
            print("    | Task_Date : {}".format(self.memo("TaskInfo", "Task_Date")))
            print("    | Task_File : {}".format(self.memo("TaskInfo", "Task_File")))
            print("    | Task_Progress : {}%\n".format(str(self.memo("TaskInfo", "Task_Progress"))))

            if FilePath(self.memo("TaskInfo", "Task_File")).exist():
                print("[SubtitleGenerator] : Task File Exist.")
            else:
                print("[SubtitleGenerator] : Task File Not Exist.")
                print("[SubtitleGenerator] : Make sure the 'Task_File' is exist.")
                print("[SubtitleGenerator] : Type Enter to Exit And Try Again.")
                input()
                return 1
            
            print("[Hint] : Why you see this message?")
            print("[Hint] : This message means the you have a task not finish in the last time.")
            print("[Hint] : You can choose to continue this task or start a new task.")
            print("[Warning] : If you start a new task, the last task will be lost.")

            if self.get_confumation("Continue the last task ?"):
                print("[SubtitleGenerator] : Continue the last task.")
            else:
                self.memo.clean()
                print("[SubtitleGenerator] : Task Removed.")
                print("[SubtitleGenerator] : Type Enter to Exit And Drop File Again.")
                input()
                return 1

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

        if self.input_file is None:
            self.print_info()
            print("[SubtitleGenerator] : Type Enter to Exit And Drop File Again.")
            input()
            return 1
        
        if self.input_file.file_ext in ["mp4", "avi", "mkv", "flv", "mov", "wmv", "mp3", "wav"]:
            # Task 1: Transfer audio to subtitle
            print("[SubtitleGenerator] : Transfer audio to Timestamp File.")
            print("[Hint] : Timestamp File will be saved in the same folder as the media file.")
            print("[Hint] : This task may take a few minutes, please wait patiently.")
            
            if self.get_confumation("Start the task"):
                print("[SubtitleGenerator] : Start the task.")
            else:
                print("[SubtitleGenerator] : Task Canceled.")
                print("[SubtitleGenerator] : Type Enter to Exit")
                input()
                return 1

            media = Media(self.input_file, SystemCmd())
            task = AudioToSubtitleTimestamp(self.cfg, self.gpt, self.wis, self.memo, media)
            task.init_task()
            task.run()
            return

        elif self.input_file.file_ext in ["json"]:
            # Task 2: Transfer timestamp to subtitle
            print("[SubtitleGenerator] : Transfer timestamp to subtitle.")
            print("[SubtitleGenerator] : please choose the language you want to translate.")
            language = None
            language_map = ["English", "Chinese", "Japanese", "Korean", "French", "German", "Spanish", "Italian", "Portuguese", "Russian"]

            while True:
                print("[SubtitleGenerator] : Support Language :")
                for i, language in enumerate(language_map):
                    print("    | {} : {}".format(i+1, language))
                print("[SubtitleGenerator] : Please input the number of the language.")
                print("[SubtitleGenerator] : Empty for Original.(Keep Original Language)")
                language = input("[SubtitleGenerator] : Number / [None] >>")
                if language == "None" or language == "":
                    language = "None"
                    break
                elif language.isdigit() and int(language) in range(1, len(language_map)+1):
                    language = language_map[int(language)-1]
                    break
                else:
                    print("[SubtitleGenerator] : Please input the number of the language.")
                    print("[SubtitleGenerator] : Or leave it empty to keep the original language.")

            if language == "None":
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
            return 1


def init_args(cfg: DockerConfig):

    continue_check = True
    while continue_check:
        cfg.read()
        
        if not cfg.is_exist("OPENAI_API_KEY"):
            print("[init_args] : Please input your OpenAI API Key.")
            api_key = input("[init_args] : OpenAI API Key >>")
            cfg.set("OPENAI", "api_key", api_key)
            print("[init_args] : Set OpenAI API Key.")
            #print("[init_args] : OpenAI Key : {}".format(cfg("OPENAI_API_KEY")))
            continue_check = True
            continue

        continue_check = False


if __name__ == "__main__":

    try:
        cfg = DockerConfig() # general config
        init_args(cfg)
        gpt = GPTApi(cfg("OPENAI_API_KEY"))
        wis = WisperApi(cfg("OPENAI_API_KEY"))
        memo = Memo(FilePath("secure_save.json", True)) # 拖动问题bug
        sg = SubtitleGenerator(cfg, gpt, wis, memo)
        status = sg.run()

        if not status:
            print("[SubtitleGenerator] : Task Finished.")
            print("[SubtitleGenerator] : Type Enter to Exit.")
            input()
        
    except Exception as e:
        print("[SubtitleGenerator] : Panic!")
        print("[SubtitleGenerator] : Serious Error Occurred.")
        print("[SubtitleGenerator] : Error Message : {}\n".format(str(e)))
        print("[SubtitleGenerator] : This Error is not expected.")
        print("[SubtitleGenerator] : Please contact the author.")
        print("[SubtitleGenerator] : Do You Want to Remove All Memory Files?")
        uin = input("[SubtitleGenerator] : [Y/N] >>")
        if uin == "Y" or uin == "y":
            print("[SubtitleGenerator] : WARNING! : This operation will remove all config files and memory files.")
            uin = input("[SubtitleGenerator] : Are You Sure? [Y/N] >>")
            if uin == "Y" or uin == "y":
                memo.clean()
                print("[SubtitleGenerator] : Memory Files Removed.")
                cfg.clear()
                print("[SubtitleGenerator] : Config Files Removed.")
            else:
                print("[SubtitleGenerator] : Operation Canceled.")
        print("[SubtitleGenerator] : Type Enter to Exit.")
        input()
