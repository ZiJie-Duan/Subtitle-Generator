import time
import sys
from types import FunctionType
import os
"""
Message Box v2.0

How to use it

from MessageBox import*
mp, print, orprint, printe, printse,\
printnn, printmid, print_mode_mute,\
print_mode_init = init_env()

@MessageBox(mp)

add these code befor function or class

"""

class MessagePrinter:

    def __init__(self) -> None:
        self.setting = {
            "date_and_time" : False,
            "time" : True,
            "source" : True,
            "type" : True,
        }
            #type有四种类型
            # IS-info, INFO, ERR, Serious-ERR, WARN
            # inside_info 不具有用户提示的属性
        self.orprint = print
        self.message_list = []
    
    def init_args(self):
        self.setting = {
            "date_and_time" : False,
            "time" : True,
            "source" : True,
            "type" : True,
        }

    def mute(self):
        self.setting = {
            "date_and_time" : False,
            "time" : False,
            "source" : False,
            "type" : False,
        }

    def message_maker(self,message,type="INFO",source="None"):
        ms = ""
        if self.setting["date_and_time"]:
            t = time.time()
            timeArray = time.localtime(t)
            ms += time.strftime("%Y-%m-%d %H:%M:%S ", timeArray)
        if self.setting["time"]:
            t = time.time()
            timeArray = time.localtime(t)
            ms += time.strftime("%H:%M:%S ", timeArray)
        if self.setting["type"]:
            ms += "[{}]".format(type)
        if self.setting["source"]:
            ms += "({}):".format(source) #here I fixed the ":" Bug
        ms += str(message)

        self.message_list.append(ms)

    def message_printer(
        self,
        f_sp = 0, #front_space #step0
        b_sp = 0, #back_space #step-2
        sp = 0, #this space in front of the text in a line #step-1
        line_break = True, #\n #step3
        centered = False, #centered print #step2
        clean = False, #print a new message after clean the screen #step1
        ):

        [self.orprint("") for _ in range(f_sp)]

        if clean:
            os.system('cls')

        if centered:
            width = os.get_terminal_size().columns
            for ms in self.message_list:
                start_point = (width - len(ms))//2
                [self.orprint(" ",end="") for _ in range(start_point)]
                self.orprint(ms)

        elif line_break:
            [self.orprint(" ",end="") for _ in range(sp)]
            [self.orprint(ms) for ms in self.message_list]
        else:
            [self.orprint(" ",end="") for _ in range(sp)]
            [self.orprint(ms,end="") for ms in self.message_list]

        [self.orprint("") for _ in range(b_sp)]
        self.message_list = []

class MessageBox:

    def __init__(self,mp,mode="easy"):
        #here input arguments
        self.mp = mp # message class
        self.mode = mode # mode choice 
    
    def __call__(self,cla):
        # find out all of the functions created by the programmer
        if isinstance(cla,FunctionType):
            # cla is a function
            func = self.wrapper_maker(cla)
            return func
        else:
            # cla is a class

            all_functions = dir(cla)
            function_list = []
            for function in all_functions:
                if "__" == function[:2] and "__" == function[-2:]:
                    pass
                else:
                    function_list.append(function)

            # cover the original code to add the wrapper
            for function in function_list:
                exec("cla.{} = self.wrapper_maker(cla.{})".\
                    format(function,function))
            return cla

    def wrapper_maker(self,func):
        if self.mode == "easy":
            def wrapper(*args, **kwds):
                return func(*args, **kwds)
            return wrapper

        elif self.mode == "normal":
            def wrapper(*args, **kwds):
                self.mp.message_maker("start running","IS-info",func.__name__)
                self.mp.message_printer()
                return func(*args, **kwds)
                # here must get the number of the arguments
                # then chooise use *args or not 
            return wrapper

        else:
            def wrapper(*args, **kwds):
                self.mp.message_maker("start running","IS-info",func.__name__)
                self.mp.message_printer()
                result = func(*args, **kwds)
                self.mp.message_maker("finish","IS-info",func.__name__)
                self.mp.message_printer()
                return result
            return wrapper

def init_env():
    mp = MessagePrinter()

    def print(message,type="INFO",f_sp=0,b_sp=0,sp=0):
        source = sys._getframe().f_back.f_code.co_name
        mp.message_maker(message,type,source)
        mp.message_printer(f_sp=f_sp,b_sp=b_sp,sp=sp)
    
    def orprint(*args,**kwds):
        mp.orprint(*args,**kwds)
    
    def printe(message,type="ERR",f_sp=1,b_sp=1,sp=0):
        source = sys._getframe().f_back.f_code.co_name
        mp.message_maker(message,type,source)
        mp.message_printer(f_sp=f_sp,b_sp=b_sp,sp=sp)

    def printse(message,type="Serious-ERR",f_sp=2,b_sp=2,sp=0):
        source = sys._getframe().f_back.f_code.co_name
        mp.message_maker(message,type,source)
        mp.message_printer(f_sp=f_sp,b_sp=b_sp,sp=sp)
        input("[Press Enter to continue...]")
    
    def printnn(message,type="INFO",f_sp=0,sp=0):
        source = sys._getframe().f_back.f_code.co_name
        mp.message_maker(message,type,source)
        mp.message_printer(f_sp=f_sp,line_break=False,sp=sp)
    
    def printmid(message,type="INFO",f_sp=0,b_sp=0,clean=False):
        source = sys._getframe().f_back.f_code.co_name
        mp.message_maker(message,type,source)
        mp.message_printer(f_sp=f_sp,b_sp=b_sp,clean=clean,centered=True)
    
    def print_mode_mute():
        mp.mute()
    def print_mode_init():
        mp.init_args()

    return mp, print, orprint, printe, printse,\
        printnn, printmid, print_mode_mute, print_mode_init

