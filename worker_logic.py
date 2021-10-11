from typing import Dict

from lux.game_map import Position
from lux import annotate

from harvest_logic import get_action, calculate_cell_weight
from pathfinding import get_lowest_neighbor_weight, action_to_avoidance_map

from utils import log
import pathfinding

actions = [
    'HARVEST',
    'SABOTAGE',
    'BUILD'
]

class WorkerAction:
    def __init__(
        self,
        worker_id,
        target_pos,
        target_action,
        new_pos,
        command,
        path = None
    ):
        self.worker_id     = worker_id
        self.target_pos    = target_pos
        self.target_action = target_action
        self.new_pos       = new_pos
        self.command       = command
        self.path          = path

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


# lol
def workers_work(player, opponent, game_state):
    actions = []
    worker_actions = {}
    for unit in player.units:
        if unit.is_worker() and unit.can_act():
            worker_action = get_worker_action(unit, player, opponent, game_state, worker_actions)
            worker_action.annotate(actions)
            actions.append(worker_action.command)

            # Add action to dictionary
            worker_actions[unit.id] = worker_action
    
    return actions

def get_worker_action(
    worker, 
    player, 
    opponent, 
    game_state, 
    worker_actions
):
    target_pos, action = get_action(worker, player, opponent, game_state, worker_actions)

    #path = pathfinding.get_path_to(
    #    game_state.map, 
    #    player, 
    #    opponent, 
    #    worker.pos, 
    #    target_pos
    #)

    command = None
    new_pos = None
    if (
        action == 'move' or 
        worker.pos.distance_to(target_pos) > 0
    ):
        #new_pos = worker.pos.translate(direction, 1)

        # Check if new position is valid.
        lowest_neighbor_weight = get_lowest_neighbor_weight(
            game_state.map, 
            player, 
            opponent, 
            worker.pos, 
            target_pos, 
            action_to_avoidance_map(action)
        )

        new_pos = lowest_neighbor_weight[0].pos
        direction = worker.pos.direction_to(new_pos)
        command = worker.move(direction)

    elif action == 'build':
        log('Worker is attempting to build.')
        command = worker.build_city()

    elif action == 'pillage':
        log('Worker is attempting to pillage.')
        command = worker.pillage()

    return WorkerAction(
        worker.id, 
        target_pos, 
        action, 
        new_pos,
        command,
#        path
    )

