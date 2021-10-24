
class Point:
    def __init__(self, content_str="", x=0, y=0) -> None:
        self.x = x
        self.y = y
        if content_str:
            points = content_str.split(',')
            self.x = int(points[0])
            self.y = int(points[1])

    @property
    def xy(self):
        return self.x, self.y

    def __add__(self, other):
        if isinstance(other, str):
            other = Point(other)
        if isinstance(other, Point):
            result = Point(x=self.x+other.x, y=self.y+other.y)
            return result
        else:
            raise TypeError(f"Cannot add with {other},type:{type(other)} ")

    def __radd__(self, other):
        return self+other

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            result = Point(x=self.x/2, y=self.y/2)
            return result
        else:
            raise TypeError(f"Cannot div with {other},type:{type(other)} ")

    def __floordiv__(self, other):
        if isinstance(other, int):
            result = Point(x=self.x//2, y=self.y//2)
            return result
        else:
            raise TypeError(f"Cannot div with {other},type:{type(other)} ")

    def __str__(self) -> str:
        return f"<{self.x},{self.y}>"

    def __repr__(self) -> str:
        return f"{self.x},{self.y}"

    @property
    def adbtext(self) -> str:
        return f"{self.x} {self.y}"
