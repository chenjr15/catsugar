from common import *

dev = chose_device()
dev.screenshot()

for i in range(9):
    dev.screenshot()
    print(i+1)
    dev.tap(895, 1396, 30)
    # dev.tap(895, 1596, 30)
    # dev.tap(895, 1796, 30)
    wait_time(30)
    dev.back()
    wait_time(1)
