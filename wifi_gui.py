#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess, sys, threading, socket, tkinter as tk
from tkinter import ttk, messagebox

WIN_SIZE = "240x320"
REFRESH_MS = 5000          # 5 秒刷新，可改成 10000（10 秒）

# ---------- 扫描 ----------
def scan_wifi():
    system = sys.platform
    try:
        if system.startswith("win"):
            raw = subprocess.check_output("netsh wlan show profiles",
                                          shell=True, text=True, errors="ignore")
            ssids = [line.split(":", 1)[1].strip()
                     for line in raw.splitlines() if "所有用户配置文件" in line]
            return {s: 80 for s in ssids}          # 返回 dict：SSID -> 信号
        elif system.startswith("linux"):
            raw = subprocess.check_output("nmcli -t -f SSID,SIGNAL dev wifi",
                                          shell=True, text=True, errors="ignore")
            return {l.split(":")[0]: int(l.split(":")[1])
                    for l in raw.splitlines() if ":" in l and l.split(":")[0]}
        elif system == "darwin":
            raw = subprocess.check_output(
                "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -s",
                shell=True, text=True, errors="ignore")
            return {parts[0]: max(0, min(100, (int(parts[1]) + 100) * 2))
                    for parts in [l.split() for l in raw.splitlines()[1:]] if parts}
    except Exception:
        return {}

# ---------- 连接 ----------
def connect_wifi(ssid, pwd):
    try:
        if sys.platform.startswith("win"):
            profile = f'''<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>{ssid}</name>
    <SSIDConfig><SSID><name>{ssid}</name></SSID></SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>auto</connectionMode>
    <MSM><security><authEncryption>
        <authentication>WPA2PSK</authentication>
        <encryption>AES</encryption>
        <useOneX>false</useOneX>
    </authEncryption><sharedKey>
        <keyType>passPhrase</keyType>
        <protected>false</protected>
        <keyMaterial>{pwd}</keyMaterial>
    </sharedKey></security></MSM>
</WLANProfile>'''
            with open("temp_profile.xml", "w", encoding="utf-8") as f:
                f.write(profile)
            subprocess.check_call('netsh wlan add profile filename="temp_profile.xml"', shell=True)
            subprocess.check_call(f'netsh wlan connect name="{ssid}"', shell=True)
        elif sys.platform.startswith("linux"):
            subprocess.check_call(f'nmcli dev wifi connect "{ssid}" password "{pwd}"', shell=True)
        elif sys.platform == "darwin":
            subprocess.check_call(f'networksetup -setairportnetwork en0 "{ssid}" "{pwd}"', shell=True)
        return True
    except Exception:
        return False

# ---------- 获取已连接 SSID 与 IP ----------
def get_connected_info():
    system = sys.platform
    ssid = ip = ""
    try:
        if system.startswith("win"):
            raw = subprocess.check_output("netsh wlan show interfaces",
                                          shell=True, text=True, errors="ignore")
            for line in raw.splitlines():
                if "SSID" in line and "BSSID" not in line:
                    ssid = line.split(":", 1)[1].strip()
        elif system.startswith("linux"):
            raw = subprocess.check_output("nmcli -t -f NAME,DEVICE connection show --active",
                                          shell=True, text=True, errors="ignore")
            for line in raw.splitlines():
                if ":" in line:
                    ssid = line.split(":")[0]
                    break
        elif system == "darwin":
            raw = subprocess.check_output(
                "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I",
                shell=True, text=True, errors="ignore")
            for line in raw.splitlines():
                if " SSID" in line:
                    ssid = line.split(":", 1)[1].strip()
        # 获取本机 IPv4
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass
    return ssid, ip

