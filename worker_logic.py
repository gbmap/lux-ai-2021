from typing import Dict
from lux.game_map import Position

from harvest_logic import get_harvest_pos
import numpy as np

actions = [
    'HARVEST',
    'SABOTAGE',
    'BUILD'
]

def worker_act(worker, player, game_state):
    target_pos = get_harvest_pos(worker, player, game_state)
    return worker.move(worker.pos.direction_to(target_pos))