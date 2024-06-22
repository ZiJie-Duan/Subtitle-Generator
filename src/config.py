import os
from typing import Any
import configparser

class Config:

    def __init__(self, path='config.ini'):
        self.config = configparser.ConfigParser()
        self.path = path
        #self.read(path)

    def __call__(self, section_key) -> Any:
        return self.get_value(section_key)

    def read(self, path):
        # 读取配置文件
        # 判断文件是否存在
        if not os.path.exists(path):
            raise FileNotFoundError(f'文件不存在: {path}')
        self.config.read(path, encoding='utf-8')

    def get_value(self, config_string: str) -> Any:
        section, key = config_string.split('.')

        # 尝试将值转换为布尔型
        try:
            return self.config.getboolean(section, key)
        except ValueError:
            pass

        # 尝试将值转换为整型
        try:
            res = self.config.getint(section, key)
            if '.' in self.config.get(section, key):
                return self.config.getfloat(section, key)
            else:
                return res
        except ValueError:
            pass

        # 尝试将值转换为浮点型
        try:
            return self.config.getfloat(section, key)
        except ValueError:
            pass

        # 如果以上尝试都失败，则返回字符串值
        return self.config.get(section, key)
    
    def set(self, section, key, value: Any):
        if not self.config.has_section(section):
            self.config.add_section(section)
        
        # 将值转换为字符串
        value_str = str(value)
        
        self.config.set(section, key, value_str)
        self.save()

    def save(self):
        with open(self.path, 'w') as configfile:
            self.config.write(configfile)


class DockerConfig(Config):

    def __init__(self, path='config.ini'):
        super().__init__(path)
        self.local_config_exist = True
        self.read(path)
    
    def __call__(self, section) -> Any:

        # 判断环境变量中是否存在该字段
        # 如果存在，则直接返回
        result = os.getenv(section)
        if result:
            return result

        # 当本地配置文件存在时，将section_key转换为适配本地配置文件的格式
        # 如果section_key中没有包含'.'，则将第一个'_'替换为'.'
        # 剩下的部分全部转换为小写
        # 此代码用于适配基础的 .ini 配置文件
        # 而全大写下划线连接的字段 用于适配docker环境下的环境变量
        if self.local_config_exist and '.' not in section:
            sections = section.split('_')
            section_ini = sections[0] + "." +\
                '_'.join([x.lower() for x in sections[1:]])
            
            # 如果存在，则返回本地配置文件中的值
            return self.get_value(section_ini)
        
        # 如果环境变量中不存在, 且本地配置文件中也不存在，则抛出异常
        raise KeyError(f'Error: {section} not found in env or config file')
    
    def read(self, path):

        if not os.path.exists(path):
            self.local_config_exist = False
            #print(f'本地配置文件不存在: {path}')
        else:
            self.config.read(path, encoding='utf-8')
            #print(f'读取本地配置文件: {path}')

