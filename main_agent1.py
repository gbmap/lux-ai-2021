import math, sys
from typing import Dict

from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate
from utils import log

from worker_logic import units_work
from city_logic import cities_work
from hyperparams import Hyperparams, load

DIRECTIONS = Constants.DIRECTIONS
game_state = None
config = {
    'hparams': Hyperparams(),
    'use_roles': True
}

def agent(observation, configuration):
    global game_state

    ### Do not edit ###
    if observation["step"] == 0:
        game_state = Game()
        game_state._initialize(observation["updates"])
        game_state._update(observation["updates"][2:])
        game_state.id = observation.player
    else:
        game_state._update(observation["updates"])
    
    actions = []

    ### AI Code goes down here! ### 
    player = game_state.players[observation.player]
    opponent = game_state.players[(observation.player + 1) % 2]
    width, height = game_state.map.width, game_state.map.height

    resource_tiles: list[Cell] = []
    for y in range(height):
        for x in range(width):
            cell = game_state.map.get_cell(x, y)
            if cell.has_resource():
                resource_tiles.append(cell)

    new_actions = cities_work(player, opponent, game_state, configuration)
    if len(new_actions) > 0:
        actions = actions + new_actions

    new_actions = units_work(player, opponent, game_state, configuration) 
    if len(new_actions) > 0:
        actions = actions + new_actions
    
    return actions

def read_input():
    """
    Reads input from stdin
    """
    try:
        return input()
    except EOFError as eof:
        raise SystemExit(eof)
step = 0
class Observation(Dict[str, any]):
    def __init__(self, player=0): 
        self.player = player
        # self.updates = []
        # self.step = 0
observation = Observation()
observation["updates"] = []
observation["step"] = 0
player_id = 0
while True:
    inputs = read_input()
    observation["updates"].append(inputs)
    
    if step == 0:
        player_id = int(observation["updates"][0])
        observation.player = player_id
    if inputs == "D_DONE":
        actions = agent(observation, config)
        observation["updates"] = []
        step += 1
        observation["step"] = step
        print(",".join(actions))
        print("D_FINISH")
