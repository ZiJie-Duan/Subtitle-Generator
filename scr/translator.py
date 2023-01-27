from MessageBox import*
from basic_tools import *
import urllib
import hashlib
import random
import requests

mp, print, orprint, printe, printse,\
printnn, printmid, print_mode_mute,\
print_mode_init = init_env()

from memo import *

@MessageBox(mp)
@MEMO()
class TRANSLATOR:
    def __init__(self):
        self.in_lang = "en"
        self.out_lang = "zh"
        self.apiurl = ""
        self.appid = ""
        self.secretyKey = ""
        self.gap = 0.2

    def translate_sentence(self,content):
        #translat function include error handle
        cont_err = 0
        while cont_err < 3:
            cont_err += 1
            new = self.translateBaidu(content)
            if new == "-233":
                printe("Translate Error")
                print("function restart")
            else:
                break
        else:
            printse("Unsolvable Translate Error")
            print("use the original sentence and attach a sign of error")
            new = "[ERROR OF TRANSLATE]"
        return new

    def translateBaidu(self, content):
        #Baidu translate api
        salt = str(random.randint(32768, 65536))
        sign = self.appid + content + salt + self.secretyKey
        sign = hashlib.md5(sign.encode('utf-8')).hexdigest()

        apiurln = self.apiurl + '?appid=' + self.appid + '&q=' + urllib.parse.quote(
            content) + '&from=' + self.in_lang + '&to=' + self.out_lang + '&salt=' + salt + '&sign=' + sign
        try:
            time.sleep(self.gap)
            res = requests.get(apiurln)
            json_res = res.json()
            dst = str(json_res['trans_result'][0]['dst'])
            return dst

        except Exception as e:
            return "-233"


# trans = TRANSLATOR()
# trans.apiurl = 'http://api.fanyi.baidu.com/api/trans/vip/translate'
# trans.appid = "" #check baidu account
# trans.secretyKey = ''