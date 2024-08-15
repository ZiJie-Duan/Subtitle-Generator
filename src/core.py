import asyncio
import json
import math
from os import walk
import random
import time

from config import DockerConfig
from memo import Memo
from openai_api import GPTApi, WisperApi
from subtitle import SubtitleWriter

"""
通用任务数据定义（每一个任务都会基于一个文件进行操作）：
在Section "TaskInfo" 中定义
TaskInfo = {
    "Task_Type": type,
    "Task_Name": name,
    "Task_Date": date,
    "Task_File": file_path,
    "Task_Progress" : float
}
在Section "TaskData" 中定义 其他的客制化数据
"""


def proportional_merge(combination, comb_time_map):
    sentences = []
    time_map = []

    comb_start = min([x[0] for x in comb_time_map])
    comb_end = max([x[1] for x in comb_time_map])
    max_length = len("".join(combination))
    comb_time_diff = comb_end - comb_start

    for index, sentence in enumerate(combination):
        duration = (len(sentence) / max_length) * comb_time_diff

        sentences.append(sentence)

        if index == 0:
            time_map.append((comb_start, comb_start + duration))
        else:
            time_map.append((time_map[-1][1], time_map[-1][1] + duration))

    return sentences, time_map


def subtitle_proportional_merge(sentences, time_map):
    sentences.append("END_OF_SUBTITLE")
    time_map.append((float("inf"), float("inf")))

    n_sentences = []
    n_time_map = []

    combination = []
    comb_time_map = []
    cbst = time_map[0][0]
    cben = time_map[0][1]

    is_comb = False

    for i in range(1, len(sentences)):
        if (
            cbst > time_map[i][0]
            or cbst > time_map[i][1]
            or cben > time_map[i][0]
            or cben > time_map[i][1]
        ):
            # i even don't belive that
            # my program can leave this line to work
            # -----------FUNNY BUG---------------------
            combination.append(sentences[i - 1])
            # -----------------------------------------
            comb_time_map.append(time_map[i - 1])
            cbst = min(cbst, time_map[i][0])
            cben = max(cben, time_map[i][1])
            is_comb = True

        else:
            if not is_comb:
                n_sentences.append(sentences[i - 1])
                n_time_map.append(time_map[i - 1])
                cbst = time_map[i][0]
                cben = time_map[i][1]

            else:
                combination.append(sentences[i - 1])
                comb_time_map.append(time_map[i - 1])

                s, t = proportional_merge(combination, comb_time_map)
                n_sentences += s
                n_time_map += t

                cbst = time_map[i][0]
                cben = time_map[i][1]
                combination = []
                comb_time_map = []
                is_comb = False

    # make each timestamp shorter
    # because float compare in Overlapping Check
    for i in range(1, len(n_sentences)):
        if n_time_map[i - 1][1] > n_time_map[i][0]:
            print("ERROR: Overlapping subtitles.")
            print(
                "time {}, Subtitle 1: {}".format(n_time_map[i - 1], n_sentences[i - 1])
            )
            print("time {}, Subtitle 2: {}".format(n_time_map[i], n_sentences[i]))

    return n_sentences, n_time_map


def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def match_sentence(short_sentence, word_list):
    short_sentence = short_sentence.replace(" ", "")
    min_dis = 9999999
    match_index = None

    for i in range(0, len(word_list)):
        dis = levenshtein_distance(short_sentence, "".join(word_list[0 : i + 1]))
        if dis <= min_dis:
            min_dis = dis
            match_index = i

    return match_index, "".join(word_list[0 : match_index + 1])


