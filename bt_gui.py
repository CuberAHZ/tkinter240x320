#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess, threading, time, tkinter as tk
from tkinter import ttk, messagebox

WIN_SIZE = "240x320"
REFRESH_MS = 5000  # 5 秒刷新

def run(cmd, timeout=3):
    """运行 shell 命令并返回 stdout 列表"""
    try:
        out = subprocess.check_output(cmd, shell=True, text=True, timeout=timeout, stderr=subprocess.DEVNULL)
        return out.splitlines()
    except Exception:
        return []

def scan_devices():
    """返回 {mac: (name, rssi)}"""
    run("bluetoothctl --timeout 5 scan on")  # 后台扫描 5 秒
    lines = run("bluetoothctl devices")
    devices = {}
    for line in lines:
        if line.startswith("Device "):
            parts = line.split(maxsplit=2)
            if len(parts) >= 3:
                mac, name = parts[1], parts[2]
                rssi = run(f"bluetoothctl info {mac} | grep RSSI")
                rssi = int(rssi[0].split(":")[1]) if rssi else 0
                devices[mac] = (name, rssi)
    return devices

def paired_devices():
    """返回 {mac: name} 已配对设备"""
    lines = run("bluetoothctl paired-devices")
    return {l.split()[1]: l.split(maxsplit=2)[2] for l in lines if l.startswith("Device")}

def connect(mac):
    run(f"bluetoothctl connect {mac}")

def disconnect(mac):
    run(f"bluetoothctl disconnect {mac}")

def trust(mac):
    run(f"bluetoothctl trust {mac}")

class BTApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("蓝牙连接器")
        self.geometry(WIN_SIZE)
        self.resizable(False, False)
        self.configure(bg="#ffffff")

        # 列表
        frm = tk.Frame(self, bg="#ffffff")
        frm.pack(fill="both", expand=True, padx=5, pady=5)
        self.tree = ttk.Treeview(frm, columns=("rssi",), show="tree headings", height=9)
        self.tree.heading("#0", text="设备")
        self.tree.heading("rssi", text="信号")
        self.tree.column("#0", width=150)
        self.tree.column("rssi", width=50, anchor="center")
        scroll = ttk.Scrollbar(frm, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # 按钮
        btn_frm = tk.Frame(self, bg="#ffffff")
        btn_frm.pack(fill="x", padx=5, pady=2)
        tk.Button(btn_frm, text="连接", command=self.connect, width=5, font=("Helvetica", 9)).pack(side="left", padx=2)
        tk.Button(btn_frm, text="断开", command=self.disconnect, width=5, font=("Helvetica", 9)).pack(side="left", padx=2)

        # 状态
        self.status = tk.Label(self, text="", font=("Helvetica", 9), bg="#ffffff")
        self.status.pack(pady=1)
        self.conn_lbl = tk.Label(self, text="", font=("Helvetica", 9), bg="#ffffff")
        self.conn_lbl.pack(pady=1)

        self.after(200, self.refresh_list)
        self.after(REFRESH_MS, self.periodic_refresh)
        self.after(REFRESH_MS, self.update_connected)

    def refresh_list(self):
        self.status.config(text="扫描中...", fg="blue")
        threading.Thread(target=self._scan, daemon=True).start()

    # ---------- 扫描 + 排序 ----------
    def _scan(self):
        devices = scan_devices()  # mac -> (name, rssi)
        connected_macs = self._get_connected_macs()  # 获取所有已连接设备的 MAC 地址
        old_sel = self.tree.selection()

        # 排序：已连接→最前；其余按名称；MAC 沉底
        def sort_key(item):
            mac, (name, _) = item
            is_conn = mac in connected_macs
            is_mac = len(name) == 17 and (name.count(':') == 5 or name.count('-') == 5)
            return (not is_conn, is_mac, name.lower())

        sorted_devices = sorted(devices.items(), key=sort_key)

        # 清空后重新插入
        for item in self.tree.get_children():
            self.tree.delete(item)
        for mac, (name, rssi) in sorted_devices:
            is_conn = mac in connected_macs
            tag = "conn" if is_conn else None
            self.tree.insert("", "end", iid=mac, text=name,
                             values=(f"{rssi} dBm",), tags=(tag,))

        # 绿色加粗已连接行
        self.tree.tag_configure("conn", foreground="green", font=("Helvetica", 9, "bold"))

        # 恢复选中
        if old_sel and old_sel[0] in devices:
            self.tree.selection_set(old_sel)

        self.status.config(text=f"{len(devices)} 个设备")

    # ---------- 底部实时显示 ----------
    def update_connected(self):
        connected_macs = self._get_connected_macs()
        if connected_macs:
            names = []
            for mac in connected_macs:
                name = self.tree.item(mac, "text")
                names.append(f"{name} ({mac})")
            self.conn_lbl.config(text=f"已连接: {', '.join(names)}", fg="green")
        else:
            self.conn_lbl.config(text="未连接", fg="gray")
        self.after(REFRESH_MS, self.update_connected)

    # ---------- 工具 ----------
    def _get_connected_macs(self):
        """返回当前所有已连接的 MAC 地址列表"""
        lines = run("bluetoothctl info | grep 'Connected: yes' -B 2")
        return [line.split()[1] for line in lines if line.startswith("Device")]

    def _find_item(self, mac):
        return mac if mac in self.tree.get_children() else None

    # ---------- 连接 ----------
    def connect(self):
        mac = self.tree.selection()
        if not mac:
            messagebox.showwarning("提示", "请选择设备")
            return
        mac = mac[0]
        name = self.tree.item(mac, "text")
        self.status.config(text="正在配对 & 连接...", fg="blue")

        def do_pair():
            # 1. 配对
            ret1 = subprocess.run(["bluetoothctl", "pair", mac],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            # 2. 信任
            subprocess.run(["bluetoothctl", "trust", mac])
            # 3. 连接
            ret3 = subprocess.run(["bluetoothctl", "connect", mac])

            if ret3.returncode == 0:
                self.after(0, lambda: self.conn_lbl.config(text=f"已连接: {name}", fg="green"))
            else:
                # 捕获配对失败信息
                err = ret1.stderr or ret1.stdout
                self.after(0, lambda: messagebox.showerror("连接失败", err))

        threading.Thread(target=do_pair, daemon=True).start()

    # ---------- 可靠断开 ----------
    def disconnect(self):
        connected_macs = self._get_connected_macs()
        if not connected_macs:
            messagebox.showinfo("提示", "未发现已连接设备")
            return
        # 先正常断开
        self.status.config(text="正在断开...", fg="blue")
        for mac in connected_macs:
            subprocess.run(["bluetoothctl", "disconnect", mac])
        # 强制移除确保彻底断开
        def hard_remove():
            for mac in connected_macs:
                subprocess.run(["bluetoothctl", "remove", mac])
                subprocess.run(["systemctl", "--user", "restart", "pulseaudio"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        threading.Thread(target=hard_remove, daemon=True).start()
        self.after(500, self.conn_lbl.config(text="已断开", fg="blue"))

    def periodic_refresh(self):
        self.refresh_list()
        self.after(REFRESH_MS, self.periodic_refresh)

if __name__ == "__main__":
    BTApp().mainloop()
    