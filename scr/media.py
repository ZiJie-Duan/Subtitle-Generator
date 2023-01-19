from basic_tools import *
from MessageBox import*
import subprocess

mp, print, orprint, printe, printse,\
printnn, printmid, print_mode_mute,\
print_mode_init = init_env()


@MessageBox(mp)
class MEDIA:
    def __init__(self, file, cmd):
        self._file = file
        self._cmd = cmd
        self._duration = 0
    
    def set_media(self, file_path):
        if self._file.set_path(file_path):
            self._duration = self.get_length(self._file())
            print("set media file success")
        else:
            print("set media file failed")

    def get_length(self,filename):
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                "format=duration", "-of",
                                "default=noprint_wrappers=1:nokey=1", filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        return float(result.stdout)

    def splite_audio(self,start=0,duration=0,new_fname="new.wav"):
        if duration == 0:
            duration = self._duration
            
        self._cmd("ffmpeg -i {} -ss {} -t {} -aq 0 -map a {}"\
            .format(self._file(),start,\
            duration,self._file.build_new_file(new_fname)))
    
    # def change_segment(self, start=0, duration=30):
    #     if self._timess['start'] == 0:

    #     self._timess['start'] = start
    #     self._timess['duration'] = duration
            

# if __name__ == "__main__":
#     file = PATH_CONVERT()
#     cmd = SYSTEM_CMD()
#     media = MEDIA(file, cmd)
#     media.set_media(r"C:\Users\lucyc\Desktop\aaa.mp4")
#     # for x in range(6):
#     #     media._timess["start"] = x*30
#     #     media._timess["duration"] = 30
#     #     media.splite_audio(new_file_name=str(x)+".wav")
#     media._timess["start"] = 0
#     media._timess["duration"] = 180
#     media.splite_audio(new_file_name="a.wav")
#     input("Press any key to exit")