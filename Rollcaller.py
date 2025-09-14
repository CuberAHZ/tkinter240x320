import tkinter as tk
import time
import random
import threading
try:
    from pinpong.board import Board
    from pinpong.libs.dfrobot_speech_synthesis import DFRobot_SpeechSynthesis_I2C
    Board().begin()
    speak = DFRobot_SpeechSynthesis_I2C()
    speak.begin(speak.V2)
except:
    speak = None


class RandomRollCall:
    def __init__(self, root):
        self.root = root
        self.root.title("随机点名器")
        self.root.geometry("240x320")
        self.root.resizable(False, False)

        self.max_num = 44
        self.current_num = 1

        self.create_widgets()

        self.root.bind('a', self.increase_max_num)
        self.root.bind('b', self.decrease_max_num)
        self.root.focus_set()

    def create_widgets(self):
        """创建界面组件"""
        title_label = tk.Label(self.root, text="随机点名器", font=("Arial", 16, "bold"))
        title_label.pack(pady=5)

        self.range_label = tk.Label(self.root, text=f"学号范围: 1-{self.max_num}",
                                   font=("Arial", 10))
        self.range_label.pack(pady=5)

        self.number_label = tk.Label(self.root, text=str(self.current_num),
                                    font=("Arial", 48, "bold"), fg="blue")
        self.number_label.pack(pady=15)

        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10)

        increase_btn = tk.Button(control_frame, text="+1",
                                command=self.increase_number,
                                width=5, height=2, bg="lightblue")
        increase_btn.grid(row=0, column=0, padx=5)

        decrease_btn = tk.Button(control_frame, text="-1",
                                command=self.decrease_number,
                                width=5, height=2, bg="lightcoral")
        decrease_btn.grid(row=0, column=1, padx=5)

        random_btn = tk.Button(self.root, text="随机点名",
                              command=self.random_select,
                              bg="lightgreen", font=("Arial", 14), height=2)
        random_btn.pack(pady=15, fill=tk.X, padx=20)

        hint_label = tk.Label(self.root, text="按A键增加范围\n按B键减少范围",
                             font=("Arial", 9), fg="gray")
        hint_label.pack(pady=5)

    def increase_number(self):
        """增加当前学号"""
        if self.current_num < self.max_num:
            self.current_num += 1
            self.number_label.config(text=str(self.current_num))

    def decrease_number(self):
        """减少当前学号"""
        if self.current_num > 1:
            self.current_num -= 1
            self.number_label.config(text=str(self.current_num))

    def increase_max_num(self, event=None):
        """增加最大学号范围"""
        self.max_num += 1
        self.range_label.config(text=f"学号范围: 1-{self.max_num}")

    def decrease_max_num(self, event=None):
        """减少最大学号范围"""
        if self.max_num > 1:
            self.max_num -= 1
            # 如果当前学号大于新的最大值，调整为最大值
            if self.current_num > self.max_num:
                self.current_num = self.max_num
                self.number_label.config(text=str(self.current_num))
            self.range_label.config(text=f"学号范围: 1-{self.max_num}")

    def random_select(self):
        """生成随机学号"""
        random_num = random.randint(1, self.max_num)
        self.current_num = random_num
        self.number_label.config(text=str(self.current_num))
        speak_thread = threading.Thread(target=self.speak_text, args=(f"{random_num}号",))
        speak_thread.start()

    def speak_text(self, text):
        """使用语音合成器朗读文本"""
        if speak:
            speak.speak(text)
        else:
            time.sleep(0.5)


if __name__ == "__main__":
    root = tk.Tk()
    app = RandomRollCall(root)
    root.mainloop()
