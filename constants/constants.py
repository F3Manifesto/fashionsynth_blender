import bpy
import os
import sys
from dataclasses import dataclass

@dataclass
class UserInput:
    prompt: str
    main: str
    scale: int
    steps: int
    init: bool
    path: str