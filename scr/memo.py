import json
from types import FunctionType

"""
from memo import *
memory = MEMORY()

@MEMO(memory)
"""

class MEMORY:

    def __init__(self) -> None:
        self.memo = {}
        self.memo_path = "memo.json"
        self.memo_load()
    
    def __call__(self, key):
        return self.memo[key]
    
    def memo_load(self):
        try:
            with open(self.memo_path,"r") as f:
                self.memo = json.load(f)
        except:
            self.memo = {}

    def memo_write(self):
        with open(self.memo_path,"w") as f:
            json.dump(self.memo,f)
        
    def memo_add(self,key,value):
        self.memo[key] = value
        self.memo_write()
    
    def memo_del(self,key):
        del self.memo[key]
        self.memo_write()


class MEMO:
    """
    MEMO is a wrapper
    if used to record the value of attributes of each class

    it can be used on functions or classes.
    in functions, it will save the data in a file when the function start.
    in classes, it will record all the attributes when the init-function finished.
    """

    def __init__(self, memory, memory_mode = "normal"):
        self.memory_mode = memory_mode
        self.memory = memory
    
    def __call__(self, mclass):
        
        if isinstance(mclass,FunctionType):
            # cla is a function
            mfunction = mclass
            func = self.writer(mfunction)
            return func
        else:
            mclass.__init__ = self.initer(mclass.__init__)

            return mclass

    def writer(self,mfunction):
        def wrapper(*args, **kwds):
            self.save()
            return mfunction(*args, **kwds)
        return wrapper
    
    def initer(self,mfunction):
        def wrapper(*args, **kwds):
            mfunction(*args, **kwds)
            if args[0].__class__.__name__ in self.memory.memo:
                for key, value in self.memory.memo[args[0].__class__.__name__].items():
                    args[0].__dict__[key] = value
            self.memory.memo[args[0].__class__.__name__] = args[0].__dict__
        return wrapper

    def save(self):
        self.memory.memo_write()


# memory = MEMORY()

# @MEMO(memory)
# class say_hello:

#     def __init__(self) -> None:
#         self.name = None
#         self.name2 = None

#     @MEMO(memory)
#     def say_hello(self):
#         print("hello {}".format(self.name))
    
#     def say2_hello(self):
#         print("hello {} and {}".format(self.name,self.name2))


# sh = say_hello()
# sh.say_hello()
# sh.say2_hello()
# print()
