from typing import Dict, List, Tuple
from lux.game_map import Cell

from utils import adjacent_dirs, get_all_units, is_unit_in_pos, is_outside_map

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

action_to_avoidance_dict = {
    'build': avoidance_map_build,
    'move': avoidance_map_move,
    'none': avoidance_map_move
}

def action_to_avoidance_map(action : str) -> Dict[str,float]:
    if action in action_to_avoidance_dict:
        return action_to_avoidance_dict[action]
    return avoidance_map_move

def pos_to_cell_type(
    game_map, 
    player, 
    opponent,
    pos
) -> str:
    units = get_all_units([player, opponent])
    if is_unit_in_pos(pos, units):
        return 'unit'

    cell = game_map.get_cell_by_pos(pos)
    if cell.citytile is not None:
        if cell.citytile.team == player.team:
            return 'citytile'
        return 'opponent citytile'
    elif cell.has_resource():
        return 'resource'

    return 'none'

def get_path_to(
    game_map,
    player,
    opponent,
    pos_A, 
    pos_B, 
    avoidance_map : Dict[str,float] = None
) -> List[Cell]:
    if pos_A == pos_B:
        return []

    # Closest cell is adjacent
    if pos_A.distance_to(pos_B) == 1:
        return [game_map.get_cell_by_pos(pos_B)]

    if avoidance_map is None:
        avoidance_map = avoidance_map_move

    # Start from pos_B (target_position)
    lowest_neighbor = get_lowest_neighbor_weight(
        game_map, 
        player, 
        opponent, 
        pos_B, 
        pos_A, 
        avoidance_map
    )
    return get_path_to(game_map, player, opponent, pos_A, lowest_neighbor[0].pos) + [lowest_neighbor[0]]

def get_lowest_neighbor_weight(
    game_map,
    player,
    opponent,
    pos,
    target_pos,
    avoidance_map : Dict[str, float]
) -> Tuple[Cell, float]:
    neighbors = get_neighbor_cells(game_map, player, opponent, pos, target_pos, avoidance_map)
    best_neighbor = min(neighbors, key=lambda n: n[1])
    return best_neighbor

def get_neighbor_cells(
    game_map,
    player,
    opponent,
    pos,
    target_pos,
    avoidance_map : Dict[str, float]
) -> Tuple[Cell, float]:
    """
    Calculates neighbor cells weight values and returns them.
    
    Returns
    ----------
    Tuple [Cell, float]
        The cell and its weight value.
    """
    neighbor_cells = []
    for direction in adjacent_dirs:
        neighbor_pos =  pos.translate(direction,1)
        if is_outside_map(game_map,neighbor_pos):
            continue

        neighbor_cell = game_map.get_cell_by_pos(neighbor_pos)
        neighbor_value = get_cell_value(game_map, player, opponent, neighbor_pos, target_pos, avoidance_map)
        neighbor_cells.append((neighbor_cell, neighbor_value))
    return neighbor_cells

def get_cell_value(
    game_map,
    player,
    opponent,
    pos,
    target_pos,
    avoidance_map : Dict[str,float]
) -> float:
    cell_type        = pos_to_cell_type(game_map, player, opponent, pos)
    cell_avoidance   = avoidance_map[cell_type]
    distance_to_pos  = target_pos - pos
    
    # Scale cell_value by its avoidance.
    cell_value = distance_to_pos * (1 + cell_avoidance)
    return cell_value
