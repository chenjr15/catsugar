
from catcat import back, visit_back, pos, wait_time, click
import os
import xml.etree.ElementTree as ET
from time import sleep
from point import Point
import logging
logger = logging.getLogger("Main")


class MyNode:
    def __init__(self, element: ET.Element) -> None:
        self.element = element
        self.center = None
        self.a = None
        self.b = None
        self.type = element.get('class', "")
        self.text = element.get('text', "")
        self.desc = element.get('content-desc', "")

        if self.element is not None:
            bounds = self.element.get('bounds')
            bounds = bounds[1:-1]
            a, b = bounds.split('][')
            self.a = Point(a)
            self.b = Point(b)
            self.center = ((self.a+self.b)//2)

    def children(self, tag=None):
        return [MyNode(e) for e in self.element.iter(tag)]

    def iter_children(self, tag=None):
        return (MyNode(e) for e in self.element.iter(tag))

    def tap(self):

        logger.info(f"taping:{self.center}")
        click(self.center.x, self.center.y)

    def __str__(self) -> str:
        return f'<{self.type}:{self.text} {self.desc} {self.center}>'

    def __repr__(self) -> str:
        return f'<{self.type}:{self.text} {self.desc} {self.center}>'


stop = False
cnt = 20
while not stop and cnt > 0:
    tree = ET.parse("./window_dump.xml")
    dom = tree.getroot()
    homepage_entry = dom.find(".//*[@content-desc='双11超级喵糖']")
    if homepage_entry:
        homepage_entry = MyNode(homepage_entry)
        homepage_entry.tap()
        print(homepage_entry)
    earn_btn = dom.find(".//*[@text='赚糖领红包']")
    if earn_btn is not None:
        earn_btn = MyNode(earn_btn)
        earn_btn.tap()
        print(earn_btn)
    go_nav_btn = dom.find(".//*[@text='去浏览']/..")
    if go_nav_btn is not None:
        go_nav_btn = MyNode(go_nav_btn)

        prompt_line = go_nav_btn.children()[2].text

        print(go_nav_btn, prompt_line)
        _, nums = prompt_line.split('(')
        nums = nums[:-1]
        a, b = nums.split('/')
        print("progress", int(a)/int(b))
        if a == b:
            print("stop!")
            stop = True
            continue
        cnt -= 1
        go_nav_btn.tap()
        wait_time(30, 20)
        back()
        wait_time(10)
