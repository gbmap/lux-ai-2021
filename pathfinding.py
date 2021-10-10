from typing import Dict

"""
Simple quick and ugly pathfinding. Because units
attempting to build stuff and losing its resources
by a friendly city tile is boring.
"""

avoidance_map_build = {
    'citytile': 1.0,
    'opponent citytile': 1.0,
    'unit': 1.0,
    'resource': 0.0,
    'none': 0.0
}

avoidance_map_move = {
    'citytile': 0.0,
    'opponent citytile': 1.0,
    'unit': 1.0,
    'resource': 0.0,
    'none': 0.0
}

def action_to_avoidance_map(action : str) -> Dict[str,float]:
    if action == 'build':
        return avoidance_map_build
    return avoidance_map_move

def pos_to_str(game_state, pos):
    #game_state.

    if cell.has_resource():
        return 'resource'
    return 'none'

def get_path_to(
    map, 
    pos_A, 
    pos_B, 
    avoidance_dict : Dict[str,float] = None
):
    pass