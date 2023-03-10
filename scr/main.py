
# -*- coding: utf-8 -*-
# you can add your python.exe path in the first line
from media import*
from subtitle import*
from translator import*
from whisper_sub import*
from basic_tools import*
import sys


class SUBTITLE_GENERATOR:

    def __init__(self):
        self.media = None
        self.subtitle = None
        self.translator = None
        self.whisper = None
    
    def init_generator(self,path):
        file = FILE_PATH()
        file.set_path(path)
        self.media = MEDIA(file, SYSTEM_CMD())
        self.translator = TRANSLATOR()

        self.whisper = WHISPER_DRIVER()
        self.whisper.model_load()

        subtitle_file = FILE_PATH()
        subtitle_path = self.media.infile.build_new_file(ext="srt")
        subtitle_file.set_path(subtitle_path)
        self.subtitle = SUBTITLE_WRITER(files=subtitle_file)
    
    def generate_subtitle(self, duration=999999999):

        audio_file = self.media.get_a_part_of_audio(duration)
        self.whisper.transcribe(audio_file)
        self.whisper.init_reader()

        while True:
            text_tuple = self.whisper.get_sentence()
            if text_tuple != (None,None,None):
                new = self.translator.translate_sentence(text_tuple[2])
                #new = "TEST MODE"
                self.subtitle.open()
                self.subtitle.write_subtitle(text_tuple[0],text_tuple[1],text_tuple[2],new)
                self.subtitle.close()
            else:
                break


def main():
    print("subtitle generator beta_0.1")
    sub = SUBTITLE_GENERATOR()

    if len(sys.argv) != 2:
        path = input("please input the path of the video file >>")
        sub.init_generator(path)
    else:
        sub.init_generator(sys.argv[1])

    sub.translator.apiurl = 'http://api.fanyi.baidu.com/api/trans/vip/translate'
    sub.translator.appid = "" #check baidu account
    sub.translator.secretyKey = '' 
    sub.generate_subtitle()

    print("subtitle generated")
    input("press any key to exit")


if __name__ =='__main__':
    main()