class AudioToSubtitleTimestamp:
    """
    Task Transfer audio to subtitle with timestamp

    TaskInfo:{
        Task_Type = "toSubtitleTimestampFile"
        Task_Name = "AudioToSubtitleTimestamp_{file_name}"
        Task_Progress =  23 FLOAT
    }

    TaskData:{
        "media_split_point" = 1254.23 FLOAT,
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

    def __init__(
        self, cfg: DockerConfig, gpt: GPTApi, wis: WisperApi, memo: Memo, media: object
    ):
        self.cfg = cfg
        self.gpt = gpt
        self.wis = wis
        self.memo = memo
        self.media = media

    def init_task(self):
        self.media.init_process()
        self.memo.update("TaskInfo", "Task_Type", "toSubtitleTimestampFile")
        self.memo.update(
            "TaskInfo",
            "Task_Name",
            "AudioToSubtitleTimestamp_{}".format(self.media.infile()),
        )
        self.memo.update(
            "TaskInfo",
            "Task_Date",
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        )
        self.memo.update("TaskInfo", "Task_File", self.media.infile())
        self.memo.update("TaskInfo", "Task_Progress", 0)

        self.memo.update("TaskData", "media_split_point", 0)
        self.memo.update("TaskData", "subtitle_timestamp", [], save=True)
        print("[AudioToSubtitleTimestamp] : Task Init.")

    def continue_task(self):
        self.media.split_start = self.memo("TaskData", "media_split_point")
        print("[AudioToSubtitleTimestamp] : Continue Task")

    def update_progress(self):
        self.memo.update(
            "TaskInfo",
            "Task_Progress",
            self.media.split_start / self.media.duration * 100,
        )
        self.memo.update(
            "TaskData", "media_split_point", self.media.split_start, save=True
        )
        print(
            "[AudioToSubtitleTimestamp] : Progress : {}%".format(
                str(self.memo("TaskInfo", "Task_Progress"))
            )
        )

    def run(self):
        while True:
            audio_pice, diff = self.media.get_audio_pice(60)
            if not audio_pice or diff < 2:
                break

            with open(audio_pice, "rb") as audio_file:
                data = self.wis.transcribe_timestamp(audio_file)

            data_list = self.memo.obj_update("TaskData", "subtitle_timestamp")

            words = []
            for word in data.words:
                words.append(
                    {
                        "word": word["word"],
                        "start": word["start"]
                        + self.memo("TaskData", "media_split_point"),
                        "end": word["end"] + self.memo("TaskData", "media_split_point"),
                    }
                )

            data_list += [{"text": data.text, "word": words}]

            self.update_progress()

        self.save()
        self.memo.clean()

    def save(self):
        file_path = self.media.infile.nfile(ext="json")
        print(file_path())
        with open(file_path(), "w") as f:
            json.dump(self.memo("TaskData", "subtitle_timestamp"), f)


def gpt_split_sentence(gpt: GPTApi, text: str):
    prompt = """
