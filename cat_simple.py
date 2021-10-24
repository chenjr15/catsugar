import os
import random
from sys import maxsize
from time import sleep, time
去浏览位置 = (900, 1000)
赚喵糖领红包 = (950, 1728)


def pos(x, y, max_off=5):
    return int(x)+random.randint(0, max_off), int(y)+random.randint(0, max_off)


def wait_time(sec=15, random_add=5):
    sleep(sec)
    sleep(random.randrange(random_add//2, random_add))


def click(x, y, use_offset=10):
    if use_offset:
        x, y = pos(x, y, use_offset)
    os.system(f'adb shell input tap {x} {y}')


def back():
    os.system(f'adb shell input keyevent 4')


def screenshot(save_to="/sdcard/screenshot.png", pull="screenshot"):
    os.system(f'adb shell screenshot -p >{save_to}')
    if pull:
        os.system(f'adb pull {save_to} ./{pull}.png')


def visit_back():
    print("去浏览")
    click(*去浏览位置)
    wait_time(50)
    print("返回")
    back()


def main():
    i = 0
    # click(*赚喵糖领红包)
    wait_time(4)
    try:
        while True:
            i += 1
            print(i)
            visit_back()
            wait_time(10)
    except KeyboardInterrupt:
        print("KeyboardInterrupt", i)
        return


if __name__ == '__main__':
    main()
