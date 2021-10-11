
import random
import numpy as np
from typing import Dict, List
from lux.game_map import Position, DIRECTIONS

from utils import is_outside_map, get_city_tiles, get_turns_to_night, log, dirs, NIGHT_LENGTH, get_citytile_fuel_per_turn, normalized_distance, can_worker_build_on, adjacent_dirs, is_resource_researched, cargo_to_fuel_amount, get_units_in_pos, get_all_units, DAY_LENGTH, WHOLE_DAY_LENGTH

worker_action_map : Dict[str, str] = {}

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

def rule_deliver_resources(player, game_state, worker, pos, worker_actions):
    action = 'move'

    cell = game_state.map.get_cell_by_pos(pos)
    if cell.citytile == None:
        return (0.0, action)

    if player.team != cell.citytile.team:
        return (0.0, action)

    city = player.cities[cell.citytile.cityid]

    # TODO: Fuel is used from the city for all city tiles.
    # This should take into account adjacent cells and their
    # fuel usage as well as to create a greater priority
    # when delivering fuel to it.
    #fuel_per_turn = get_citytile_fuel_per_turn(game_state, cell.citytile)
    fuel_per_turn = city.get_light_upkeep()
    night_usage = fuel_per_turn * NIGHT_LENGTH

    cargo_fuel = cargo_to_fuel_amount(worker.cargo)

    if cargo_fuel < night_usage:
        return (0.0, action)

    weight = max(0, night_usage - city.fuel) / night_usage
    weight = float(weight > 0.0)
    return (weight, action)

def rule_resource_value(player, game_state, worker, pos, worker_actions):
    """
    Rule for collecting resources.
    """
    if worker.get_cargo_space_left() == 0:
        return (0.0, 'move')

    cell_resource_weight = 0.025
    cell_value = 0.0
    for _dir in dirs:
        npos = pos.translate(_dir, 1)

        if is_outside_map(game_state.map, npos):
            continue

        cell = game_state.map.get_cell_by_pos(npos)

        # TODO: improve cell evaluation
        # based on resource level and availability
        if not cell.has_resource() or not is_resource_researched(player, cell.resource):
            continue

        cell_value = cell_value + cell_resource_weight # * cell.resource.amount/100

    dist = normalized_distance(game_state, worker.pos, pos)

    # Make more distant cells less desirable
    cell_value = cell_value * pow(1.0 - dist, 5.0)
    return (cell_value, 'move')

def rule_build(player, game_state, worker, pos, worker_actions):
    if not can_worker_build_on(game_state.map, worker, pos):
        return (0.0, 'build')

    build_points = 0.0
    ndirs = list(set(dirs) - set([DIRECTIONS.CENTER]))

    citytile_build_weight = 0.25
    resource_build_weight = 0.0825
    if len(player.cities.keys()) == 0:
        resource_build_weight = resource_build_weight * 2.0

    for _dir in ndirs:
        neighbor_pos = pos.translate(_dir, 1)
        if is_outside_map(game_state.map, neighbor_pos):
            continue

        # City tile weight is <citytile_build_weight>.
        neighbor_cell = game_state.map.get_cell_by_pos(neighbor_pos)
        if neighbor_cell.citytile is not None and neighbor_cell.citytile.team == player.team:
            build_points = build_points + citytile_build_weight
        
        # Resource weight is [0, <resource_build_weight>] based on
        # the availability of the resources.
        elif neighbor_cell.resource is not None:
            resource = neighbor_cell.resource
            resource_weight = resource_build_weight #* resource.amount/100
            build_points = build_points + resource_weight

    return (build_points, 'build')

def rule_avoid_units(player, game_state, worker, pos, worker_actions):
    units = get_all_units(game_state.players)
    unit_in_pos = get_units_in_pos(pos, units)
    if unit_in_pos != worker:
        return (-1.0, 'move')
    return (0.0, 'move')

def rule_avoid_field_if_no_fuel(player, game_state, worker, pos, worker_actions):
    is_night = (game_state.turn % WHOLE_DAY_LENGTH) > DAY_LENGTH
    distance_to_cell = worker.pos.distance_to(pos)
    game_state.turn % WHOLE_DAY_LENGTH
    #turns_in_night = 
    #minimum_fuel = 
    if not is_night:
        return (0.0, 'move')
    
    cell = game_state.map.get_cell_by_pos(pos)
    if not cell.has_resource():
        return (-1.0, 'move')

    return (0.0, 'move')

def rule_avoid_city_tile_if_building(player, game_state, worker, pos, worker_actions):
    if worker.id not in worker_actions:
        return (0.0, 'move')

    cell = game_state.map.get_cell_by_pos(pos)

    last_action = worker_actions[worker.id]
    last_action_is_build = last_action.target_action == 'build' 
    is_pos_citytile = cell.citytile is not None

    if last_action_is_build and is_pos_citytile:
        return (-1.0, 'move')

    return (0.0, 'move')