You are a subtitle segmenter. Your task is to segment the text enclosed in <<<>>> symbols into short sections based on semantics and pauses, with each section not exceeding 12 words and containing no punctuation. Each segmented subtitle should be presented in the following format:
---
subtitle text 1
---
subtitle text 2
---
Maintain the natural flow of the dialogue and ensure each segment can independently convey a complete meaning. Do not provide any explanations with your outputs. Do not modify any text.
    """
    success = False

    for i in range(5):
        try:
            usermsg = "<<<{}>>>".format(text)
            message = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": usermsg},
            ]
            response = gpt.query(
                message, max_tokens=4000, temperature=0.1, model="gpt-4o-mini"
            )
            sentences = response[4:-4].split("\n---\n")
            success = True
            break
        except:
            print("[gpt_split_sentence]: gpt-4o-mini Invalid Response.")
            print("[gpt_split_sentence]: Retry {} times.".format(i + 1))
            continue

    if not success:
        print("[gpt_split_sentence]: gpt-4o-mini Invalid Response.")
        print("[gpt_split_sentence]: Please Check Your Network.")
        print("[gpt_split_sentence]: Exit.")
        input("Press Enter to Exit...")
        exit(0)

    # print("DEBUG 原文: ", text)
    return sentences


def euclidean_distance(vector1, vector2):
    if len(vector1) != len(vector2):
        raise ValueError("The length of two vectors must be the same.")

    distance = math.sqrt(sum((x - y) ** 2 for x, y in zip(vector1, vector2)))
    return distance


async def get_embedding_async(gpt, sentence):
    loop = asyncio.get_running_loop()  # 获取当前运行的事件循环
    response = await loop.run_in_executor(None, gpt.get_embedding, sentence)
    return response


async def get_embedding_list_async(gpt, sentences):
    tasks = [get_embedding_async(gpt, sentence) for sentence in sentences]
    embeddings = await asyncio.gather(*tasks)
    return embeddings


class SubStampToSubtitleOriginal:
    """
    Task Transfer subtitle timestamp to subtitle

    TaskInfo:{
        Task_Type = "toSubtitleOriginal"
        Task_Name = "SubStampToSubtitleOriginal_{file_name}"
        Task_Progress =  23 FLOAT
    }

    TaskData:{
        "paragraph_index" = 0 INT,  # 当前段落索引 来自字幕时间戳文件
        "paragraph": "xxx" STR,     # 当前段落文本 来自字幕时间戳文件
        # 以上两个变量是在 以 段落为单位颗粒度的保存

        "sentence": [] LIST,        # 由GPT进行分段的句子
        "word_timestamp": [] LIST,  # 当前段落的单词时间戳 来自字幕时间戳文件
        "subtitle_match": [] LIST,   # 完成时间定位的字幕与其时间戳
        # 以上三个变量是在 以句子为单位颗粒度的保存
        # sentences 和 word_timestamp 是一一对应的, 匹配之后将会被逐步弹出移除
        # subtitle_match 是匹配之后的结果, 会被逐步添加，直到 sentence 和 word_timestamp 为空

        # 当subtitle_match 完成后，将会被写入到 subtitle_srt 中
    }
    """

    def __init__(
        self,
        cfg: DockerConfig,
        gpt: GPTApi,
        wis: WisperApi,
        memo: Memo,
        subwriter: SubtitleWriter,
        timestamp_file: object,
    ):
        self.cfg = cfg
        self.gpt = gpt
        self.wis = wis
        self.memo = memo
        self.subwriter = subwriter
        self.timestamp_file = timestamp_file
        self.timestamp = None

        self.load_timestamp()

    def load_timestamp(self):
        with open(self.timestamp_file(), "r") as f:
            self.timestamp = json.load(f)

    def init_task(self):
        self.memo.update("TaskInfo", "Task_Type", "toSubtitleOriginal")
        self.memo.update("TaskInfo", "Task_File", self.timestamp_file())
        self.memo.update(
            "TaskInfo",
            "Task_Name",
            "SubStampToSubtitleOriginal_{}".format(self.memo("TaskInfo", "Task_File")),
        )
        self.memo.update(
            "TaskInfo",
            "Task_Date",
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        )
        self.memo.update("TaskInfo", "Task_Progress", 0)
        self.memo.update("TaskData", "paragraph_index", 0)
        self.memo.update("TaskData", "paragraph", "")
        self.memo.update("TaskData", "sentences", [])
        self.memo.update("TaskData", "word_timestamp", [])
        self.memo.update("TaskData", "subtitle_match", [])
        self.memo.update("TaskData", "subtitle_srt", "", save=True)
        print("[SubStampToSubtitleOriginal] : Task Init.")

    def continue_task(self):
        print("[SubStampToSubtitleOriginal] : Continue Task")

    def update_progress(self):
        self.memo.update(
            "TaskInfo",
            "Task_Progress",
            self.memo("TaskData", "paragraph_index") / len(self.timestamp) * 100,
            save=True,
        )
        print(
            "[SubStampToSubtitleOriginal] : Progress : {}%".format(
                str(self.memo("TaskInfo", "Task_Progress"))
            )
        )

    def run(self):
        while True:
            paragraph_index = self.memo("TaskData", "paragraph_index")
            if paragraph_index == len(self.timestamp):
                break

            print(
                "[SubStampToSubtitleOriginal] : Processing Paragraph : {}".format(
                    paragraph_index
                )
            )

            if self.memo("TaskData", "paragraph") == "":
                self.memo.update(
                    "TaskData", "paragraph", self.timestamp[paragraph_index]["text"]
                )

            if self.memo("TaskData", "word_timestamp") == []:
                self.memo.update(
                    "TaskData",
                    "word_timestamp",
                    self.timestamp[paragraph_index]["word"],
                )

            if self.memo("TaskData", "sentences") == []:
                sentences = gpt_split_sentence(
                    self.gpt, self.memo("TaskData", "paragraph")
                )
                self.memo.update("TaskData", "sentences", sentences)

            while True:
                if self.memo("TaskData", "sentences") == []:
                    break

                sentence = self.memo("TaskData", "sentences")[0]

                # 英文和中文的分词不同，需要进行匹配
                # 考虑性能 和 分词复杂度， 在这里选择不进行长度相关的分词
                # 直接将整个段落 与 时间戳进行匹配
                # length = len(sentence.split(" "))

                words_data = self.memo("TaskData", "word_timestamp")[:]

                if len(words_data) == 0:
                    print(words_data)
                    print(sentence)
                    print(self.memo("TaskData", "sentences"))
                    print(
                        "[SubStampToSubtitleOriginal] : Error, Segmentation misplacement leads to an empty list."
                    )
                    print(
                        "[SubStampToSubtitleOriginal] : This error will cause partial misalignment of subtitles and some subtitles not to display, but it will not affect subsequent subtitles. The next version will fix this issue."
                    )
                    break

                words_list = [x["word"] for x in words_data]
                last_index, matched_st = match_sentence(sentence, words_list)

                print(
                    "[SubStampToSubtitleOriginal] : Processing Sentence : {}".format(
                        sentence
                    )
                )
                print(
                    "[SubStampToSubtitleOriginal] : Matched Words       : {}".format(
                        matched_st
                    )
                )

                start_time = words_data[0]["start"]
                end_time = words_data[last_index]["end"]

                # 将以下三个操作 合并为一个操作 原子性操作
                self.memo.obj_update("TaskData", "subtitle_match").append(
                    {"text": sentence, "start": start_time, "end": end_time}
                )
                self.memo.update(
                    "TaskData",
                    "word_timestamp",
                    self.memo("TaskData", "word_timestamp")[last_index + 1 :],
                )
                self.memo.obj_update("TaskData", "sentences").pop(0)
                self.memo.save()

            # print("debug : add pindex ") Becareful, why paragraph_index not correct
            self.memo.update("TaskData", "paragraph_index", paragraph_index + 1)
            self.memo.update("TaskData", "paragraph", "")
            self.memo.update("TaskData", "sentences", [])
            self.memo.update("TaskData", "word_timestamp", [])
            self.update_progress()

        self.save()
        self.memo.clean()

    def save(self):
        self.subwriter.open()
        index = 1
        for i in self.memo("TaskData", "subtitle_match"):
            self.subwriter.write_subtitle_timestamp(
                index, i["start"], i["end"], [i["text"]]
            )
            index += 1
        self.subwriter.close()


def try_to_query_gpt(gpt, fail, message, max_tokens, temperature, timeout):
    if fail < 3:
        temperature = random.uniform(temperature - 0.1, temperature + 0.1)
        temperature = max(0, temperature)
    else:
        temperature = 0

    if fail < 2:
        model = "gpt-4o-mini"
    elif fail < 4:
        model = "gpt-4o"
    else:
        model = "gpt-4"

    response = gpt.query(
        message,
        max_tokens=max_tokens,
        temperature=temperature,
        model=model,
        timeout=timeout,
    )
    return response


def gpt_split_sentence_translation(gpt: GPTApi, text: str, language: str):
    prompt_translation = """
