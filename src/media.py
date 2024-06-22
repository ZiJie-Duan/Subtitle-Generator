from basic_tools import *

class Media:
    """媒体音频控制类
       目前仅对音频进行操作
       同时仅支持Windows系统
    """

    def __init__(self, infile: object, cmd: object ,outfile: object=None):
        self.infile = infile              # 输入文件路径对象
        self.cmd = cmd                    # 命令执行对象
        self.duration = self.get_length(self.infile()) # 获取音频时长

        if outfile == None:       
            # 如果没有设定输出文件路径，自动生成一个临时文件
            self.outfile = infile.nfile(full_name="temp.mp3")
        else:
            self.outfile = outfile       # 设置输出文件路径

        self.split_start = 0              # 分割开始时间
        self.finish_flag = 0              # 分割完成标志


    def init_process(self):
        """
        初始化进程
        """
        self.split_start = 0
        self.finish_flag = 0


    def get_length(self,filename):
        """
        获取音频文件时长
        """
        args = ["ffprobe", "-v", "error", "-show_entries",
                "format=duration", "-of",
                "default=noprint_wrappers=1:nokey=1", filename]
        return float(self.cmd.run(args))


    def splite_audio(self, start, duration): 
        """
        分割音频 start: 开始时间 duration: 时长
        """
        args = ["ffmpeg", "-i", self.infile(), "-ss", str(start), 
                "-t", str(duration), "-aq", "0", "-map", "a", 
                self.outfile()]
        self.cmd.run(args)
        return self.outfile()
        

    def get_audio_pice(self, lenth = -1):
        """
        通过分割音频获取音频片段
        lenth : 时长， -1 为默认值，表示获取全部音频
        """
        if self.outfile.exist():
            self.outfile.delete()
            
        if self.finish_flag == 1:
            return False

        if (lenth == -1) or (lenth + self.split_start > self.duration):
            # 当lenth处于默认值-1 或者 分割长度加上分割开始时间大于音频总时长时
            # 全选音频 或 全选剩余音频
            # 请注意 self.split_start 默认值为0，所以当lenth为-1时，会全选音频
            self.finish_flag = 1
            res = self.splite_audio(self.split_start, self.duration)
            self.split_start = self.duration
            return res
        
        else:
            res = self.splite_audio(self.split_start, lenth)
            self.split_start = self.split_start + lenth
            return res



# import vlc
# import time

# # 创建VLC实例
# instance = vlc.Instance()

# # 创建一个新的媒体播放器对象
# player = instance.media_player_new()

# md = Media(FilePath(r"C:\Users\lucyc\Desktop\7e510bff71993a21eb8f68adb133dcc8.mp4"),
#            SystemCmd())


# for i in range(5):

#     # 设置媒体源
#     media = instance.media_new(md.get_audio_pice(10))
#     player.set_media(media)

#     # 播放音频
#     player.play()
#     time.sleep(10)