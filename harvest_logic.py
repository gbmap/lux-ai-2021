
import random
import numpy as np
from lux.game_map import Position, DIRECTIONS
from lux.game_constants import GAME_CONSTANTS

from utils import is_outside_map, get_city_tiles, get_turns_to_night, log, dirs, NIGHT_LENGTH, get_citytile_fuel_per_turn, normalized_distance, can_worker_build_on, adjacent_dirs, is_resource_researched

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

def rule_deliver_resources(player, game_state, worker, pos):
    action = 'move'

    if worker.get_cargo_space_left() > 0:
        return (0.0, action)

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

    weight = max(0, night_usage - city.fuel) / night_usage
    weight = float(weight > 0.0)
    return (weight, action)

def rule_resource_value(player, game_state, worker, pos):
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

def rule_build(player, game_state, worker, pos):
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
            (rule_deliver_resources, 0.5),
            (rule_build, 0.3)
        ]

    # Convert tuple list to two lists of
    # functions and weights
    rules = list(map(list, zip(*rules)))
    rule_functions = rules[0]
    rule_weights   = rules[1]

    w = game_state.map.width
    h = game_state.map.height

    #target_rule   = None
    #max_val = -0.1 

    # Last in first out queue to select possible actions
    # for the worker. 
    possible_actions = []

    for x in range(w):
        for y in range(h):
            pos = Position(x,y)
            rule_results   = [rule(player, game_state, worker, pos) for rule in rule_functions]

            # Scale cell rule weight by rule's weight
            rule_values    = [r[0]*rule_weights[i] for i, r in enumerate(rule_results)]
            rule_actions   = [r[1] for r in rule_results]
            rule_positions = [pos]*len(rule_results) # Ugly but quick

            # Tuple with data for current cell.
            list_cell_rule_data = zip(rules[0], rule_actions, rule_values, rule_positions)

            # Winning rule is the rule with the greatest weight.
            cell_rule_data = max(list_cell_rule_data, key=lambda k: k[2])

            # Max value for this cell.
            cell_weight = np.sum(rule_values)
            #cell_weight  = cell_rule_data[2] # 

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
    
    rule_function = cell_rule_data[0]
    rule_value    = cell_rule_data[2]
    rule_action   = cell_rule_data[1]
    target_pos    = cell_rule_data[3]

    #other_units = player.units + opponent.units
    #for unit in other_units:
    #    if unit.id == worker.id:
    #        continue
    #        
    #    if unit.pos == target_pos:
    #        # Possible collision.
    #        random_direction = adjacent_dirs[random.randint(0, 3)]
    #        target_pos.translate(random_direction, 1)

    #for key, action in worker_actions.items():
    #    # If there is already an 
    #    if action.target_pos == target_pos:

    log(f'[TURN {game_state.turn}] [WORKER {worker.id} at {worker.pos}] [ACTION {rule_action}] [VALUE {rule_value}] at {target_pos} ({rule_function.__name__})')

    return target_pos, rule_action
