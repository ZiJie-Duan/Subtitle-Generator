import basic_tools
import json
import os

class Memo:
    def __init__(self, file_path: object):
        self.mute = False
        self.file_path = file_path
        self.data = {}

    def load(self):
        with open(self.file_path(), "r") as f:
            self.data = json.load(f)

    def save(self):
        if self.mute:
            return
        with open(self.file_path(), "w") as f:
            json.dump(self.data, f)

    def exist(self):
        return os.path.exists(self.file_path())
    
    def __call__(self, section: str, key: str):
        return self.data[section][key]
    
    def update(self, section: str, key: str, value, save=False):
        self.data[section][key] = value
        if save:
            self.save()
    
    def obj_update(self, section: str, key: str):
        return self.data[section][key]

    def add_section(self, section: str, save=False):
        self.data[section] = {}
        if save:
            self.save()

    def clean(self):
        os.remove(self.file_path())

    
# ss = SecureSave(basic_tools.FilePath("secure_save.json", True))
# ss.set_basic_info("TestTask", "TestTask_1", "2021-10-10", "hello/test.mp3")
# ss.save()