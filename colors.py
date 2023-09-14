#!/usr/bin/env python3

from colorama import Fore, Style
import time
import random

#X = 3
#
#print("abcde")
#print("abcde")
#print("abcde")
#print("abcde")
#
#time.sleep(1)
#
#print(f"\033[{X}A")
#print("0123")
#print("0123")

MESSAGE = "longstring"
DELAY = 0.1
FLASH_STOP = 3

SCRAMBLE_COLOR = "none"

COLORS = {
    "red": {
        "dim": Fore.RED + Style.DIM,
        "bright": Fore.LIGHTRED_EX + Style.BRIGHT,
        "normal": Fore.RED + Style.NORMAL,
        },
    "green": {
        "dim": Fore.GREEN + Style.DIM,
        "bright": Fore.LIGHTGREEN_EX + Style.BRIGHT,
        "normal": Fore.GREEN + Style.NORMAL,
        },
    "yellow": {
        "dim": Fore.YELLOW + Style.DIM,
        "bright": Fore.LIGHTYELLOW_EX + Style.BRIGHT,
        "normal": Fore.YELLOW + Style.NORMAL,
        },
    "blue": {
        "dim": Fore.BLUE + Style.DIM,
        "bright": Fore.LIGHTBLUE_EX + Style.BRIGHT,
        "normal": Fore.BLUE + Style.NORMAL,
        },
    "magenta": {
        "dim": Fore.MAGENTA + Style.DIM,
        "bright": Fore.LIGHTMAGENTA_EX + Style.BRIGHT,
        "normal": Fore.MAGENTA + Style.NORMAL,
        },
    "cyan": {
        "dim": Fore.CYAN + Style.DIM,
        "bright": Fore.LIGHTCYAN_EX + Style.BRIGHT,
        "normal": Fore.CYAN + Style.NORMAL,
        },
    "standard": {
        "dim": Style.DIM,
        "bright": Style.BRIGHT,
        "normal": Style.NORMAL,
        },
    "none": {
        "dim": "",
        "bright": "",
        "normal": "",
        },
}

def bump_mask(mask, amount, direction):

    mask = [num + 1 if 0 < num < FLASH_STOP else num for num in mask]

    if amount == 0:
        return mask
    elif amount > len(mask):
        return [1 if val == 0 else val for val in mask]

    if direction == "random":
        while amount > 0:
            zeros_at = [index for index, value in enumerate(mask) if value == 0]
            if zeros_at:
                mask[random.choice(zeros_at)] = 1
            amount -= 1
        return mask

    if direction == "left":
        mask = mask[::-1]

    try:
        first_non_zero_at = min([index for index, value in enumerate(mask) if value != 0])
        if amount < first_non_zero_at:
            mask[first_non_zero_at-amount:first_non_zero_at] = [1] * amount
        else:
            mask[:first_non_zero_at] = [1] * first_non_zero_at
    except ValueError:
        mask = [0] * (len(mask) - amount) + [1] * amount

    if direction == "left":
        return mask[::-1]
    else:
        return mask

def random_char():
    return chr(random.randint(33, 126))

def color_text(color, text):
    return color + text + Style.RESET_ALL

def get_string(message, mask, text_color, scramble_color):
    """
    mask=[0, 0, 1, 0, 1, ...]"
    """
    string = ''.join([
        color_text(COLORS[scramble_color]["dim"], random_char()) if mask[i]==0 else
        color_text(COLORS[text_color]["bright"], message[i]) if 0<mask[i]<FLASH_STOP else
        color_text(COLORS[text_color]["normal"], message[i])
        for i in range(len(message))
        ])
    return string

def coalesce_random(color):
    print()
    mask = [0]*len(MESSAGE)
    for i in range(len(MESSAGE) + FLASH_STOP):
        print("\033[1A" + get_string(MESSAGE, mask, color, "none"))
        mask = bump_mask(mask, 2, "random")
        time.sleep(DELAY)

def coalesce_left(color):
    print()
    mask = [0]*len(MESSAGE)
    for i in range(len(MESSAGE) + FLASH_STOP):
        print("\033[1A" + get_string(MESSAGE, mask, color, "none"))
        mask = bump_mask(mask, 2, "left")
        time.sleep(DELAY)

def coalesce_right(color):
    print()
    mask = [0]*len(MESSAGE)
    for i in range(len(MESSAGE) + FLASH_STOP):
        print("\033[1A" + get_string(MESSAGE, mask, color, "none"))
        mask = bump_mask(mask, 2, "right")
        time.sleep(DELAY)

def print_color():
    for color in COLORS.keys():
        coalesce_right(color)
        coalesce_left(color)
        coalesce_random(color)

if __name__ == "__main__":
    print_color()
