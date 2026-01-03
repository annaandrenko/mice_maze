from dataclasses import dataclass

@dataclass
class Entity:
    x: int
    y: int

    def pos(self) -> tuple[int, int]:
        return (self.x, self.y)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(x={self.x}, y={self.y})"