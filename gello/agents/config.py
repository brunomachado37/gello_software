from dataclasses import dataclass
from typing import Optional

@dataclass
class Dummy:
    name: str = "none"
    bimanual: bool = False

@dataclass
class Gello(Dummy):
    name: str = "gello"
    port: Optional[str] = None

@dataclass
class Quest(Dummy):
    name: str = "quest"
    port: Optional[str] = None

@dataclass
class Spacemouse(Dummy):
    name: str = "spacemouse"

@dataclass
class LeRobot(Dummy):
    name: str = "lerobot"
    id: Optional[str] = None
    type: Optional[str] = None
    task: Optional[str] = None
