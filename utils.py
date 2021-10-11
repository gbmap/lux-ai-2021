
import logging
from typing import List
from lux.game_constants import GAME_CONSTANTS
from lux.game_map import Position, DIRECTIONS, GameMap, Cell
from lux.game_objects import Player, Unit

DAY_LENGTH = GAME_CONSTANTS['PARAMETERS']['DAY_LENGTH']
NIGHT_LENGTH = GAME_CONSTANTS['PARAMETERS']['NIGHT_LENGTH']
WHOLE_DAY_LENGTH = DAY_LENGTH + NIGHT_LENGTH
CITY_BUILD_COST = GAME_CONSTANTS["PARAMETERS"]["CITY_BUILD_COST"]
RESOURCE_TYPES = GAME_CONSTANTS["RESOURCE_TYPES"]
RESOURCE_TO_FUEL_RATE = GAME_CONSTANTS["PARAMETERS"]["RESOURCE_TO_FUEL_RATE"]
UNIT_TYPES = GAME_CONSTANTS["UNIT_TYPES"]

logging.basicConfig(filename='log.log',level=logging.DEBUG)

def log(msg):
    logging.info(msg)

dirs = [
    DIRECTIONS.NORTH,
    DIRECTIONS.EAST,
    DIRECTIONS.SOUTH,
    DIRECTIONS.WEST,
    DIRECTIONS.CENTER
]

adjacent_dirs = list(set(dirs) - set([DIRECTIONS.CENTER]))

def get_city_tiles(game_state, player):
    city_tiles = []
    for k, city in player.cities.items():
        for city_tile in city.citytiles:
            city_tiles.append(city_tile)

    return city_tiles

def get_citytile_fuel_per_turn(game_state, citytile):
    neighbor_city_tiles = 0
    for _dir in adjacent_dirs:
        cell_pos = citytile.pos.translate(_dir, 1)
        cell     = game_state.map.get_cell_by_pos(cell_pos)
        if cell.citytile is not None and cell.citytile.team == citytile.team:
            neighbor_city_tiles = neighbor_city_tiles + 1
    return 23 - 5*neighbor_city_tiles

def get_turns_to_night(game_state):
    return abs(min(0, (game_state.turn % 40) - 30))

def is_outside_map(map, pos):
    return (pos.x < 0 or pos.x >= map.width 
        or pos.y < 0 or pos.y >= map.height)

def normalized_distance(game_state, posA, posB):
    sz = Position(game_state.map.width, game_state.map.height)
    return posA.distance_to(posB) / (sz.x+sz.y)

def can_worker_build_on(map, worker, pos):
    cell = map.get_cell_by_pos(pos)
    worker_resource_count = (worker.cargo.wood + worker.cargo.coal + worker.cargo.uranium) 
    worker_can_build = worker_resource_count >= CITY_BUILD_COST
    return (worker.can_act() and 
            worker_can_build and 
            (not cell.has_resource()) and 
            cell.citytile is None)

def is_resource_researched(player, resource):
    if resource.type == RESOURCE_TYPES["COAL"]:
        return player.researched_coal()
    elif resource.type == RESOURCE_TYPES["URANIUM"]:
        return player.researched_uranium()
    return True

def get_unit_dict(player):
    total = len(player.units)
    unit_dict = {
        0: 0,
        1: 0
    }
    for unit in player.units:
        if unit.type not in unit_dict:
            unit_dict[unit.type] = 0
        unit_dict[unit.type] = unit_dict[unit.type] + 1
    return unit_dict

def cargo_to_fuel_amount(cargo):
    return (cargo.wood*RESOURCE_TO_FUEL_RATE["WOOD"]
           +cargo.coal*RESOURCE_TO_FUEL_RATE["COAL"]
           +cargo.coal*RESOURCE_TO_FUEL_RATE["URANIUM"])

def get_all_units(players : List[Player]) -> List[Unit]:
    units = []
    for player in players:
        units = units + player.units
    return units

def is_unit_in_cell(cell : Cell, units : List[Unit]) -> bool:
    return is_unit_in_pos(cell.pos, units)

def is_unit_in_pos(pos : Position, units : List[Unit]) -> bool:
    return any([unit.pos == pos for unit in units])

def get_units_in_pos(pos : Position, units : List[Unit]) -> Unit:
    for unit in units:
        if unit.pos == pos:
            return unit
    return None

