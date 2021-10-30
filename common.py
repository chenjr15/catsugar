import random
from time import sleep
from subprocess import PIPE, check_output, run, CalledProcessError
from typing import List, Optional, Union
from enum import Enum

from point import Point


class Activity(Enum):
    # 首页
    TB_MAIN = 'com.taobao.taobao/com.taobao.tao.TBMainActivity'
    # 喵糖界面
    TB_BROWSER = 'com.taobao.taobao/com.taobao.browser.BrowserActivity'
    TB_STORE = 'com.taobao.taobao/com.alibaba.triver.container.TriverMainActivity'
    TB_LIVE = 'com.taobao.taobao/com.taobao.taolive.room.TaoLiveVideoActivity'
    TB_EXBROWSER = 'com.taobao.taobao/com.taobao.browser.exbrowser.BrowserUpperActivity'

    @property
    def package(self):
        return self.value.split('/')[0]

    def __eq__(self, o: object) -> bool:
        if isinstance(o, str):
            return self.value == o
        return super().__eq__(o)

    def __repr__(self) -> str:
        print(self.name, self.value)
        return super().__repr__()

    def package_match(self, intent: Union[str, 'Activity']):
        if isinstance(intent, self.__class__):
            intent = intent.value
        if isinstance(intent, str):
            return self.package == intent.split('/')[0]
        return False


def pos_withoffset(x, y, max_off=5):
    return int(x)+random.randint(0, max_off), int(y)+random.randint(0, max_off)


def wait_time(sec=15, random_add=5, ch='*'):
    if sec == 0:
        return
    print("wait:", sec)
    sec += random.randrange(random_add//2, random_add)
    # print(f"{sec}s : ", end='')
    # print('['+'-'*sec+']\b'+'\b'*sec, end='')
    print(f"{0:2}/{sec} s [{'-'*(sec)}]", end='', flush=True)
    try:
        for i in range(sec):
            sleep(1)
            print(f"\r{i:2}/{sec} s [{ch*i}{'-'*(sec-i)}]", end='', flush=True)
            # print(ch, end='', flush=True)
    except KeyboardInterrupt:
        print("\nCanceled!!\nCtrl-C again to exit")
        # 防止无法退出
        sleep(0.5)
    else:
        print(f"\r{sec}/{sec} s [{ch*(sec)}]",  flush=True)


ADB_PREFIX = ["adb", "shell"]


class Device:
    serial: str
    shell_prefix: list
    model: str

    def __init__(self, serial=None) -> None:
        self.serial = serial
        self.prefix = ['adb']
        self.set_serial(serial)

    def set_serial(self, serial):
        if serial:
            self.prefix += ['-s', serial]
        self.shell_prefix = self.prefix+["shell"]
        try:
            self.update_model()
        except:
            pass

    def update_model(self) -> str:
        self.model = self.shell("getprop ro.product.model").strip()
        return self.model

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
        return componts[-1][:-1]

    def start_activity(self, intent: str):
        # if activity is None and isinstance(package, (list, tuple)) and len(package) > 1:
        #     activity = package[1]
        #     package = package[0]
        if isinstance(intent, Activity):
            intent = intent.value
        print("start:", intent)
        self.shell(f"am start -n {intent}")

    def tap(self, x: int, y: int, use_offset=10):
        if use_offset:
            x, y = pos_withoffset(x, y, use_offset)
        print('tap:', x, y)
        self.shell(f'input tap {x} {y}')

    def tap_rect(self, a: Point, b: Point):
        diff = abs(b-a)
        lower = diff//4
        upper = lower*3
        x = min(a.x, b.x)+random.randrange(lower.x, upper.x)
        y = min(a.y, b.y)+random.randrange(lower.y, upper.y)
        self.tap(x, y, 0)

    def swipe(self, a: Point, b: Point, duration=200):
        self.shell(f"input swipe {a.x} {a.y} {b.x} {b.y} {duration}")

    def back(self):
        self.shell('input keyevent 4')

    def screenshot(self, host_path=None, device_path="/sdcard/screenshot.png", rm=True):
        """截图

        Args:
            host_path (str, optional): 保存在主机上的文件位置，传入None时是当前的serial.png . Defaults to None.
            device_path (str, optional): 设备上的文件位置. Defaults to "/sdcard/screenshot.png".
            rm (bool, optional): 是否删除设备上的文件. Defaults to True.
        """
        if host_path is None:
            host_path = f"{self.serial}.png"
        self.shell(f'screencap -p >{device_path}')
        if host_path:
            self.pull(device_path, host_path)
        if rm:
            self.shell(f"rm -f {device_path}")

    def dump_window(self, host_path="window_dump.xml", device_path="/storage/emulated/0/window_dump.xml",  rm=True):
        ret = self.shell(f'uiautomator dump {device_path}')
        print(ret)
        # ret = run(self.shell_prefix +
        #           [f'uiautomator dump {device_path}'], stdout=PIPE, stderr=PIPE)
        # print(ret, ret.stderr, ret.stdout, ret.returncode)
        if host_path:
            self.pull(device_path, host_path)
        if rm:
            self.shell(f"rm -f {device_path}")

    def batter_temp(self):
        raw = self.shell(f'dumpsys battery|grep temperature')
        raw = raw.replace('temperature:', '')
        raw = raw.strip()
        val = float(raw)
        val /= 10
        return val

    def __repr__(self) -> str:
        return f'<{self.model}({self.serial}) {self.batter_temp()}℃ >'


class DummyDevice(Device):

    def __init__(self, serial=None) -> None:
        super().__init__(serial=serial)
        self.cur_activity = ""

    def adb(self, *cmd) -> str:
        cmd_ = self.prefix+list(cmd)
        print("Dummy:", " ".join(cmd_))

        return ""

    def shell(self, *cmd) -> str:
        cmd_ = self.shell_prefix+list(cmd)
        print("Dummy:", " ".join(cmd_))
        return "0"

    def update_model(self, serial=None) -> str:
        self.model = "Dummy"
        return self.model

    def current_activity(self):
        return self.cur_activity


device = Device()


def shell(*cmd) -> str:
    return dev.shell(*cmd)


def adb(*cmd) -> str:
    return dev.adb(*cmd)


def pull(device_src, host_dest):
    return device.pull(device_src, host_dest)


def current_activity():
    return device.current_activity()


def start_activity(intent: str):
    return device.start_activity(intent)


def tap(x: int, y: int, use_offset=10):
    return device.tap(x, x, use_offset)


def back():
    device.back()


def screenshot(host_path="screenshot.png", device_path="/sdcard/screenshot.png",  rm=True):
    device.screenshot(device_path, host_path, rm)


def dump_window(host_path="window_dump.xml", device_path="/sdcard/window_dump.xml",  rm=True):
    device.dump_window(device_path, host_path, rm)


def batter_temp() -> float:
    return device.batter_temp()


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
                print(i, dev)

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

    print(repr(Activity.TB_BROWSER))
    print(Activity.TB_LIVE.package_match(Activity.TB_BROWSER))
    devices = list_devices()
    for dev in devices:
        print(dev)
        cur = dev.current_activity()
        print(cur, Activity.TB_LIVE == cur,
              Activity.TB_MAIN.package_match(cur), Activity.TB_EXBROWSER.package_match("cur"))
        print(dev.batter_temp())
        dev.screenshot()
    print(devices[0].serial)
    dev = chose_device()
    print(dev)
    dev.dump_window()

    uname = dev.shell("uname -a")
