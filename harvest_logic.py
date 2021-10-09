
import random
import numpy as np
from lux.game_map import Position, DIRECTIONS

from utils import get_city_tiles, get_turns_to_night, log

def dist(a, b):
    ar = np.array([a.x, a.y])
    br = np.array([b.x, b.y])
    d = br - ar
    return np.sqrt(np.dot(d,d))

def normalize_dist(dist, game_state):
    w = game_state.map.width
    h = game_state.map.height
    d = Position(w, h).distance_to(Position(0,0))
    return dist / d

def rule_random_value(player, game_state, worker, pos):
    return random.randint(0, 5)

def rule_city_distance(player, game_state, worker, pos):
    #pos = worker.pos
    city_tiles = get_city_tiles(game_state, player)
    dists = [pos.distance_to(c.pos) for c in city_tiles]
    if len(dists) == 0:
        return 0.0

    # Sort city tiles by distance from cell.
    tc = zip(dists, city_tiles)
    tc = sorted(tc, key=lambda c: c[0])

    v = np.min(dists)
    turns_to_night = get_turns_to_night(game_state)

    t = 0
    if t == 0:
        # sqrt like distance form
        v = v / max(1, turns_to_night)
        return -100.0*v
        #norm_ttn = turns_to_night / 30
        #v_exp = 1.0/(2.0-norm_ttn)
        #v = pow(v, v_exp)
        return (1.0-v)
    else:
        # Forma 2
        return int(v < turns_to_night)*-10

def rule_deliver_resources(player, game_state, worker, pos):
    if worker.get_cargo_space_left() > 0:
        return 0.0

    cell = game_state.map.get_cell_by_pos(pos)
    if cell.citytile == None:
        return 0.0

    if player.team != cell.citytile.team:
        return 0.0

    return 10000.0

def rule_resource_value(player, game_state, worker, pos):
    dirs = [
        DIRECTIONS.NORTH,
        DIRECTIONS.EAST,
        DIRECTIONS.SOUTH,
        DIRECTIONS.WEST,
        DIRECTIONS.CENTER
    ]

    cell_value = 0.0
    for _dir in dirs:
        npos = pos.translate(_dir, 1)

        if (npos.x < 0 or npos.x >= game_state.map.width 
         or npos.y < 0 or npos.y >= game_state.map.height):
            continue

        cell = game_state.map.get_cell_by_pos(npos)

        # TODO: improve cell evaluation
        if not cell.has_resource():
            continue

        cell_value = cell_value + cell.resource.amount

    return cell_value

def get_harvest_pos(worker, player, game_state):
    rules = [
        rule_resource_value,
        rule_city_distance,
        rule_deliver_resources
    ]

    w = game_state.map.width
    h = game_state.map.height

    map_values = np.zeros((w,h))

    target_pos = Position(0,0)
    max_val = -1000

    for x in range(w):
        for y in range(h):
            pos = Position(x,y)
            rule_values = [rule(player, game_state, worker, pos) for rule in rules]
            v = np.sum(rule_values)
            if v >= max_val:
                if v == max_val:
                    # If the current value is equal to the maximum value,
                    # decide based on closest cell.
                    positions = [
                        target_pos,
                        pos
                    ]
                    dists         = [ worker.pos.distance_to(pos) for pos in positions ]
                    closest_value = sorted(zip(positions, dists), key=lambda k: k[1])[0]
                    max_val       = v
                    target_pos    = closest_value[0]
                else:
                    max_val = v
                    target_pos = pos
    
    return target_pos

