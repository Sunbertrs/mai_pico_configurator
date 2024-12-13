import tkinter as tk

def on_key_press(event):
    # 显示按下的键
    print(f"Pressed key: {event.keysym}")

# 创建主窗口
root = tk.Tk()
root.title("Key Press Detector")

# 创建一个标签，用来显示按下的键
label = tk.Label(root, text="Press any key...")
label.pack(pady=20)

# 将键盘事件绑定到窗口
root.bind('<KeyPress>', on_key_press)

# 运行主循环
root.mainloop()