# ---------- GUI ----------
class WifiGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Wi-Fi")
        self.geometry(WIN_SIZE)
        self.resizable(False, False)
        self.configure(bg="#ffffff")

        # 列表
        list_frm = tk.Frame(self, bg="#ffffff")
        list_frm.pack(fill="both", expand=True, padx=5, pady=5)
        self.tree = ttk.Treeview(list_frm, columns=("sig",), show="tree headings", height=9)
        self.tree.heading("#0", text="SSID")
        self.tree.heading("sig", text="信号")
        self.tree.column("#0", width=150)
        self.tree.column("sig", width=50, anchor="center")
        scroll = ttk.Scrollbar(list_frm, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # 底部
        bottom = tk.Frame(self, bg="#ffffff")
        bottom.pack(side="bottom", fill="x", padx=5, pady=2)
        tk.Label(bottom, text="密码:", font=("Helvetica", 9), bg="#ffffff").grid(row=0, column=0, sticky="w")
        self.pwd = tk.StringVar()
        tk.Entry(bottom, textvariable=self.pwd, show="*", width=14, font=("Helvetica", 9)).grid(row=0, column=1, padx=2)
        tk.Button(bottom, text="连接", command=self.on_connect, width=5, font=("Helvetica", 9)).grid(row=0, column=2)

        # 状态
        self.status = tk.Label(self, text="", font=("Helvetica", 9), bg="#ffffff")
        self.status.pack(pady=1)
        self.conn_lbl = tk.Label(self, text="", font=("Helvetica", 9), bg="#ffffff")
        self.conn_lbl.pack(pady=1)

        # 定时器
        self.after(200, self.refresh_list)
        self.after(REFRESH_MS, self.periodic_refresh)
        self.after(REFRESH_MS, self.update_connected)

    # ---------- 增量刷新 ----------
    def refresh_list(self):
        self.status.config(text="扫描中...", fg="blue")
        threading.Thread(target=self._scan, daemon=True).start()

    def _scan(self):
        new_data = scan_wifi()          # dict: SSID -> 信号
        old_sel = self.tree.item(self.tree.selection(), "text") if self.tree.selection() else None

        # 1. 更新或新增
        for ssid, sig in new_data.items():
            item = self._find_item(ssid)
            if item:
                self.tree.item(item, values=(f"{sig}%",))
            else:
                self.tree.insert("", "end", text=ssid, values=(f"{sig}%",))

        # 2. 删除已消失的
        for item in self.tree.get_children():
            if self.tree.item(item, "text") not in new_data:
                self.tree.delete(item)

        # 3. 恢复选中
        if old_sel and old_sel in new_data:
            item = self._find_item(old_sel)
            if item:
                self.tree.selection_set(item)

        self.status.config(text=f"{len(new_data)} 个网络")

    def _find_item(self, ssid):
        for item in self.tree.get_children():
            if self.tree.item(item, "text") == ssid:
                return item
        return None

    # ---------- 连接 ----------
    def on_connect(self):
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("提示", "请选择 Wi-Fi")
            return
        ssid = self.tree.item(item, "text")
        pwd = self.pwd.get()
        if not pwd:
            messagebox.showwarning("提示", "请输入密码")
            return
        self.status.config(text="连接中...", fg="blue")
        threading.Thread(target=self._connect, args=(ssid, pwd), daemon=True).start()

    def _connect(self, ssid, pwd):
        ok = connect_wifi(ssid, pwd)
        self.status.config(text="连接成功" if ok else "连接失败", fg="green" if ok else "red")
        self.after(500, self.update_connected)

    # ---------- 定时 ----------
    def periodic_refresh(self):
        self.refresh_list()
        self.after(REFRESH_MS, self.periodic_refresh)

    def update_connected(self):
        ssid, ip = get_connected_info()
        if ssid:
            self.conn_lbl.config(text=f"已连接: {ssid}\nIP: {ip}", fg="green")
        else:
            self.conn_lbl.config(text="未连接", fg="gray")
        self.after(REFRESH_MS, self.update_connected)


if __name__ == "__main__":
    WifiGUI().mainloop()
    