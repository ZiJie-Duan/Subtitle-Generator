
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
        #self.sub_index = 0
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

    def time_convert(self, time):
        hours = time // 3600
        remain = time % 3600
        min = remain // 60
        remain = remain % 60
        sec = remain // 1
        msec = remain % 1
        msec = (msec // 0.001)
        return (int(hours),int(min),int(sec),int(msec))

    def write_subtitle(self, index:int, start :list, end :list, text: list):
        """
        写入一条字幕 (1,1,1,234),(4,3,2,123),["Hello world","good day"]
        index - 字幕序号 ex: 1
        start - 开始时间 ex: (1,1,1,234)
        end - 结束时间 ex: (4,3,2,123)
        text - 字幕文本列表 ex: ["Hello world","good day"]
        """
        data = str(index) + "\n"
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
        
        self.write_line(data)
    
    def write_subtitle_timestamp(self, index, start, end, text):
        """写入一条字幕，时间戳格式"""
        self.write_subtitle(index,
                            self.time_convert(start),
                            self.time_convert(end),
                            text
                            )



class SubtitleDecoder:

    def __init__(self) -> None:
        self.subtitle = []
        self.index = 0

    def reset(self):
        self.subtitle = []
        self.index = 0

    def decode(self, subtitle: str) -> list:
        # [((1,1,1,234),(4,3,2,123),["Hello world","good day"]), ...]

        subtitle_list = subtitle.split("\n\n")
        for i in subtitle_list:
            self.index += 1
            pic = i.split("\n")
            time_str = pic[1].split(" --> ")

            start = time_str[0].split(":")
            start_last = start.pop().split(",")
            start += start_last

            end = time_str[1].split(":")
            end_last = end.pop().split(",")
            end += end_last
            
            start = [int(i) for i in start]
            end = [int(i) for i in end]

            content = [pic[2]]
            self.subtitle.append((self.index, start, end, content))

        return self.subtitle



# ---------- TEST CODE ------------

# sbd = SubtitleDecoder()
# sub = sbd.decode("""""")

# from basic_tools import *
# file = FilePath(r"C:\Users\lucyc\Desktop\jj.str")
# subw = SubtitleWriter(file)
# subw.open()
# for i in sub:
#     subw.write_subtitle(i[0],i[1],i[2],i[3])
# subw.close()

# from basic_tools import *

# file = FilePath(r"C:\Users\lucyc\Desktop\jj.str")
# subw = SubtitleWriter(file)
# subw.open()
# subw.write_subtitle((1,1,1,234),(4,3,2,123),["Hello world","good day"])
# subw.write_subtitle((1,1,2,234),(4,3,6,123),["My name is Peter Duan"])
# subw.close()