import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import threading
import time
import os
import platform

# ---------- 系统命令封装 ----------
def execute_action(action):
    """根据选择执行对应的系统命令"""
    sys = platform.system()
    if sys == 'Windows':
        if action == '关机':
            os.system('shutdown /s /t 0')
        elif action == '重启':
            os.system('shutdown /r /t 0')
        elif action == '睡眠':
            os.system('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')
        elif action == '休眠':
            # 需要系统启用休眠功能
            os.system('shutdown /h')
        elif action == '锁屏':
            os.system('rundll32.exe user32.dll,LockWorkStation')
    elif sys == 'Darwin':   # macOS
        if action == '关机':
            os.system('sudo shutdown -h now')
        elif action == '重启':
            os.system('sudo shutdown -r now')
        elif action == '睡眠':
            os.system('pmset sleepnow')
        elif action == '休眠':
            os.system('pmset sleepnow')  # macOS 通常只用睡眠
        elif action == '锁屏':
            os.system('pmset displaysleepnow')
    else:                   # Linux
        if action == '关机':
            os.system('shutdown -h now')
        elif action == '重启':
            os.system('shutdown -r now')
        elif action == '睡眠':
            os.system('systemctl suspend')
        elif action == '休眠':
            os.system('systemctl hibernate')
        elif action == '锁屏':
            os.system('gnome-screensaver-command -l || xdg-screensaver lock || loginctl lock-session')

# ---------- 主界面 ----------
class PowerTimerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("定时操作小工具")
        self.root.geometry("300x280")
        self.root.resizable(False, False)

        self.cancel_event = threading.Event()   # 用于取消定时
        self.timer_thread = None                # 记时线程

        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ---------- 构建界面 ----------
    def create_widgets(self):
        # 操作选择
        ttk.Label(self.root, text="选择操作：").pack(pady=(10,0))
        self.action_var = tk.StringVar(value='关机')
        actions = ['关机', '重启', '睡眠', '休眠', '锁屏']
        self.action_combo = ttk.Combobox(self.root, textvariable=self.action_var,
                                         values=actions, state='readonly', width=10)
        self.action_combo.pack()

        # 定时方式选择
        ttk.Label(self.root, text="定时方式：").pack(pady=(10,0))
        self.mode_var = tk.StringVar(value='倒计时')
        ttk.Radiobutton(self.root, text='倒计时', variable=self.mode_var,
                        value='倒计时', command=self.toggle_mode).pack()
        ttk.Radiobutton(self.root, text='指定时间', variable=self.mode_var,
                        value='指定时间', command=self.toggle_mode).pack()

        # 倒计时输入区
        self.countdown_frame = ttk.Frame(self.root)
        self.countdown_frame.pack(pady=5)
        ttk.Label(self.countdown_frame, text="时 分 秒").pack()
        time_frame = ttk.Frame(self.countdown_frame)
        time_frame.pack()
        self.h_spin = tk.Spinbox(time_frame, from_=0, to=99, width=4, justify='center')
        self.h_spin.pack(side=tk.LEFT, padx=2)
        self.m_spin = tk.Spinbox(time_frame, from_=0, to=59, width=4, justify='center')
        self.m_spin.pack(side=tk.LEFT, padx=2)
        self.s_spin = tk.Spinbox(time_frame, from_=0, to=59, width=4, justify='center')
        self.s_spin.pack(side=tk.LEFT, padx=2)

        # 指定时间输入区（初始隐藏）
        self.time_frame = ttk.Frame(self.root)
        ttk.Label(self.time_frame, text="输入时间 (HH:MM):").pack(side=tk.LEFT)
        self.time_entry = ttk.Entry(self.time_frame, width=8, justify='center')
        self.time_entry.pack(side=tk.LEFT)

        # 按钮
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)
        self.start_btn = ttk.Button(btn_frame, text="开始计时", command=self.start_timer)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.cancel_btn = ttk.Button(btn_frame, text="取消", command=self.cancel_timer,
                                     state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, padx=5)

        # 状态标签
        self.status_label = ttk.Label(self.root, text="", foreground='blue')
        self.status_label.pack(pady=5)

    def toggle_mode(self):
        """切换倒计时/指定时间输入区"""
        if self.mode_var.get() == '倒计时':
            self.time_frame.pack_forget()
            self.countdown_frame.pack(pady=5)
        else:
            self.countdown_frame.pack_forget()
            self.time_frame.pack(pady=10)

    # ---------- 开始 / 取消 ----------
    def start_timer(self):
        action = self.action_var.get()
        mode = self.mode_var.get()

        # 计算目标秒数
        if mode == '倒计时':
            try:
                h = int(self.h_spin.get())
                m = int(self.m_spin.get())
                s = int(self.s_spin.get())
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字")
                return
            total_seconds = h * 3600 + m * 60 + s
            if total_seconds <= 0:
                messagebox.showerror("错误", "请设置大于0的时间")
                return
            target_label = f"倒计时 {h:02d}:{m:02d}:{s:02d}"
        else:  # 指定时间
            time_str = self.time_entry.get().strip()
            try:
                target_h, target_m = map(int, time_str.split(':'))
                if not (0 <= target_h <= 23 and 0 <= target_m <= 59):
                    raise ValueError
            except:
                messagebox.showerror("错误", "时间格式错误，请使用 HH:MM（如 20:30）")
                return
            now = datetime.datetime.now()
            target_dt = now.replace(hour=target_h, minute=target_m, second=0, microsecond=0)
            if target_dt <= now:
                target_dt += datetime.timedelta(days=1)   # 如果时间已过，明天执行
            total_seconds = (target_dt - now).total_seconds()
            target_label = target_dt.strftime("%H:%M:%S")

        # 更新界面状态
        self.status_label.config(text=f"将在 {target_label} 执行【{action}】")
        self.start_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.action_combo.config(state=tk.DISABLED)

        # 启动后台计时线程
        self.cancel_event.clear()
        self.timer_thread = threading.Thread(target=self.countdown, args=(total_seconds, action))
        self.timer_thread.daemon = True
        self.timer_thread.start()

    def cancel_timer(self):
        """中止定时"""
        self.cancel_event.set()
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join(timeout=1)
        self.reset_ui()
        self.status_label.config(text="已取消")

    def countdown(self, seconds, action):
        """倒计时线程（每秒检查一次取消事件）"""
        remaining = int(seconds)
        while remaining > 0:
            if self.cancel_event.is_set():
                return
            self.root.after(0, self.update_status, remaining)
            time.sleep(1)
            remaining -= 1

        # 倒计时结束，执行操作
        if not self.cancel_event.is_set():
            self.root.after(0, self.execute_action, action)

    def update_status(self, remaining):
        """在主线程更新剩余时间显示"""
        h, rem = divmod(remaining, 3600)
        m, s = divmod(rem, 60)
        self.status_label.config(text=f"剩余 {h:02d}:{m:02d}:{s:02d}")

    def execute_action(self, action):
        """执行系统命令并重置界面"""
        self.status_label.config(text=f"正在执行【{action}】...")
        self.root.update()
        execute_action(action)
        self.reset_ui()

    def reset_ui(self):
        """恢复界面到可设置状态"""
        self.start_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.action_combo.config(state='readonly')
        self.status_label.config(text="")

    def on_closing(self):
        """窗口关闭时如果线程在运行，取消它"""
        self.cancel_event.set()
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join(timeout=1)
        self.root.destroy()

# ---------- 运行 ----------
if __name__ == '__main__':
    app = PowerTimerApp()
    app.root.mainloop()