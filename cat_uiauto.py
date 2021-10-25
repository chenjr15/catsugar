
import logging
from typing import Union
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from time import sleep

try:
    from common import Activity, Device, chose_device, list_devices, wait_time
    from point import Point
except ImportError:
    from .common import Activity, Device, chose_device, list_devices, wait_time
    from .point import Point

logger = logging.getLogger("Main")

device: Device = None


def set_device(dev):
    global device
    device = dev


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
        global device
        logger.info(f"taping:{self.center}")
        device.tap(self.center.x, self.center.y)

    def full_text(self) -> str:
        """get full text from it children

        Returns:
            str: full text
        """
        full = []
        for elem in self.element.iter():
            text = elem.get('text')
            if text is not None and text.strip() != '':
                full.append(text.strip())
        return " ".join(full)

    def __str__(self) -> str:
        text = self.text+self.desc
        if text == '':
            text = self.full_text()
        return f'<{self.type}:{text} {self.center}>'

    def __repr__(self) -> str:
        return f'<{self.type}:{self.text} {self.desc} {self.center}>'


stop = False
cnt = 20


@dataclass
class Keywords:
    homepage = '双11超级喵糖'
    opentask_btn = '赚糖领红包'
    nav = '去浏览'
    task_done = ['任务已完成', '喵糖已发放', '任务已完成喵糖已发放', '喵糖已发放明天再来吧']
    task_inprogress = "浏览得奖励"


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
        global device
        device.dump_window(host_path=self.xml_filename)
        self.tree = ET.parse(self.xml_filename)
        for handler in self.handlers:
            node = handler.match(self.tree)
            if node is None:
                continue
            stophere = handler.handle(node, self)
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

    def match(self, tree: ET.ElementTree) -> MyNode:
        elem = tree.find(self.xpath)
        if elem is not None:
            print('Matched!', self.xpath)
            return MyNode(elem)
        return None

    def handle(self, node: MyNode, executor: Executor) -> bool:
        node.tap()
        print(node)
        return True

    def __str__(self) -> str:
        return self.__repr__()

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
        global device
        device.back()
        wait_time(10)
        return True


class PrefixMatch(Handler):
    def match(self, tree: ET.ElementTree) -> MyNode:
        elems = tree.findall(".//node[@index='0']")
        node: MyNode = None
        for elem in elems:
            child = elem.find("./node/node[@index='0']")
            if child is None:
                continue
            if child.get('text').startswith('浏览15'):
                node = MyNode(elem)

        return node

    def handle(self, node: MyNode, executor: Executor) -> bool:
        node.tap()
        print(node)
        return True


class InStore(Handler):

    def __init__(self, name, post_delay=5) -> None:
        super().__init__(name, "", post_delay=post_delay)

    def match(self, tree: ET.ElementTree) -> MyNode:
        cur = device.current_activity()
        elem = None
        for word in keyword_config.task_done:

            elem = tree.find(f".//node[@text='{word}']")
            if elem is not None:
                break
        if elem is not None:
            return MyNode(elem)
        in_store = False
        for act in (Activity.TB_EXBROWSER, Activity.TB_LIVE, Activity.TB_STORE):
            if cur == act.value:
                in_store = True
                return cur
        return None

    def handle(self, node: Union[MyNode, list], executor: Executor) -> bool:
        if isinstance(node, list):
            if node == Activity.TB_EXBROWSER.value:
                elem = executor.tree.find(".//node[@text='打开链接']")
                if elem is not None:
                    node = MyNode(elem)
                    print(node)
                    node.tap()
                    return True
                else:
                    print("not found")
            print("wait for task appear")
            wait_time(15)
        if isinstance(node, MyNode):
            print("task done!")
            wait_time(5)
            device.back()
        else:
            # keep going
            return False
        return True


def execute():

    executor = Executor()
    executor.add_handler(
        Handler('tb_main', f".//*[@content-desc='{keyword_config.homepage}']"))
    executor.add_handler(
        Handler('cat_home', f".//*[@text='{keyword_config.opentask_btn}']"))
    executor.add_handler(
        DoVisitHandler('tasklist', f".//*[@text='{keyword_config.nav}']/.."))
    executor.add_handler(PrefixMatch("浏览15秒", ''))
    executor.add_handler(InStore("任务进行中",))

    while not stop and cnt > 0:
        print(device)
        executor.handle_once()


if __name__ == '__main__':
    device = chose_device()

    current = device.current_activity()
    if current == Activity.TB_BROWSER.value:
        # TODO 判断有没有任何一个match
        pass
    elif current != Activity.TB_MAIN.value:
        device.start_activity(Activity.TB_MAIN)
        wait_time(20)
    execute()