You are a professional translator proficient in multiple languages. Your task is to translate the text enclosed by <<<>>> into {}, achieving the most natural and fluent translation possible.
Present in the following format:
---
example translated paragraph
---
""".format(language)

    prompt_split = """
You are a subtitle segmenter. Your task is to segment the text enclosed in <<<>>> symbols into short sections based on semantics and pauses, with each section not exceeding 12 words and containing no punctuation. Each segmented subtitle should be presented in the following format:
---
example subtitle text 1
---
example subtitle text 2
---
Maintain the natural flow of the dialogue and ensure each segment can independently convey a complete meaning. Do not provide any explanations with your outputs. Do not modify any text. 
    """

    prompt_match = """
Your task is to match sentences in two different languages that have the same meaning. The final output should be segmented results in both languages, matched in the specified format.

Text within <<<>>> contains fixed text, segmented by "|".
Text within ((( ))) contains text to be matched, without separators.
Match each segment of the fixed text with the most accurate segment from the text to be matched, ensuring the best possible meaning match. Multiple segments can be matched with each other, but aim for one-to-one correspondence as much as possible. Try to match the text to be matched in sequence.

Each segment should be presented in the following format:
---
example fixed text 1
-
example matched text 1
---
example fixed text 2
-
example matched text 2
---
Please do not provide any explanations and do not answer any questions.
"""
    success = False
    # print("DEBUG 原文: ", text)
    for i in range(5):
        try:
            usermsg = "<<<{}>>>".format(text)
            message = [
                {"role": "system", "content": prompt_translation},
                {"role": "user", "content": usermsg},
            ]
            # print("DEBUG stc: ", message)
            response = try_to_query_gpt(
                gpt, i, message, max_tokens=4000, temperature=1, timeout=60
            )
            sentences = response[4:-4]
            # print("DEBUG stc: ", sentences)

            usermsg = "<<<{}>>>".format(sentences)
            message = [
                {"role": "system", "content": prompt_split},
                {"role": "user", "content": usermsg},
            ]
            # "gpt-4o-mini"
            response = try_to_query_gpt(
                gpt, i, message, max_tokens=4000, temperature=0.1, timeout=60
            )
            sentences = response[4:-4].split("\n---\n")
            # print("DEBUG stc2: ", sentences)

            usermsg = "<<<{}>>> \n((({})))".format("|".join(sentences), text)
            message = [
                {"role": "system", "content": prompt_match},
                {"role": "user", "content": usermsg},
            ]
            response = try_to_query_gpt(
                gpt, i, message, max_tokens=4000, temperature=0.1, timeout=60
            )
            sentences = response[4:-4].split("\n---\n")
            # print("DEBUG stc3: ", sentences)
            sentences = [x.split("\n-\n") for x in sentences]
            translation = [x[0] for x in sentences]
            match_only = [x[1] for x in sentences]

            success = True
            break
        except Exception as e:
            print("[gpt_split_sentence_translation]: gpt Invalid Response.")
            print("[gpt_split_sentence_translation]: Retry {} times.".format(i + 1))
            print("[gpt_split_sentence_translation]: Error : {}".format(str(e)))
            continue

    if not success:
        print("[gpt_split_sentence_translation]: gpt Invalid Response.")
        print("[gpt_split_sentence_translation]: Please Check Your Network.")
        print("[gpt_split_sentence_translation]: Exit.")
        input("Press Enter to Exit...")
        exit(0)

    # print("DEBUG 原文: ", text)
    # print("DEBUG 翻译: ", translation)
    # print("DEBUG 匹配: ", match_only)

    return translation, match_only


def sliding_matching(words_data, sentences):
    """
    sliding matching alg
    match each sentence with words and timestamp
    """
    # remove all of the space in each sentences
    # this for different language
    sentences = [x.replace(" ", "") for x in sentences]
    words = []
    words_map = []
    time_map = []
    location = 0

    # timestamp is inside the words_data
    # the words_map make us can easily find the word via index
    for i, word in enumerate(words_data):
        wordStr = word["word"]
        for char in wordStr:
            words.append(char)
            words_map.append(i)

    for sentence in sentences:
        min_distance = 999999999
        min_location = 0

        # find the most accurate location in a longer sentence
        # min_location is the head location of the sub_string
        for i in range(0, len(words) - len(sentence) + 1):
            be_matched = "".join(words[i : i + len(sentence)])
            distance = levenshtein_distance(be_matched, sentence)
            distance += abs(i - location) * 0.1

            # print("be_matched: {} distance: {}, len {}".format(be_matched, distance, len(be_matched)))
            if distance < min_distance:
                min_distance = distance
                min_location = i

        # when len(words) - len(sentence) = 0
        # it also means var "words" don't have too much words
        # it means the paragraph not too long, only have one sentence
        if min_distance == 999999999:
            print("\n[sliding_matching] : sliding_matching ALG not Active")
            print("[sliding_matching] : ERROR : words    : ", "".join(words))
            print("[sliding_matching] : ERROR : sentence : ", sentence)
            print("[sliding_matching] : ERROR SOlVED : Skip Sentence.")
            return [], False

        # when sentence == "  "
        # I don't know why, maybe GPT's reply include some empty value ?
        if len(sentence) == 0:
            print("\n[sliding_matching] : ERROR : sentence empty")
            if len(time_map) >= 1:
                time_map.append((time_map[-1][1] + 0.0001, time_map[-1][1] + 0.0002))
                print("[sliding_matching] : ERROR SOlVED : Delta Shift")
                continue
            else:
                print("[sliding_matching] : ERROR SOlVED : Skip Sentence")
                return [], False
                # why we give up all the data (time_map)
                # because if len(time_map) < 1 means there no data

        else:
            location += len(sentence)
            print("\nsentence: ", sentence)
            print(
                "Matched : ",
                "".join(words[min_location : min_location + len(sentence)]),
            )

            # if len(words_map) > min_location or len(words_map) > (min_location + len(sentence)-1):
            if (
                words_data[words_map[min_location]]["end"]
                - words_data[words_map[min_location]]["start"]
                > 2
            ):
                start_time = words_data[words_map[min_location]]["end"] - 1.2
            else:
                start_time = words_data[words_map[min_location]]["start"]
            time_map.append(
                (
                    start_time,
                    words_data[words_map[min_location + len(sentence) - 1]]["end"],
                )
            )

    return time_map, True


class SubStampToSubtitleTranslation:
    """
    Task Transfer subtitle timestamp to subtitle

    TaskInfo:{
        Task_Type = "toSubtitleTranslation"
        Task_Name = "SubStampToSubtitleTranslation_{file_name}"
        Task_Progress =  23 FLOAT
        Task_Language = "English"
    }

    TaskData:{
        "paragraph_index" = 0 INT,  # 当前段落索引 来自字幕时间戳文件
        "paragraph": "xxx" STR,     # 当前段落文本 来自字幕时间戳文件
        # 以上两个变量是在 以 段落为单位颗粒度的保存

        "sentence": [] LIST,        # 由GPT进行分段的句子（翻译版本）
        "word_timestamp": [] LIST,  # 当前段落的单词时间戳 来自字幕时间戳文件
        "subtitle_match": [] LIST,   # 完成时间定位的字幕与其时间戳
        # 以上三个变量是在 以句子为单位颗粒度的保存
        # sentences 和 word_timestamp 是一一对应的, 匹配之后将会被逐步弹出移除
        # subtitle_match 是匹配之后的结果, 会被逐步添加，直到 sentence 和 word_timestamp 为空

        # 当subtitle_match 完成后，将会被写入到 subtitle_srt 中
    }
    """

    def __init__(
        self,
        cfg: DockerConfig,
        gpt: GPTApi,
        wis: WisperApi,
        memo: Memo,
        subwriter: SubtitleWriter,
        timestamp_file: object,
        language: str,
    ):
        self.cfg = cfg
        self.gpt = gpt
        self.wis = wis
        self.memo = memo
        self.subwriter = subwriter
        self.timestamp_file = timestamp_file
        self.timestamp = None
        self.language = language

        self.load_timestamp()

    def load_timestamp(self):
        with open(self.timestamp_file(), "r") as f:
            self.timestamp = json.load(f)

    def init_task(self):
        self.memo.update("TaskInfo", "Task_Type", "toSubtitleTranslation")
        self.memo.update("TaskInfo", "Task_File", self.timestamp_file())
        self.memo.update(
            "TaskInfo",
            "Task_Name",
            "SubStampToSubtitleTranslation_{}".format(
                self.memo("TaskInfo", "Task_File")
            ),
        )
        self.memo.update(
            "TaskInfo",
            "Task_Date",
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        )
        self.memo.update("TaskInfo", "Task_Progress", 0)
        self.memo.update("TaskInfo", "Task_Language", self.language)
        self.memo.update("TaskData", "paragraph_index", 0)
        self.memo.update("TaskData", "paragraph", "")
        self.memo.update("TaskData", "sentences", [])
        self.memo.update("TaskData", "match_anchor", [])
        self.memo.update("TaskData", "word_timestamp", [])
        self.memo.update("TaskData", "subtitle_match", [])
        self.memo.update("TaskData", "subtitle_srt", "", save=True)
        print("[SubStampToSubtitleTranslation] : Task Init.")

    def continue_task(self):
        print("[SubStampToSubtitleTranslation] : Continue Task")

    def update_progress(self):
        self.memo.update(
            "TaskInfo",
            "Task_Progress",
            self.memo("TaskData", "paragraph_index") / len(self.timestamp) * 100,
            save=True,
        )
        print(
            "[SubStampToSubtitleTranslation] : Progress : {}%".format(
                str(self.memo("TaskInfo", "Task_Progress"))
            )
        )

    def run(self):
        while True:
            paragraph_index = self.memo("TaskData", "paragraph_index")
            if paragraph_index == len(self.timestamp):
                break

            print(
                "[SubStampToSubtitleTranslation] : Processing Paragraph : {}".format(
                    paragraph_index
                )
            )

            if self.memo("TaskData", "paragraph") == "":
                self.memo.update(
                    "TaskData",
                    "paragraph",
                    self.timestamp[paragraph_index]["text"],
                    True,
                )

            if self.memo("TaskData", "word_timestamp") == []:
                self.memo.update(
                    "TaskData",
                    "word_timestamp",
                    self.timestamp[paragraph_index]["word"],
                    True,
                )

            if self.memo("TaskData", "sentences") == []:
                sentence, match_anchor = gpt_split_sentence_translation(
                    self.gpt, self.memo("TaskData", "paragraph"), self.language
                )
                self.memo.update("TaskData", "sentences", sentence)
                self.memo.update("TaskData", "match_anchor", match_anchor, True)

            # new alg to match sentence
            # ------------- NEW ALG ----------------
            if self.memo("TaskData", "sentences") == []:
                break

            sentence = self.memo("TaskData", "sentences")
            match_anchor = self.memo("TaskData", "match_anchor")

            word_list = self.memo("TaskData", "word_timestamp")
            time_map, status = sliding_matching(word_list, match_anchor)

            if status:
                # sliding_matching will return false if no match
                # if success, then do the following

                sentence, time_map = subtitle_proportional_merge(sentence, time_map)

                for i in range(len(sentence)):
                    start_time = time_map[i][0]
                    end_time = time_map[i][1]

                    # 将以下三个操作 合并为一个操作 原子性操作
                    self.memo.obj_update("TaskData", "subtitle_match").append(
                        {"text": sentence[i], "start": start_time, "end": end_time}
                    )
            else:
                print(
                    "[SubStampToSubtitleTranslation] : ERROR HANDLING : Skip Sentence."
                )
                print(
                    "[SubStampToSubtitleTranslation] : DEBUG PARAGRAPH : ",
                    str(self.memo("TaskData", "paragraph")),
                )

            self.memo.update("TaskData", "paragraph_index", paragraph_index + 1)
            self.memo.update("TaskData", "paragraph", "")
            self.memo.update("TaskData", "sentences", [])
            self.memo.update("TaskData", "match_anchor", [])
            self.memo.update("TaskData", "word_timestamp", [])
            self.update_progress()

        self.save()
        self.memo.clean()

    def save(self):
        self.subwriter.open()
        index = 1
        for i in self.memo("TaskData", "subtitle_match"):
            self.subwriter.write_subtitle_timestamp(
                index, i["start"], i["end"], [i["text"]]
            )
            index += 1
        self.subwriter.close()
