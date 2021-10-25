import random
from time import sleep
from subprocess import check_output, run
from typing import List, Optional, Union
from enum import Enum


class Activity(Enum):
    # 首页
    TB_MAIN = ['com.taobao.taobao', 'com.taobao.tao.TBMainActivity']
    # 喵糖界面
    TB_BROWSER = ['com.taobao.taobao', 'com.taobao.browser.BrowserActivity']
    TB_STORE = ['com.taobao.taobao',
                'com.alibaba.triver.container.TriverMainActivity']
    TB_LIVE = ['com.taobao.taobao',
               'com.taobao.taolive.room.TaoLiveVideoActivity']
    TB_EXBROWSER = ['com.taobao.taobao',
                    'com.taobao.browser.exbrowser.BrowserUpperActivity']


def pos_withoffset(x, y, max_off=5):
    return int(x)+random.randint(0, max_off), int(y)+random.randint(0, max_off)


def wait_time(sec=15, random_add=5, ch='*'):
    if sec == 0:
        return
    sec += random.randrange(random_add//2, random_add)
    print(f"{sec}s : ", end='')
    print('['+'-'*sec+']\b'+'\b'*sec, end='')
    for i in range(sec):
        sleep(1)
        print(ch, end='', flush=True)
    print()


ADB_PREFIX = ["adb", "shell"]


class Device:
    serial: str
    shell_prefix: list
    temp_idx: int

    def __init__(self, serial=None, temp_idx=1) -> None:
        self.serial = serial
        self.prefix = ['adb']
        self.temp_idx = temp_idx
        self.set_serial(serial)

    def set_serial(self, serial):
        if serial:
            self.prefix += ['-s', serial]
        self.shell_prefix = self.prefix+["shell"]

    def shell(self, *cmd) -> str:
        cmd_ = self.shell_prefix+list(cmd)
        out = check_output(cmd_)
        return out.decode()

    def adb(self, *cmd) -> str:
        cmd_ = self.prefix + list(cmd)
        out = check_output(cmd_)
        return out.decode()

    def pull(self, device_src, host_dest):
        return self.adb('pull', device_src, host_dest)

    def current_activity(self):

        line = self.shell("dumpsys window | grep mCurrentFocus")
        componts = line.split()
        return componts[-1][:-1].split('/')

    def start_activity(self, package: Union[str, list,  tuple], activity: str = None):
        if activity is None and isinstance(package, (list, tuple)) and len(package) > 1:
            activity = package[1]
            package = package[0]
        print("start:", package, activity)
        self.shell(f"am start -n {package}/{activity}")

    def tap(self, x: int, y: int, use_offset=10):
        if use_offset:
            x, y = self.pos_withoffset(x, y, use_offset)
        self.shell(f'input tap {x} {y}')

    def back(self):
        self.shell('input keyevent 4')

    def screenshot(self, device_path="/sdcard/screenshot.png", host_path="screenshot", rm=True):
        self.shell(f'screenshot -p >{device_path}')
        if host_path:
            self.pull(device_path, f'./{host_path}.png')
        if rm:
            self.shell(f"rm -f {device_path}")

    def dump_window(self, device_path="/sdcard/window_dump.xml", host_path="window_dump.xml", rm=True):
        self.shell(f'uiautomator dump {device_path}')
        if host_path:
            self.pull(device_path, host_path)
        if rm:
            self.shell(f"rm -f {device_path}")

    def batter_temp(self, idx=None):
        if idx is None:
            idx = self.temp_idx
        output = self.shell(f'cat /sys/class/thermal/thermal_zone{idx}/temp')
        output = output.strip()
        return int(output)/1000

    def __repr__(self) -> str:
        return f'<ADB({self.serial}) idx:{self.temp_idx}>'


device = Device()


def shell(*cmd) -> str:
    cmd_ = device.shell_prefix+list(cmd)
    out = check_output(cmd_)
    return out.decode()


def adb(*cmd) -> str:
    cmd_ = device.prefix + list(cmd)
    out = check_output(cmd_)
    return out.decode()


def pull(device_src, host_dest):
    return device.adb('pull', device_src, host_dest)


def current_activity():

    line = device.shell("dumpsys window | grep mCurrentFocus")
    componts = line.split()
    return componts[-1][:-1].split('/')


def start_activity(package: Union[str, list,  tuple], activity: str = None):
    if activity is None and isinstance(package, (list, tuple)) and len(package) > 1:
        activity = package[1]
        package = package[0]
    print("start:", package, activity)
    device.shell(f"am start -n {package}/{activity}")


def tap(x: int, y: int, use_offset=10):
    if use_offset:
        x, y = device.pos_withoffset(x, y, use_offset)
    device.shell(f'input tap {x} {y}')


def back():
    device.shell('input keyevent 4')


def screenshot(device_path="/sdcard/screenshot.png", host_path="screenshot", rm=True):
    device.shell(f'screenshot -p >{device_path}')
    if host_path:
        device.pull(device_path, f'./{host_path}.png')
    if rm:
        device.shell(f"rm -f {device_path}")


def dump_window(device_path="/sdcard/window_dump.xml", host_path="window_dump.xml", rm=True):
    device.shell(f'uiautomator dump {device_path}')
    if host_path:
        device.pull(device_path, host_path)
    if rm:
        device.shell(f"rm -f {device_path}")


def batter_temp(path='/sys/class/thermal/thermal_zone1/temp') -> float:
    output = device.shell(f'cat {path}')
    output = output.strip()
    temp_val = float(output)
    if temp_val > 1000:
        temp_val /= 1000
    return temp_val


def list_devices() -> List[Device]:
    dev_lines = device.adb("devices").splitlines()[1:]
    return [Device(line.split()[0]) for line in dev_lines if line.strip()]


def chose_device() -> Device:
    devs = list_devices()
    cur_device = None
    if len(devs) == 0:
        print("设备未连接！")
        cur_device = None
    elif len(devs) > 1:
        while cur_device is None:
            print("存在多个设备:")
            for i, dev in enumerate(devs, start=1):
                print(i, dev.serial)

            idx = input("请输入序号:")
            try:
                idx = int(idx)
            except ValueError:
                print("输入错误！", idx)
                continue
            if idx > 0 and idx <= len(devs):
                print("选择设备：", idx, devs[idx-1])
                cur_device = devs[idx-1]
            else:
                print("超出范围！", idx)
    else:
        cur_device = devs[0]
    return cur_device


if __name__ == '__main__':
    devices = list_devices()
    for dev in devices:
        print(dev)
        print(dev.current_activity())
        print(dev.batter_temp())
    print(devices[0].serial)
    dev = chose_device()
    print(dev)
    uname = dev.shell("hostname")
    print(uname)
