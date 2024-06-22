
import vlc


class VlcPlayer:
    '''
        args:设置 options
    '''
    def __init__(self, *args):
        if args:
            instance = vlc.Instance(*args)
            self.media = instance.media_player_new()
        else:
            self.media = vlc.MediaPlayer()

    # 设置待播放的url地址或本地文件路径，每次调用都会重新加载资源
    def set_uri(self, uri):
        self.media.set_mrl(uri)

    # 播放 成功返回0，失败返回-1
    def play(self, path=None):
        if path:
            self.set_uri(path)
            return self.media.play()
        else:
            return self.media.play()

    # 暂停
    def pause(self):
        self.media.pause()

    # 恢复
    def resume(self):
        self.media.set_pause(0)

    # 停止
    def stop(self):
        self.media.stop()

    # 释放资源
    def release(self):
        return self.media.release()

    # 是否正在播放
    def is_playing(self):
        return self.media.is_playing()

    # 已播放时间，返回毫秒值
    def get_time(self):
        return self.media.get_time()

    # 拖动指定的毫秒值处播放。成功返回0，失败返回-1 (需要注意，只有当前多媒体格式或流媒体协议支持才会生效)
    def set_time(self, ms):
        return self.media.set_time(ms)

    # 音视频总长度，返回毫秒值
    def get_length(self):
        return self.media.get_length()

    # 获取当前音量（0~100）
    def get_volume(self):
        return self.media.audio_get_volume()

    # 设置音量（0~100）
    def set_volume(self, volume):
        return self.media.audio_set_volume(volume)

    # 返回当前状态：正在播放；暂停中；其他
    def get_state(self):
        state = self.media.get_state()
        if state == vlc.State.Playing:
            return 1
        elif state == vlc.State.Paused:
            return 0
        else:
            return -1

    # 当前播放进度情况。返回0.0~1.0之间的浮点数
    def get_position(self):
        return self.media.get_position()

    # 拖动当前进度，传入0.0~1.0之间的浮点数(需要注意，只有当前多媒体格式或流媒体协议支持才会生效)
    def set_position(self, float_val):
        return self.media.set_position(float_val)

    # 获取当前文件播放速率
    def get_rate(self):
        return self.media.get_rate()

    # 设置播放速率（如：1.2，表示加速1.2倍播放）
    def set_rate(self, rate):
        return self.media.set_rate(rate)

    # 设置宽高比率（如"16:9","4:3"）
    def set_ratio(self, ratio):
        self.media.video_set_scale(0)  # 必须设置为0，否则无法修改屏幕宽高
        self.media.video_set_aspect_ratio(ratio)

    # 注册监听器
    def add_callback(self, event_type, callback):
        self.media.event_manager().event_attach(event_type, callback)

    # 移除监听器
    def remove_callback(self, event_type, callback):
        self.media.event_manager().event_detach(event_type, callback)

    def set_marquee(self):
            self.media.video_set_marquee_int(vlc.VideoMarqueeOption.Enable, 1)
            self.media.video_set_marquee_int(vlc.VideoMarqueeOption.Size, 28)
            self.media.video_set_marquee_int(vlc.VideoMarqueeOption.Color, 0xff0000)
            self.media.video_set_marquee_int(vlc.VideoMarqueeOption.Position, 13)
            self.media.video_set_marquee_int(vlc.VideoMarqueeOption.Timeout, 0)
            self.media.video_set_marquee_int(vlc.VideoMarqueeOption.Refresh, 10000)

    def update_text(self, content):
        self.media.video_set_marquee_string(vlc.VideoMarqueeOption.Text, content)


import tkinter as tk

