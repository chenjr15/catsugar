
import logging
from os import stat
from typing import Iterable, List, Tuple, Union
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from time import sleep
from subprocess import CalledProcessError
import json
try:
    from common import Activity, Device, chose_device, list_devices, wait_time, DummyDevice
    from point import Point
except ImportError:
    from .common import Activity, Device, chose_device, list_devices, wait_time, DummyDevice
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
        self.text = element.get('text', "").replace('\n', ' ')
        self.desc = element.get('content-desc', "").replace('\n', ' ')

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
        device.tap_rect(self.a, self.b)
        # device.tap(self.center.x, self.center.y)

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
            text = self.full_text().replace('\n', ' ')
        return f'<{self.type}:{text} {self.center}>'

    def __repr__(self) -> str:
        return f'<{self.type}:{self.text} {self.desc} {self.center}>'


stop = False
cnt = 20


# @dataclass
class Keywords:
    homepage = ('双11超级喵糖', '20亿红包', '双十一喵糖总动员互动游戏')
    opentask_btn = ('赚糖领红包',)
    nav = '去浏览'
    task_done = ('任务已完成', '喵糖已发放', '任务已完成喵糖已发放', '奖励已发放',
                 '喵糖已发放明天再来吧', '喵糖已发放\n明天再来吧', '任务已完成\n喵糖已发放')
    task_inprogress = ("浏览得奖励",)
    attrs = ('content-desc', 'text')

    def load(self, path: str = "keywords.json"):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for k, v in self.__class__.__dict__.items():
                if k .startswith('_') or callable(v):
                    continue
                # print(k, v)
                if k in data:
                    self.__dict__[k] = data[k]

    def dump(self,  path: str = "keywords.json"):
        data = {}
        for k, v in self.__class__.__dict__.items():
            if k .startswith('_') or callable(v):
                continue
            # print(k, v)
            data[k] = self.__getattribute__(k)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


KW = Keywords()


class Executor:
    def __init__(self, xml_filename="./window_dump.xml") -> None:
        self.xml_filename = xml_filename
        self.tree: ET.ElementTree = None
        self.root: ET.Element = None
        self.stop = False
        self.handlers: list['Handler'] = []

    def add_handler(self, handler: 'Handler'):
        self.handlers.append(handler)

    def handle_once(self) -> int:
        global device
        print("dumping...")
        try:
            device.dump_window(host_path=self.xml_filename)
        except CalledProcessError as e:
            print("dump 失败，跳过", e.stderr, e.stdout, e.returncode)
            wait_time(1)
            return 1
        self.tree = ET.parse(self.xml_filename)
        for handler in self.handlers:
            node = handler.match(self.tree)
            if node is None:
                continue
            print("exec:", handler)
            stophere = handler.handle(node, self)
            wait_time(handler.post_delay)
            if stophere:
                break
        return 0

    def loop(self, limit=-1, interval=30, screenshot=True):
        """自动循环

        Args:
            limit (int, optional): 最多运行次数，负数为不限制. Defaults to -1.
            interval (int, optional): 休息次数. Defaults to 30.

        Returns:
            None
        """
        cnt = 0
        failed = 0
        while not self.stop and (limit < -1 or cnt < limit):
            KW.load()
            if screenshot:
                device.screenshot()
            cnt += 1
            if limit > -1 and cnt > limit:
                print("reach limit")
                break
            if cnt % interval == 0:
                print("休息时间")
                wait_time(20)
            print(device, cnt, failed)
            status = self.handle_once()
            if status == 0:
                failed = 0
            else:
                failed += status
            wait_time(1)
            # 连续10次失败, 则尝试返回
            if failed > 2:
                print('Too many fails，return', failed)
                device.back()
                failed = 0
        device.start_activity(Activity.TB_MAIN)
        device.back()
        wait_time(1)
        device.back()
        device.back()
        print("Bye!")
        return cnt


class Handler:
    name: str
    xpath: str
    post_delay: int

    def __init__(self, name, post_delay=5) -> None:
        self.name = name
        self.post_delay = post_delay

    def match(self, tree: ET.ElementTree) -> MyNode:
        return None

    def handle(self, node: MyNode, executor: Executor) -> bool:
        return True

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f'<{self.name} {self.__class__.__qualname__}>'


