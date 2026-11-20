"""Feature screens.

Every feature module exposes main(instance). The tables below are the single
place that maps a button label to the function it opens, so the window no
longer needs importlib or exec.
"""

from . import aime, factory, gpio, hid, level, sense, update

# the five buttons in the action row
buttons = {
    "Sensitivity": sense.main,
    "LED brightness": level.main,
    "Aime": aime.main,
    "GPIO definition": gpio.main,
    "HID mode": hid.main,
}

# the two buttons under the device panel
system_buttons = {
    "Update firmware": update.main,
    "Factory reset": factory.main,
}
