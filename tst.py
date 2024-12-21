# from tkinter import *
#
# buttons = {
#     "Sensitivity adjust": 'cmds.sense',
#     "LED brightness": 'cmds.level',
#     "Buttons adjust": 'cmds',
#     "Aime": 'cmds.aime',
#     "Test": 'cmds',
#     "HID mode": 'cmds.hid',
#     "Update firmware": 'cmds.update',
# }
# # 创建主窗口
# root = Tk()
#
# cmd_btn = []
# for i, name in enumerate(buttons.keys()):
#     cmd_btn.append(Button(root, text=name, command=lambda curr=name: print(curr, buttons[curr])))
#     cmd_btn[i].grid(row=i // 4, column=i % 4, padx=12, pady=10)
#
# # 运行主循环
# root.mainloop()

print(f'{"Play"}{"ON":>10}')
print(f'{"Abc"}{"OFF":>10}')