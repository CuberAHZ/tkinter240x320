import socket
import pyaudio
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox

__version__ = "1.1.0"

# 音频发送函数
def audio_send(receiver_ip, port, rate, channels, chunk, FORMAT=pyaudio.paInt16):
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=channels, rate=rate, input=True, frames_per_buffer=chunk * 2)
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        print("开始发送音频数据...")
        while True:
            data = stream.read(chunk)  # 从麦克风读取数据
            udp_socket.sendto(data, (receiver_ip, port))  # 发送音频数据到接收端
    except KeyboardInterrupt:
        print("停止发送音频数据...")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        udp_socket.close()

# 音频接收函数
def audio_recv(port, rate, channels, chunk, MAXSIZE=100, FORMAT=pyaudio.paInt16):
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=channels, rate=rate, output=True, frames_per_buffer=chunk * 2)
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(("0.0.0.0", port))
    audio_q = queue.Queue(maxsize=MAXSIZE)

    def udp_receiver():
        while True:
            data, _ = udp_socket.recvfrom(16384)
            try:
                audio_q.put(data, timeout=0.1)
            except queue.Full:
                pass  # 丢弃过多的数据，防止阻塞

    threading.Thread(target=udp_receiver, daemon=True).start()

    try:
        print("开始接收音频数据...")
        while True:
            try:
                data = audio_q.get(timeout=0.2)
            except queue.Empty:
                data = b'\x00' * (chunk * channels * 2)
            stream.write(data)
    except KeyboardInterrupt:
        print("停止接收音频数据...")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        udp_socket.close()

# GUI 应用程序
class AudioApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("音频传输工具")
        self.geometry("240x320")
        self.resizable(False, False)

        # 发送音频部分
        self.send_frame = ttk.LabelFrame(self, text="发送音频")
        self.send_frame.pack(pady=5, padx=5, fill="both", expand=True)

        ttk.Label(self.send_frame, text="接收端 IP:").grid(row=0, column=0, padx=2, pady=2, sticky="w")
        self.receiver_ip = ttk.Entry(self.send_frame, width=15)
        self.receiver_ip.grid(row=0, column=1, padx=2, pady=2)
        self.receiver_ip.insert(0, "127.0.0.1")

        ttk.Label(self.send_frame, text="端口:").grid(row=1, column=0, padx=2, pady=2, sticky="w")
        self.port_send = ttk.Entry(self.send_frame, width=5)
        self.port_send.grid(row=1, column=1, padx=2, pady=2)
        self.port_send.insert(0, "50007")

        self.send_button = ttk.Button(self.send_frame, text="开始发送", command=self.start_send, width=10)
        self.send_button.grid(row=2, column=0, columnspan=2, pady=5)

        # 接收音频部分
        self.recv_frame = ttk.LabelFrame(self, text="接收音频")
        self.recv_frame.pack(pady=5, padx=5, fill="both", expand=True)

        ttk.Label(self.recv_frame, text="端口:").grid(row=0, column=0, padx=2, pady=2, sticky="w")
        self.port_recv = ttk.Entry(self.recv_frame, width=5)
        self.port_recv.grid(row=0, column=1, padx=2, pady=2)
        self.port_recv.insert(0, "50007")

        self.recv_button = ttk.Button(self.recv_frame, text="开始接收", command=self.start_recv, width=10)
        self.recv_button.grid(row=1, column=0, columnspan=2, pady=5)

        self.send_thread = None
        self.recv_thread = None

    def start_send(self):
        if self.send_thread and self.send_thread.is_alive():
            messagebox.showwarning("警告", "音频发送已经在运行中！")
            return

        receiver_ip = self.receiver_ip.get()
        port = int(self.port_send.get())
        rate = 24000
        channels = 1
        chunk = 128

        self.send_thread = threading.Thread(target=audio_send, args=(receiver_ip, port, rate, channels, chunk), daemon=True)
        self.send_thread.start()
        messagebox.showinfo("提示", "音频发送已开始！")

    def start_recv(self):
        if self.recv_thread and self.recv_thread.is_alive():
            messagebox.showwarning("警告", "音频接收已经在运行中！")
            return

        port = int(self.port_recv.get())
        rate = 24000
        channels = 1
        chunk = 128

        self.recv_thread = threading.Thread(target=audio_recv, args=(port, rate, channels, chunk), daemon=True)
        self.recv_thread.start()
        messagebox.showinfo("提示", "音频接收已开始！")

if __name__ == "__main__":
    app = AudioApp()
    app.mainloop()
    