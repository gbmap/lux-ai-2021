from typing import Dict, List, Tuple

from lux.game_map import Position, Cell
from lux import annotate

from harvest_logic import get_action
from pathfinding import get_lowest_neighbor_weight, action_to_avoidance_map, get_neighbor_cells

from utils import log, get_most_abundant_resource, get_resource_from_cargo
import pathfinding
import rules

worker_rules = [
#    (rules.rule_collect_resources, 0.2),
    (rules.rule_collect_resources, 1.0),
    (rules.rule_deliver_resources, 1.0),
#    (rules.rule_build, 0.2),
    (rules.rule_build, 1.0),
    (rules.rule_avoid_units, 1.0),
    (rules.rule_avoid_field_if_no_fuel, 1.0),
    (rules.rule_avoid_other_target_positions, 1.0),
    (rules.rule_transfer_to_cart, 1.0)
#   (rule_avoid_city_tile_if_building, 0.5)
]

cart_rules = [
    (rules.rule_random, 1.0),
    (rules.rule_avoid_field_if_no_fuel, 1.0),
    (rules.rule_avoid_other_target_positions, 1.0)
]

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

        

def units_work(player, opponent, game_state):
    actions = []
    unit_action_map = {}
    for unit in player.units:
        if unit.can_act():
            if unit.is_worker():
                unit_rules = worker_rules
            elif unit.is_cart():
                unit_rules = cart_rules

            action = get_unit_action(
                unit, 
                player, 
                opponent, 
                game_state, 
                unit_action_map, 
                unit_rules
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
    rules
):
    target_pos, action = get_action(
        worker, 
        player, 
        opponent, 
        game_state, 
        worker_actions, 
        rules
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

        #lowest_neighbor_weight = get_lowest_neighbor_weight(
        #    game_state.map, 
        #    player, 
        #    opponent, 
        #    worker.pos, 
        #    target_pos, 
        #    action_to_avoidance_map(action)
        #)

        #lowest_neighbor_weight = get_lowest_neighbor_weight(
        #    game_state.map, 
        #    player, 
        #    opponent, 
        #    worker.pos, 
        #    target_pos, 
        #    action_to_avoidance_map(action)
        #)

        new_pos = lowest_neighbor_weight[0].pos
        direction = worker.pos.direction_to(new_pos)
        command = worker.move(direction)

    elif action == 'build':
        log('Worker is attempting to build.')
        command = worker.build_city()

    elif action == 'pillage':
        log('Worker is attempting to pillage.')
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
