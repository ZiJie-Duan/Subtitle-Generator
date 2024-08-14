
# Subtitle Generator

![License](https://img.shields.io/badge/license-MIT-blue)
![Version](https://img.shields.io/badge/versions-v1.3.0-alpha-orange)
[Windows-image]: <https://img.shields.io/badge/-Windows-blue?logo=windows>
[MacOS-image]: <https://img.shields.io/badge/-MacOS-black?logo=apple>
[Linux-image]: <https://img.shields.io/badge/-Linux-333?logo=ubuntu>
![image](logo.jpg)

## Project Overview

Subtitle Generator is a Python project based on the OpenAI Whisper model and GPT-4 series models. It aims to simplify the process of generating multilingual subtitles from media files. By leveraging advanced prompt engineering, this project produces subtitles that far surpass the quality of YouTube's auto-generated captions and translations, especially optimized for complex sentences, inverted structures, and the unique characteristics of different languages. Additionally, it features a user-friendly operation logic with numerous prompts, making it easy to use.

## Key Features

- **Media File Processing**: Supports converting media files (e.g., MP4, MP3) into timestamped word files.
- **Subtitle Generation**: Generates subtitle files from timestamp files, supporting bilingual subtitles.
- **Smart Detection**: Automatically detects the file type and processes it accordingly, streamlining the workflow.
- **Crash Protection**: In the event of a program crash, a "secure_save.json" file is generated to protect processed information, avoiding unnecessary API costs.

## Requirements

- An OpenAI API key is required.

## Quick Start

### Installation Steps

1. Clone this repository to your local machine.
2. Create a Python virtual environment:

   ```
   python3 -m venv xxx_env
   ```

3. Activate the virtual environment.
4. Install the project dependencies:

   ```
   pip install -r requirements.txt
   ```

   If your network connection is unstable, consider using a proxy:

   ```
   pip install -r requirements.txt --proxy=http://[address]:[port]
   ```

### Usage

#### Basic Operations

1. **Generating Timestamp Files**:
   - Open a terminal and enter the following command, replacing with your specific paths:

     ```
     python [project_path]/Subtitle-Generator/src/main.py [your_video_file_path]
     ```

   - The program will generate a `.json` file with the same name as your video file, containing all the text information extracted from the audio.

2. **Generating Subtitle Files**:
   - Open a terminal and enter the following command, replacing with your specific paths:

     ```
     python [project_path]/Subtitle-Generator/src/main.py [your_video_json_path]
     ```

   - Follow the prompts to select the language for translation or generate subtitles in the original language.

### Important Notes

- **API Key Storage**: After entering your API key for the first time, the program will store it in a `config.ini` file located in the same directory as `main.py`. Please ensure not to submit or share this file. You can delete it at any time, and the program will prompt you to enter the API key again upon the next startup.
- **Crash Protection**: If the program encounters an unexpected crash, it will save a secure storage file. When you restart the program, it will automatically resume from the point of failure.

## Getting Help

- **Built-in Help**: If you double-click to run the program without passing any files, this guide will be displayed to help you understand how to use it.
- **Troubleshooting**: If you encounter issues during use, follow the prompts provided by the program to ensure the correct file paths and API key are entered.

## Enjoy Creating Subtitles with Ease
