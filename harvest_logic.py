
import random
import numpy as np
from typing import Dict, List
from lux.game_map import Position, DIRECTIONS

from utils import is_outside_map, get_city_tiles, get_turns_to_night, log, dirs, NIGHT_LENGTH, get_citytile_fuel_per_turn, normalized_distance, can_worker_build_on, adjacent_dirs, is_researched, cargo_to_fuel_amount, get_units_in_pos, get_all_units, DAY_LENGTH, WHOLE_DAY_LENGTH
import rules

def get_action(
    worker, 
    player, 
    opponent, 
    game_state, 
    worker_actions,
    rules,
    hparams,
):
    possible_actions = get_possible_actions(
        worker, 
        player, 
        opponent, 
        game_state, 
        worker_actions, 
        rules,
        hparams
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

    #log(f'[TURN {game_state.turn}] [WORKER {worker.id} at {worker.pos}] [ACTION {rule_action}] [VALUE {rule_value}] at {target_pos} ({rule_function.__name__})')

    return target_pos, rule_action


def get_possible_actions(
    worker,
    player,
    opponent,
    game_state,
    worker_actions,
    rules,
    hparams
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
                rules,
                hparams
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
    rules,
    hparams
):
    pos = Position(x,y)

    # Convert tuple list to two lists of
    # functions and weights
    rules = list(map(list, zip(*rules)))
    rule_functions = rules[0]
    rule_weights   = rules[1]

    # Calculate cell weight for each rule
    rule_results   = [rule(player, game_state, worker, pos, worker_actions, hparams) for rule in rule_functions]

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