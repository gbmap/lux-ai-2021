from typing import Dict, List, Tuple, Any

from lux.game_objects import Unit
from lux.game_map import Position, Cell
from lux import annotate

from harvest_logic import get_action
from pathfinding import get_lowest_neighbor_weight, action_to_avoidance_map, get_neighbor_cells

from utils import log, get_most_abundant_resource, get_resource_from_cargo
import pathfinding
import rules

worker_rules = None 
cart_rules   = None

class UnitAction:
    def __init__(
        self,
        worker_id,
        target_pos,
        target_action,
        new_pos,
        command,
        neighbor_cell_values : List[Tuple[Cell, float]] = None,
        path = None
    ):
        self.worker_id            = worker_id
        self.target_pos           = target_pos
        self.target_action        = target_action
        self.new_pos              = new_pos
        self.command              = command
        self.neighbor_cell_values = neighbor_cell_values
        self.path                 = path

    def __eq__(self, o):
        return (
            self.worker_id     == o.worker_id and
            self.target_pos    == o.target_pos and
            self.new_pos       == o.new_pos and
            self.target_action == o.target_action and
            self.command       == o.command
        )

    def same_pos(self, o):
        return self.target_pos == o.target_pos

    def annotate(self, actions):
        x = self.target_pos.x
        y = self.target_pos.y
        actions.append(annotate.text(x, y, self.target_action, 64))

        if self.neighbor_cell_values is not None:
            for cell, value in self.neighbor_cell_values:
                actions.append(
                    annotate.text(
                        cell.pos.x, cell.pos.y, 
                        round(value,2), fontsize=64
                    )
                )

        if self.new_pos is not None:
            actions.append(
                annotate.x(self.new_pos.x, self.new_pos.y)
            )

        if self.target_pos is not None:
            actions.append(
                annotate.circle(
                    self.target_pos.x, self.target_pos.y
                )
            )

        if self.path is None:
            return

        for i, cell in enumerate(self.path):
            if i == 0:
                continue

            # Previous cell
            pcell = self.path[i-1]

            actions.append(annotate.line(
                cell.pos.x, cell.pos.y,
                pcell.pos.x, pcell.pos.y
            ))

        

"""
    UNIT ROLES
"""

map_role_to_rules = {
    'builder': worker_rules,
    'collector': worker_rules,
    'cart': cart_rules
}

map_worker_to_role : Dict[str, str] = {}

def get_percentage_map(units, map_worker_to_role):
    total_workers = len(units)
    map_role_to_percentage = {}
    map_role_to_count = {}

    if len(map_worker_to_role) == 0:
        return {
            'builder': 0.0,
            'collector': 0.0,
            'clown': 0.0
        }

    roles = ['builder', 'collector', 'clown']
    map_role_to_count = { k:list(map_worker_to_role.values()).count(k) for k in roles }
    map_role_to_percentage = {k:v/total_workers for (k,v) in map_role_to_count.items()}
    return map_role_to_percentage

def get_target_role(
    worker : Unit, 
    map_role_to_percentage : Dict[str, float], 
    map_role_distribution : Dict[str, float]
) -> Tuple[str, float]:

    map_role_delta = {}
    for key, value in map_role_to_percentage.items():
        map_role_delta[key] = value - map_role_distribution[key]

    map_role_delta = {k : v-map_role_distribution[k] for (k,v) in map_role_to_percentage.items()}

    # No absolute distance means negative values are below
    # the target distribution. Most distant current percentage
    # has priority in role allocation.
    lowest_delta = min(map_role_delta, key = lambda k: map_role_delta[k])
    return lowest_delta

def worker_to_rules(
    worker : Unit, 
    player_workers : List[Unit],
    map_worker_to_role : Dict[str, str], 
    map_role_to_rules : Dict[str, Any], 
    map_role_distribution : Dict[str, float]
) -> List:
    role = ''

    # Worker hasn't been assigned a role,
    # choose new.
    if worker.id not in map_worker_to_role:
        map_role_to_percentage = get_percentage_map(player_workers, map_worker_to_role)
        role = get_target_role(worker, map_role_to_percentage, map_role_distribution)
        map_worker_to_role[worker.id] = role
    else:
        role = map_worker_to_role[worker.id]

    return map_role_to_rules[role]

