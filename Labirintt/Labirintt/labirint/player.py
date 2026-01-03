from entity import Entity

class Player(Entity):
    def __init__(self, x: int, y: int, name: str, coins: int = 0, hp: int = 3):
        super().__init__(x, y)          # <-- спадкування працює тут
        self.name = name
        self.coins = coins
        self._hp = hp                   # <-- під property
        self.max_hp = 3

    @property
    def hp(self) -> int:
        return self._hp

    @hp.setter
    def hp(self, value: int) -> None:
        self._hp = max(0, min(self.max_hp, value))
