import basic_tools
import json

class SecureSave:
    def __init__(self, file_path: object):
        self.file_path = file_path
        self.data = None
        self.progress = {}
        self.progress_data = {}

    def load(self):
        with open(self.file_path, "r") as f:
            self.data = json.load(f)

    def save(self):
        with open(self.file_path, "w") as f:
            json.dump(self.data, f)
    
    def set_basic_info(self,type, name, date):
        self.data = {
            "Task_Type": type,
            "Task_Name": name,
            "Task_Date": date,
            "Task_Progress": None,
            "Task_Data": None
        }

    def get_control_handle(self):
        return self.progress, self.progress_data
    
    def update(self):
        self.data["Task_Progress"] = self.progress
        self.data["Task_Data"] = self.progress_data
        self.save()

    