def get_action(
    worker, 
    player, 
    opponent, 
    game_state, 
    worker_actions,
    rules = None
):
    if rules is None:
        rules = [
            (rule_resource_value, 0.2),
            (rule_deliver_resources, 10.0),
            (rule_build, 0.2),
            (rule_avoid_units, 0.5),
            (rule_avoid_field_if_no_fuel, 0.5)
#            (rule_avoid_city_tile_if_building, 0.5)
        ]

    possible_actions = get_possible_actions(
        worker, player, opponent, game_state, worker_actions, rules
    )

    cell_rule_data = select_best_action(
        possible_actions, 
        worker, 
        player, 
        opponent, 
        game_state, 
        worker_actions, 
        rules
    )
    
    rule_function = cell_rule_data[0]
    rule_value    = cell_rule_data[2]
    rule_action   = cell_rule_data[1]
    target_pos    = cell_rule_data[3]

    log(f'[TURN {game_state.turn}] [WORKER {worker.id} at {worker.pos}] [ACTION {rule_action}] [VALUE {rule_value}] at {target_pos} ({rule_function.__name__})')

    return target_pos, rule_action


def get_possible_actions(
    worker,
    player,
    opponent,
    game_state,
    worker_actions,
    rules
) -> List: 

    w = game_state.map.width
    h = game_state.map.height

    possible_actions = []

    for x in range(w):
        for y in range(h):

            cell_rule_data = calculate_cell_weight(
                x, y,
                worker,
                player,
                opponent,
                game_state,
                worker_actions,
                rules
            )

            cell_weight  = cell_rule_data[2] 

            if len(possible_actions) == 0:
                possible_actions.append(cell_rule_data)
            else:
                lowest_priority_action = possible_actions[-1]
                # lowest action has higher cell weight, continue
                if lowest_priority_action[2] > cell_rule_data[2]:
                    continue

                # same cell weight, if cell is closer,
                # add to possible actions
                elif lowest_priority_action[2] == cell_rule_data[2]:
                    dist_to_cell = worker.pos.distance_to(cell_rule_data[3])
                    dist_to_lowest_cell = worker.pos.distance_to(lowest_priority_action[3])
                    if dist_to_cell < dist_to_lowest_cell:
                        possible_actions.append(cell_rule_data)

                # cell has higher weight than lowest, add
                # to possible actions
                else:
                    possible_actions.append(cell_rule_data)

            # if cell_weight >= max_cell_weight:
            #     if cell_weight == max_cell_weight:
            #         closest_rule = min([max_rule, target_rule], key=lambda r: worker.pos.distance_to(r[3])) 
            #         # If the current value is equal to the maximum value,
            #         # decide based on closest cell.
            #     else:
            #         target_rule   = max_rule
            #     target_rule     = max_rule
            #     max_cell_weight = cell_weight
            #     possible_actions.append(target_rule)

    # Sort possible actions first by weight then by distance.
    possible_actions.sort(key=lambda a: (-a[2], worker.pos.distance_to(a[3])))
    return possible_actions

def calculate_cell_weight(
    x, y,
    worker,
    player,
    opponent,
    game_state,
    worker_actions,
    rules
):
    pos = Position(x,y)

    # Convert tuple list to two lists of
    # functions and weights
    rules = list(map(list, zip(*rules)))
    rule_functions = rules[0]
    rule_weights   = rules[1]

    # Calculate cell weight for each rule
    rule_results   = [rule(player, game_state, worker, pos, worker_actions) for rule in rule_functions]

    # Scale each rule weight by rule's weight
    rule_values    = [r[0]*rule_weights[i] for i, r in enumerate(rule_results)]
    rule_actions   = [r[1] for r in rule_results]
    rule_positions = [pos]*len(rule_results) # Ugly but quick

    # Tuple with data for current cell.
    list_cell_rule_data = zip(rules[0], rule_actions, rule_values, rule_positions)

    # Winning rule is the rule with the greatest weight.
    cell_rule_data = max(list_cell_rule_data, key=lambda k: k[2])

    # Max value for this cell.
    cell_weight = np.sum(rule_values)
    cell_rule_data = list(cell_rule_data)
    #cell_rule_data[2] = cell_weight

    return tuple(cell_rule_data)

def select_best_action(
    possible_actions,
    worker,
    player,
    opponent,
    game_state,
    worker_actions,
    rules
):  
    # Get first possible actions, aka higher score.
    cell_rule_data_index = 0
    is_valid_action = False

    # Now we handle for collisions between worker actions
    # if another worker has an action at <target_pos>,
    # we choose the next best action.
    while not is_valid_action:
        cell_rule_data = possible_actions[cell_rule_data_index]
        if len(worker_actions.items()) == 0:
            break 

        for key, action in worker_actions.items():
            is_valid_action = action.target_pos != cell_rule_data[3] 
            if not is_valid_action:
                cell_rule_data_index = cell_rule_data_index + 1

                # If all possible_actions are not available,
                # choose the first one anyways. 
                if cell_rule_data_index == len(possible_actions):
                    cell_rule_data_index = 0 
                    is_valid_action = True
                    break

                break
    
    return cell_rule_data