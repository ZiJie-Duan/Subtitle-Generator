from basic_tools import *
import json

class SubtitleTimestampFile:

    def __init__(self, progress, progress_data, file_path: str):
        """
        progress_data: {
            "subtitle_timestamp": [
                {
                    "text": "paragraph 1",
                    "word": <OpenAI Word Defined>
                },
                {
                    "text": "paragraph 2",
                    "word": <OpenAI Word Defined>
                }
            ]
        }
        """
        self.progress = progress
        self.progress_data = progress_data
        self.file_path = file_path
    
    def add_paragraph(self, text: str, word: object):
        self.progress_data["subtitle_timestamp"].append(
            {
            "text": text,
            "word": word
            }
        )
    
    def save_to_timestamp(self):
        with open(self.file_path, "w") as f:
            json.dump(self.progress_data["subtitle_timestamp"], f)

    
