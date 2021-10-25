
import xml.etree.ElementTree as ET
from time import sleep
from dataclasses import dataclass

import logging
try:
    from common import *
    from point import Point
except ImportError:
    from .common import *
    from .point import Point

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
        adbtap(self.center.x, self.center.y)

    def __str__(self) -> str:
        return f'<{self.type}:{self.text} {self.desc} {self.center}>'

    def __repr__(self) -> str:
        return f'<{self.type}:{self.text} {self.desc} {self.center}>'


stop = False
cnt = 20


@dataclass
class Keywords:
    homepage = '双11超级喵糖'
    opentask_btn = '赚糖领红包'
    nav = '去浏览'


keyword_config = Keywords()


class Executor:
    def __init__(self, xml_filename="./window_dump.xml") -> None:
        self.xml_filename = xml_filename
        self.tree: ET.ElementTree = None
        self.root: ET.Element = None
        self.stop = False
        self.handlers: list['Handler'] = []

    def add_handler(self, handler: 'Handler'):
        self.handlers.append(handler)

    def handle_once(self):
        dump_window(pull=self.xml_filename)
        self.tree = ET.parse(self.xml_filename)
        self.root = self.tree.getroot()
        for handler in self.handlers:
            elem = self.root.find(handler.xpath)
            print("finding:", handler.xpath, elem)

            if elem is None:
                continue
            stophere = handler.handle(MyNode(elem), self)
            wait_time(handler.post_delay)
            if stophere:
                break


class Handler:
    name: str
    xpath: str
    post_delay: int

    def __init__(self, name, xpath, post_delay=5) -> None:
        self.name = name
        self.xpath = xpath
        self.post_delay = post_delay

    def handle(self, node: MyNode, executor: Executor):
        node.tap()
        print(node)
        return True

    def __repr__(self) -> str:
        return f'<{self.name} Handler>'


class DoVisitHandler(Handler):
    def handle(self, go_nav_btn: MyNode, executor: Executor):
        prompt_line = go_nav_btn.children()[2].text
        print(go_nav_btn, prompt_line)
        _, nums = prompt_line.split('(')
        nums = nums[:-1]
        a, b = nums.split('/')
        print("progress", int(a)/int(b))
        go_nav_btn.tap()
        wait_time(30, 20)
        back()
        wait_time(10)
        return True


def execute():

    executor = Executor()
    executor.add_handler(
        Handler('tb_main', f".//*[@content-desc='{keyword_config.homepage}']"))
    executor.add_handler(
        Handler('cat_home', f".//*[@text='{keyword_config.opentask_btn}']"))
    executor.add_handler(
        DoVisitHandler('tasklist', f".//*[@text='{keyword_config.nav}']/.."))

    while not stop and cnt > 0:
        executor.handle_once()


if __name__ == '__main__':
    current = current_activity()
    if current == TB_BROWSER:
        # TODO 判断有没有任何一个match
        pass
    elif current != TB_MAIN:
        start_activity(TB_MAIN)
        wait_time(20)
    execute()
