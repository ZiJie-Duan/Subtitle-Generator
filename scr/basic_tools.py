import platform
import os

from memo import *

class FILE_PATH:
    def __init__(self):
        self.system = platform.system()
        self.file_path = None
        self.file_name = None
        self.file_working_path = None
    
    def __call__(self):
        return self.file_path
    
    def _path_check(self, file_path):
        tmp_path = file_path.split("\\")
        if "." in tmp_path[-1]:
            return True
        else:
            return False

    def set_path(self, file_path):
        if self.system == "Windows":
            if self._path_check(file_path):
                self.file_path = file_path
                tmp = file_path.split("\\")
                self.file_name = tmp[-1]
                tmp = tmp[:-1]
                self.file_working_path = "\\".join(tmp)
                return True
            else:
                return False

        else:
            pass # MAC or other system
    

@MEMO()
class FILE_MANAGER:

    def __init__(self):
        self.files = {}

    def __call__(self,sign):
        return self.files[sign].file_path
    
    def add_file(self,sign,file):
        self.files[sign] = file
    
    def build_new_file(self, sign, file_name):
        if self.system == "Windows":
            return self.files[sign].file_working_path + "\\" + file_name

        else:
            pass # MAC or other system


class SYSTEM_CMD:

    def __init__(self):
        self.system = platform.system()

    def __call__(self, cmd="NONE"):
        if cmd == "NONE":
            pass
        else:
            self.cmd(cmd)
    
    def cmd(self, cmd):
        if self.system == "Windows":
            os.system(cmd)

        else:
            pass # MAC or other system


    # def cmd_with_return(self, cmd):
    #     if self.system == "Windows":
    #         return os.popen(cmd).read()

    #     else:
    #         pass # MAC or other system
    
    def open_file(self, file_path):
        if self.system == "Windows":
            os.startfile(file_path)
        
        else:
            pass # MAC or other system


# test code

# @MEMO(memory)
# def wr():
#     pass

# test = PATH_CONVERT()
# print(test.file_path)
# print(test.file_working_path)
# print(test.file_name)
# wr()
# input()