class TextHandler(Handler):
    textlist: Iterable[str]
    attrs: Iterable[str]

    def __init__(self, name, text_list: Iterable[str], attrs: Iterable[str] = ['text', 'content-desc'], post_delay=5) -> None:
        super().__init__(name, post_delay)
        self.textlist = text_list
        self.attrs = attrs

    def attr_text_iter(self):
        return ((attr, text) for text in self.textlist for attr in self.attrs)

    def match(self, tree: ET.ElementTree) -> MyNode:
        for attr, text in self.attr_text_iter():

            xpath = f".//node[@{attr}='{text}']"
            elem = tree.find(xpath)
            if elem is not None:
                print('Matched!', attr, text)
                return MyNode(elem)
        return None

    def handle(self, node: MyNode, executor: Executor) -> bool:
        node.tap()
        print("tap:", node)
        return True


class PrefixMatch(Handler):
    def match(self, tree: ET.ElementTree) -> MyNode:
        elems = tree.findall(".//node[@text='']")
        node: MyNode = None
        for elem in elems:
            child = elem.find(
                "./node[@index='0']/node[@index='1']/node[@index='0']")
            if child is None:
                continue
            if not child.get('text').startswith('浏览15'):
                continue
            # 已完成就不要再继续了
            done = elem.find(".//node[@text='已完成']")

            if done is None:
                node = MyNode(elem)
                break
            else:
                print(MyNode(elem), "done")
                # node = "STOP"
                node = None
                continue
        return node

    def handle(self, node: MyNode, executor: Executor) -> bool:
        if node == "STOP":
            executor.stop = True
        else:
            node.tap()
            print(node)
        return True


class InTask(TextHandler):

    def __init__(self, name, keywords: Iterable[str] = None, attrs: Iterable[str] = None, post_delay=5) -> None:
        if keywords is None:
            keywords = KW.task_done
        if attrs is None:
            attrs = KW.attrs
        super().__init__(name, keywords, attrs=attrs, post_delay=post_delay)

    def match(self, tree: ET.ElementTree) -> MyNode:
        cur = device.current_activity()
        done_elem = None
        # 检测任务是否完成
        for attr, word in self.attr_text_iter():
            done_elem = tree.find(f".//node[@{attr}='{word}']")
            # print(attr, word, elem)
            if done_elem is not None:
                break

        if done_elem is not None:
            return MyNode(done_elem)
        in_store = False
        # 如果在这些activity中说明在执行任务
        for act in (Activity.TB_EXBROWSER, Activity.TB_LIVE, Activity.TB_STORE):
            if act == cur:
                in_store = True
                return act
        return None

    def handle(self, node: Union[MyNode, Activity], executor: Executor) -> bool:
        if isinstance(node, Activity):
            act = node
            if Activity.TB_EXBROWSER == act:
                elem = executor.tree.find(".//node[@text='打开链接']")
                if elem is not None:
                    node = MyNode(elem)
                    print(node)
                    node.tap()
                    return True
                else:
                    print("not found")
            print("wait for task appear")
            wait_time(5)
        if isinstance(node, MyNode):
            print("task done!", node)
            wait_time(1)
            device.back()
        else:
            # keep going
            return False
        return True


def execute(limit=10):

    executor = Executor()
    executor.add_handler(TextHandler('tb_main', KW.homepage))
    executor.add_handler(TextHandler('cat_home', KW.opentask_btn))
    executor.add_handler(TextHandler(
        "签到", ["每日签到领喵糖(0/1)", "签到得喵糖完成可获得1个喵糖，点击可以去完成"]))
    executor.add_handler(TextHandler(
        "主会场", ["逛逛天猫主会场(0/1)"], attrs=["text"], post_delay=10))
    # executor.add_handler(
    #     DoVisitHandler('tasklist', f".//*[@text='{keyword_config.nav}']/.."))
    executor.add_handler(PrefixMatch("15S查找"))

    executor.add_handler(InTask("任务执行页面",))

    return executor.loop(limit)


def setup():
    global device
    device = chose_device()


if __name__ == '__main__':
    setup()
    # set_device(DummyDevice())

    current = device.current_activity()
    if Activity.TB_BROWSER.package_match(current):
        # TODO 判断有没有任何一个match
        pass
    else:
        device.start_activity(Activity.TB_MAIN)
        wait_time(1)
    try:
        execute(150)
    except KeyboardInterrupt:
        print("退出")
