from MessageBox import*

mp, print, orprint, printe, printse,\
printnn, printmid, print_mode_mute,\
print_mode_init = init_env()

@MessageBox(mp)
class SUBTITLE_WRITER:

    def __init__(self,files) -> None:
        self.files = files
        self.sub_index = 0
        self.file_subtitle = None
    
    def open(self):
        self.file_subtitle = open(self.files(),"a",encoding='utf-8')

    def close(self):
        self.file_subtitle.close()

    def fix_zero(self,number,msec=False):
        if msec:
            if len(str(number)) > 2:
                return str(number)
            elif len(str(number)) > 1:
                return "0"+str(number)
            else:
                return "00"+str(number)
        else:
            if len(str(number)) > 1:
                return str(number)
            else:
                return "0"+str(number)
        
    def write_line(self,data):
        data += "\n"
        self.file_subtitle.write(data)

    def write_subtitle(self,start,end,text,text2=None):
        data = str(self.sub_index) + "\n"
        data += "{}:{}:{},{} --> {}:{}:{},{}\n"\
            .format(\
                self.fix_zero(start[0]),\
                self.fix_zero(start[1]),\
                self.fix_zero(start[2]),\
                self.fix_zero(start[3],msec=True),\
                self.fix_zero(end[0]),\
                self.fix_zero(end[1]),\
                self.fix_zero(end[2]),\
                self.fix_zero(end[3],msec=True),\
                text)

        for sentence in text:
            data += sentence

        if text2 != None:
            data += "\n"
            for sentence in text2:
                data += sentence
                
        data += "\n"
        self.write_line(data)
        print(data)
        self.sub_index += 1


# from basic_tools import *

# file = FILE_PATH()
# file.set_path(r"C:\Users\lucyc\Desktop\subt.srt")
# fm = FILE_MANAGER()
# fm.add_file("OUT_SUBTITLE",file=file)
# subw = SUBTITLE_WRITER(fm)
# subw.open()
# subw.write_text((1,1,1,234),(4,3,2,123),["Hello world"])
# subw.write_text((1,1,2,234),(4,3,6,123),["My name is Peter Duan"])
# subw.close()