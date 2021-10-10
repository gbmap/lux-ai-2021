from typing import Dict

from lux.game_map import Position
from lux import annotate

from harvest_logic import get_action

from utils import log

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
        command
    ):
        self.worker_id     = worker_id
        self.target_pos    = target_pos
        self.target_action = target_action
        self.command       = command

    def __eq__(self, o):
        return (self.worker_id == o.worker_id and
               self.target_pos == o.target_pos and
               self.target_action == o.target_action and
               self.command == o.command)

    def same_pos(self, o):
        return self.target_pos == o.target_pos

    def annotate(self, actions):
        x = self.target_pos.x
        y = self.target_pos.y
        actions.append(annotate.text(x, y, self.target_action, 64))
        #actions.append(annotate.x(x, y))

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

def get_worker_action(worker, player, opponent, game_state, worker_actions):
    target_pos, action = get_action(worker, player, opponent, game_state, worker_actions)
    command = None
    if action == 'move':
        command = worker.move(worker.pos.direction_to(target_pos))

    elif worker.pos.distance_to(target_pos) > 0:
        command = worker.move(worker.pos.direction_to(target_pos))
    
    elif action == 'build':
        log('Worker is attempting to build.')
        command = worker.build_city()

    return WorkerAction(worker.id, target_pos, action, command)

