
class Subtitle:

    def __init__(self) -> None:
        self.subtitle = []
        self.location = 0
        self.lenth = 0
    
    def add_subtitle(self, subtitle: list) -> None:
        if self.subtitle == []:
            self.subtitle.append(subtitle)
            self.lenth += 1
            return True
        
        if subtitle[1] == self.subtitle[-1][1]:
            return False
        else:
            self.subtitle.append(subtitle)
            self.lenth += 1
            return True
    
    def get_subtitle(self, lenth: int = -1) -> None:
        if lenth == -1:
            location = self.location
            self.location = len(self.subtitle)
            self.lenth = 0
            return self.subtitle[location:]
        else:
            return self.subtitle[-lenth:]
    

    def get_subtitle_str(self, lenth: int = -1) -> str:
        subtitle = self.get_subtitle(lenth)
        subtitle_str = ""
        for i in subtitle:
            subtitle_str += i[0] + i[1] + "\n"
        return subtitle_str



class SubtitleWriter:
    """一个用于写入字幕文件的类"""

    def __init__(self,files:object) -> None:
        self.files = files
        self.sub_index = 0
        self.file_subtitle = None
    
    def open(self):
        """打开字幕文件"""
        self.file_subtitle = open(self.files(),"a",encoding='utf-8')

    def close(self):
        """关闭字幕文件"""
        self.file_subtitle.close()

    def fix_zero(self,number,msec=False):
        """修正数字格式"""
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
        """写入一行字幕"""
        data += "\n"
        self.file_subtitle.write(data)

    def write_subtitle(self,start :list, end :list, text: list):
        """
        写入一条字幕
        start - 开始时间
        end - 结束时间
        text - 字幕文本列表
        """
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
            data += sentence + "\n"
                
        data += "\n"
        self.write_line(data)
        print(data)
        self.sub_index += 1


# from basic_tools import *

# file = FilePath(r"C:\Users\lucyc\Desktop\jj.str")
# subw = SubtitleWriter(file)
# subw.open()
# subw.write_subtitle((1,1,1,234),(4,3,2,123),["Hello world","good day"])
# subw.write_subtitle((1,1,2,234),(4,3,6,123),["My name is Peter Duan"])
# subw.close()