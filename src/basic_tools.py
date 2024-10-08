import platform
import os
import subprocess


class FilePath:
    """
    一个文件路径管理类
    负责跨平台的处理和管理文件路径
    可以检测操作系统，拆分工作路径，文件名和 文件后缀
    可以根据工作路径快速构建 新的文件 灵活的指定后缀和名称
    """

    def __init__(self, file_path: str, build: bool = False):
        self.system = platform.system()  # 检测操作系统
        self.file_path = ""  # 文件完整路径
        self.file_name = ""  # 文件完成名称
        self.file_name_no_ext = ""  # 文件名称 无后缀
        self.file_ext = ""  # 文件后缀
        self.file_working_path = ""  # 文件工作路径

        if build:
            # build 为True时, 传入一个相对路径, 会自动转换为绝对路径
            fully_path = os.path.abspath(file_path)
            self.set_path(fully_path)
        else:
            self.set_path(file_path)

    def __call__(self, quote: bool = False):
        """返回文件完整路径"""
        if quote:
            return self.quote()
        else:
            return self.file_path

    def _path_check(self, file_path: str):
        """检查传入的文件路径 是否合法"""
        if self.system == "Windows":
            tmp_path = file_path.split("\\")
        else:
            tmp_path = file_path.split("/")
        if "." in tmp_path[-1]:
            return True
        else:
            return False

    def set_path(self, file_path: str):
        """设置文件路径并分离出文件名、文件扩展名等"""
        if self.system == "Windows":
            if self._path_check(file_path):
                self.file_path = file_path
                tmp = file_path.split("\\")
                self.file_name = tmp[-1]
                self.file_name_no_ext = "".join(self.file_name.split(".")[:-1])
                self.file_ext = self.file_name.split(".")[-1]
                tmp = tmp[:-1]
                self.file_working_path = "\\".join(tmp)
                return True
            else:
                return False
        else:
            # linux system
            if self._path_check(file_path):
                self.file_path = file_path
                tmp = file_path.split("/")
                self.file_name = tmp[-1]
                self.file_name_no_ext = "".join(self.file_name.split(".")[:-1])
                self.file_ext = self.file_name.split(".")[-1]
                tmp = tmp[:-1]
                self.file_working_path = "/".join(tmp)
                return True
            else:
                return False

    def nfile(self, name: str = "", full_name: str = "", ext: str = ""):
        """
        构建新的文件路径, 返回一个新的FilePath对象
            name: 新文件名称 不包含后缀
            full_name: 新文件名称 全名
            ext: 新文件后缀
        如果full_name不为None, 则忽略name和ext
        只有name将会改变文件名称, ext将会改变文件后缀
        """
        new_file_path = None

        if self.system == "Windows":
            # Windows实现
            if full_name:
                new_file_path = self.file_working_path + "\\" + full_name
            else:
                if name:
                    if ext:
                        new_file_path = self.file_working_path + "\\" + name + "." + ext
                    else:
                        new_file_path = (
                            self.file_working_path + "\\" + name + "." + self.file_ext
                        )
                else:
                    if ext:
                        new_file_path = (
                            self.file_working_path
                            + "\\"
                            + self.file_name_no_ext
                            + "."
                            + ext
                        )
                    else:
                        new_file_path = (
                            self.file_working_path
                            + "\\"
                            + self.file_name_no_ext
                            + "_new."
                            + self.file_ext
                        )
        else:
            if full_name:
                new_file_path = self.file_working_path + "/" + full_name
            else:
                if name:
                    if ext:
                        new_file_path = self.file_working_path + "/" + name + "." + ext
                    else:
                        new_file_path = (
                            self.file_working_path + "/" + name + "." + self.file_ext
                        )
                else:
                    if ext:
                        new_file_path = (
                            self.file_working_path
                            + "/"
                            + self.file_name_no_ext
                            + "."
                            + ext
                        )
                    else:
                        new_file_path = (
                            self.file_working_path
                            + "/"
                            + self.file_name_no_ext
                            + "_new."
                            + self.file_ext
                        )
        return FilePath(new_file_path)

    def exist(self):
        """检查文件是否存在"""
        return os.path.exists(self.file_path)

    def write(self, content: str, mode: str = "a"):
        """写入文件"""
        with open(self.file_path, mode=mode) as f:
            f.write(content)

    def delete(self):
        """删除文件"""
        os.remove(self.file_path)

    def quote(self):
        """返回带引号的文件路径"""
        return '"' + self.file_path + '"'


class SystemCmd:
    """
    一个系统命令行管理类
    """

    def __init__(self):
        self.system = platform.system()  # 检测操作系统

    def __call__(self, cmd: str = "NONE"):
        """执行命令行命令, cmd为命令"""

        if cmd == "NONE":
            pass
        else:
            self.cmd(cmd)

    def cmd(self, cmd: str):
        """执行命令行命令, cmd为命令"""

        if self.system == "Windows":
            os.system(cmd)
        else:
            pass  # 其他系统（例如MAC）

    def new_run(self, file_path: str):
        """打开文件"""

        if self.system == "Windows":
            os.startfile(file_path)

        else:
            pass  # 其他系统（例如MAC）

    def run(self, cmd: list):
        return subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        ).stdout


# ---------- TEST CODE ------------
# fp = FilePath(r"C:\Users\lucyc\Desktop\kk.jpg")
# print(fp.file_path)
# nfp = fp.nfile(ext="go")
# print(nfp.file_path)