def update_worker_roles(
    workers : List[Unit],
    map_worker_to_role : Dict[str, str]
):
    new_map = {}
    for worker in workers:
        if not worker.id in map_worker_to_role:
            continue
            
        new_map[worker.id] = map_worker_to_role[worker.id]
    return new_map

"""
    UNITS LOGIC
"""

def units_work(player, opponent, game_state, configuration):
    global worker_rules 
    global cart_rules
    global map_worker_to_role
    hparams = configuration['hparams']

    player_workers = [u for u in player.units if u.is_worker()]

    map_worker_to_role = update_worker_roles(player.units, map_worker_to_role)

    if game_state.turn % 10 == 0 and configuration['use_roles']:
        percentage_map = get_percentage_map(player_workers, map_worker_to_role)
        log(f'[{game_state.turn}]')
        log(map_worker_to_role)
        log(percentage_map)

    # Shitty code beware
    if worker_rules is None:
        worker_rules = rules.generate_rule_array(hparams.worker_rule_weights)
    
    if cart_rules is None:
        cart_rules = rules.generate_rule_array(hparams.cart_rule_weights)

    actions = []
    unit_action_map = {}
    for unit in player.units:
        if not unit.can_act():
            continue

        if unit.is_worker():
            if configuration['use_roles']:
                unit_rules = rules.generate_rule_array(worker_to_rules(
                    unit, 
                    player_workers,
                    map_worker_to_role, 
                    hparams.role_rules, 
                    hparams.role_distribution
                ))
            else:
                unit_rules = worker_rules
        elif unit.is_cart():
            unit_rules = cart_rules

        action = get_unit_action(
            unit, 
            player, 
            opponent, 
            game_state, 
            unit_action_map, 
            unit_rules,
            hparams
        )
        action.annotate(actions)
        if action.command is not None:
            actions.append(action.command)

        # Add action to dictionary
        unit_action_map[unit.id] = action
    return actions

def get_unit_action(
    worker, 
    player, 
    opponent, 
    game_state, 
    worker_actions,
    rules,
    hparams
):
    target_pos, action = get_action(
        worker, 
        player, 
        opponent, 
        game_state, 
        worker_actions, 
        rules,
        hparams
    )

    command = None
    new_pos = worker.pos
    cell_weights = None
    if (
        worker.pos.distance_to(target_pos) > action_to_minimum_dist(action)
    ):
        # Shitty pathfinding.
        cell_weights = get_neighbor_cells(
            game_state.map, 
            player, 
            opponent, 
            worker.pos, 
            target_pos, 
            action_to_avoidance_map(action)
        )

        lowest_neighbor_weight = min(
            cell_weights, key=lambda n: n[1]
        )

        new_pos = lowest_neighbor_weight[0].pos
        direction = worker.pos.direction_to(new_pos)
        command = worker.move(direction)

    elif action == 'build':
        #log('Worker is attempting to build.')
        command = worker.build_city()

    elif action == 'pillage':
        #log('Worker is attempting to pillage.')
        command = worker.pillage()

    elif 'transfer' in action:
        action, transfer_id = action.split(';')
        resource_type = get_most_abundant_resource(worker.cargo)
        amount = get_resource_from_cargo(worker.cargo, resource_type)
        command = worker.transfer(transfer_id, resource_type, amount)

    return UnitAction(
        worker.id, 
        target_pos, 
        action, 
        new_pos,
        command,
        cell_weights
#        path
    )

map_action_to_minimum_dist = {
    'move': 0,
    'build': 0,
    'pillage': 0,
    'transfer': 1
}

def action_to_minimum_dist(action):
    action = action.split(';')[0]
    return map_action_to_minimum_dist[action]