class App(tk.Tk):
    def __init__(self, text_timeline=[]):
        super().__init__()
        self.player = VlcPlayer()
        self.title("流媒体播放器")
        
        # 定义三个Frame
        self.video_frame = tk.Frame(self)
        self.control_frame = tk.Frame(self)
        self.timeline_frame = tk.Frame(self)
        
        self.video_frame.grid(row=0, column=0, sticky='nsew')
        self.control_frame.grid(row=0, column=1, sticky='new')
        self.timeline_frame.grid(row=1, column=0, columnspan=2, sticky='ew')

        # 添加一个新的Frame用于文本轴和滚动条
        self.text_axis_frame = tk.Frame(self)
        self.text_axis_frame.grid(row=2, column=0, columnspan=2, sticky='nsew')

        self.create_video_view()
        self.create_control_view()
        self.create_timeline_view()
        self.create_text_axis(text_timeline)

        # 设置grid的配置，使得Frames可以随窗口缩放
        self.grid_columnconfigure(0, weight=20)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=20)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=2)

    def create_video_view(self):
        self._canvas = tk.Canvas(self.video_frame, bg="black")
        self._canvas.pack(fill=tk.BOTH, expand=True)
        self.player.media.set_hwnd(self._canvas.winfo_id())

    def create_control_view(self):
        tk.Button(self.control_frame, text="播放", command=lambda: self.click(0)).pack(side=tk.TOP, pady=5)
        tk.Button(self.control_frame, text="暂停", command=lambda: self.click(1)).pack(side=tk.TOP, pady=5)
        tk.Button(self.control_frame, text="停止", command=lambda: self.click(2)).pack(side=tk.TOP, pady=5)


    def create_timeline_view(self):
        self.timeline = tk.Scale(self.timeline_frame, orient=tk.HORIZONTAL, sliderlength=10, showvalue=False)
        self.timeline.bind("<ButtonRelease-1>", self.update_video_position)
        self.timeline.pack(fill=tk.X, expand=True)
        self.update_timeline()  # 更新时间轴的范围和当前值
    
    def create_text_axis(self, text_timeline):
        # 创建滚动条并绑定到Canvas
        self.scrollbar = tk.Scrollbar(self.text_axis_frame, orient=tk.HORIZONTAL)
        self.scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.text_axis = tk.Canvas(self.text_axis_frame, bg="white", xscrollcommand=self.scrollbar.set)
        self.text_axis.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.scrollbar.config(command=self.text_axis.xview)

        last_x = 10  # 起始位置
        
        for time_ratio, text_segment in text_timeline:
            # 如果文本过长，进行换行
            if len(text_segment) > 30:
                text_segment = text_segment[:30] + "\n" + text_segment[30:]

            # 绘制竖线
            self.text_axis.create_line(last_x, 0, last_x, 40, fill="gray")  # 高度根据文本长度进行调整
            text_id = self.text_axis.create_text(last_x + 10, 10, anchor=tk.W, text=text_segment, activefill="blue", width=200)
            self.text_axis.tag_bind(text_id, '<Button-1>', lambda e, t=time_ratio: self.set_video_position(t))

            # 根据文本宽度来确定下一个文本的位置
            text_bbox = self.text_axis.bbox(text_id)
            last_x = text_bbox[2] + 10
        
        # 设置Canvas的滚动区域
        self.text_axis.config(scrollregion=self.text_axis.bbox(tk.ALL))
    
    def set_video_position(self, time_ratio):
        print(time_ratio)
        total_length = self.player.get_length()
        new_position = int(total_length * time_ratio)
        print(new_position)
        print(self.player.set_time(new_position))
        self.update_timeline()  # 同时更新时间轴的位置

    def update_timeline(self):
        total_length = self.player.get_length() // 1000  # 获得视频长度 (秒)
        current_time = self.player.get_time() // 1000   # 获得当前播放时间 (秒)
        
        self.timeline.config(from_=0, to=total_length)
        self.timeline.set(current_time)
        
        self.after(1000, self.update_timeline)  # 每秒更新一次

    def update_video_position(self, event):
        # 根据时间轴的值设置视频的播放位置
        self.player.set_position(self.timeline.get() / (self.player.get_length() // 1000))


    def click(self, action):
        if action == 0:
            if self.player.get_state() == 0:
                self.player.resume()
            elif self.player.get_state() == 1:
                pass  # 播放新资源
            else:
                self.player.play(r"C:\Users\lucyc\Desktop\aaa.mp4")
                self.player.media.video_set_subtitle_file(r"C:\Users\lucyc\Desktop\sc\subt_ch.srt")
        elif action == 1:
            if self.player.get_state() == 1:
                self.player.pause()
        else:
            self.player.stop()




# ---------- TEST CODE ------------

# if "__main__" == __name__:
#     # 传入文本轴数据的例子
#     example_timeline = [
#         (0.1, "开始这是一段废话 用来测试我们的程序开始这是一段废话 用来测试我们的程序效果，我不知道这个话语在哪里会被截断开始这是一段废话 用来测开始这是一段废话 用来测试我们的程序效果，我不知道这个话语在哪里会被截断开始这是一段废话 用来测试我们的程序效果，我不知道这个话语在哪里会被截断试我们的程序效果，我不知道这个话语在哪里会被截断效"), 
#         (0.2, "第一个关键点"), 
#         (0.5, "中间部分"), 
#         (0.75, "将近尾声"), 
#         (0.9, "结束")
#     ]

#     app = App(example_timeline)
#     app.mainloop()