import random
from time import sleep
from subprocess import check_output, run
TB_MAIN = ['com.taobao.taobao', 'com.taobao.tao.TBMainActivity']
TB_BROWSER = ['com.taobao.taobao', 'com.taobao.browser.BrowserActivity']


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


def current_activity():

    line = check_output(
        ["adb", "shell", "dumpsys window | grep mCurrentFocus"])
    line = line.decode()
    componts = line.split()
    return componts[-1][:-1].split('/')


def start_activity(package, activity=None):
    if activity is None and isinstance(package, (list, tuple)) and len(package) > 1:
        activity = package[1]
        package = package[0]
    print("start:", package, activity)
    run(["adb", "shell", f"am start -n {package}/{activity}"])


def adbtap(x, y, use_offset=10):
    if use_offset:
        x, y = pos_withoffset(x, y, use_offset)
    run(['adb', 'shell', 'input', 'tap', str(x), str(y)])


def back():
    run(['adb', 'shell', 'input', 'keyevent', '4'])


def screenshot(save_to="/sdcard/screenshot.png", pull="screenshot"):
    run(['adb', 'shell', f'screenshot -p >{save_to}'])
    if pull:
        run(['adb', 'pull', save_to, f'./{pull}.png'])


def dump_window(save_to="/sdcard/window_dump.xml", pull="window_dump.xml"):
    run(['adb', 'shell', f'uiautomator dump {save_to}'])
    if pull:
        run(['adb', 'pull', save_to, f'{pull}'])


if __name__ == '__main__':
    print(current_activity())
    dump_window()
    wait_time(10)
