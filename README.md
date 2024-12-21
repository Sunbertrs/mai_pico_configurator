# mai_pico_configurator

This is a visualize configurator for [mai_pico](https://github.com/whowechina/mai_pico), writing in Python Tkinter framework.

## Screenshots

## To-do

- Rewrite some logic on displaying sensor canvas.

- Full support for non Windows platforms.

- Add more functions.

Welcome suggestions for new features, bug report ~or pull requests~.

The project is still in developing now, and haven't been release yet. Stay tuned!

## Introduction

The project provides a GUI for the project [mai_pico](https://github.com/whowechina/mai_pico), to help you adjust the settings with only a few clicks.

Run command `py main.py` **in this project directory** to start this program, and click `Connect` button to connect to your device and use.

For the first time use, you need to ensure that Python which version is larger than 3.8 was installed, and run `pip install -r requirements.txt` in this project directory.

### Features

- Detect and show in a larger interface automatically if you are using dual screens and/or your screen is displaying in portrait. You can disable this feature in `config.yaml`.

- Automatically get the COM port information and apply config if you don't config it properly. It works on Windows and implements with Powershell. Can also be disabled in `config.yaml`.

- Real-time displaying of its sensor raw readings, sensitivity adjustment, and sensor touching.

### Sensitivity adjust

Click the "Sensitivity adjust" button, type the area you want to adjust, and adjust it using arrow `←` or `→`. Then apply the changes with a Enter.

You can turn back to the main screen by pressing Esc.

### LED brightness

Click the "LED brightness" button, and on the popped up window, slide the slider to adjust the brightness level.

Click the "Apply" button to make the changes take effect. The "OK" button can also make the changes take effect, and close the window.

### Button adjust

t.b.c.

### Aime

Click the "Aime" button, and use arrow `↑` and `↓` to navigate to the target option.

Use arrow `←` or `→` to adjust the target value, finally apply the settings by pressing Enter.

### HID mode

Click the "HID mode" button, and change the target mode using arrow `↑` and `↓`. Press Enter to apply.

### Update

Simply click the "Update firmware" button to update firmware. The program will exit.

## License

This project is licensed under a GPL v3 license.