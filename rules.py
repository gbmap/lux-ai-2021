
import random
import utils
from typing import List, Tuple, Any
from utils import is_outside_map, get_city_tiles, get_turns_to_night, log, dirs, NIGHT_LENGTH, get_citytile_fuel_per_turn, normalized_distance, can_worker_build_on, adjacent_dirs, is_researched, cargo_to_fuel_amount, get_units_in_pos, get_all_units, DAY_LENGTH, WHOLE_DAY_LENGTH
from hyperparams import UnitRuleWeights

# RULE ORDER
# rule_array = [
#     rule_random,
#     rule_collect_resources,
#     rule_deliver_resources,
#     rule_build,
#     rule_avoid_units,
#     rule_avoid_field_if_no_fuel,
#     rule_avoid_other_target_positions,
# ]

def generate_rule_array(weights : UnitRuleWeights) -> List[Tuple[Any, float]]:
    if len(weights.weights) < len(rule_array):
        raise Exception(f'Expecting a weight list of {len(rule_array)} values.')
    
    return list(zip(rule_array, weights.weights))

def rule_deliver_resources(
    player, 
    game_state, 
    worker, 
    pos, 
    worker_actions,
    hparams
):
    action = 'move'

    cell = game_state.map.get_cell_by_pos(pos)
    if cell.citytile == None:
        return (0.0, action)

    if player.team != cell.citytile.team:
        return (0.0, action)

    if worker.get_cargo_space_left() > 0:
        return (0.0, action)

    city = player.cities[cell.citytile.cityid]

    # TODO: Fuel is used from the city for all city tiles.
    # This should take into account adjacent cells and their
    # fuel usage as well as to create a greater priority
    # when delivering fuel to it.
    #fuel_per_turn = get_citytile_fuel_per_turn(game_state, cell.citytile)
    fuel_per_turn = city.get_light_upkeep()
    night_usage = fuel_per_turn * utils.NIGHT_LENGTH

    # cargo_fuel = utils.cargo_to_fuel_amount(worker.cargo)

    # This is preventing agents from
    # delivering during the day.
    # if cargo_fuel < night_usage:
    #     return (0.0, action)

    weight = max(0, night_usage - city.fuel) / night_usage
    weight = float(weight > 0.0)
    return (weight, action)

def rule_collect_resources(
    player, 
    game_state, 
    worker, 
    pos, 
    worker_actions,
    hparams
):
    """
    Rule for collecting resources.
    """
    if worker.get_cargo_space_left() == 0:
        return (0.0, 'move')

    cell_resource_weight = hparams.resource_collect_weight
    cell_value = 0.0
    for _dir in utils.dirs:
        npos = pos.translate(_dir, 1)

        if utils.is_outside_map(game_state.map, npos):
            continue

        cell = game_state.map.get_cell_by_pos(npos)

        # TODO: improve cell evaluation
        # based on resource level and availability
        if not cell.has_resource() or not utils.is_researched(player, cell.resource):
            continue

        cell_value = cell_value + cell_resource_weight # * cell.resource.amount/100

    dist = utils.normalized_distance(game_state, worker.pos, pos)
    cell_value = decay_distance(
        game_state, 
        cell_value, 
        worker.pos, 
        pos,
        hparams.distance_decay
    )
    return (cell_value, 'move')

def rule_build(
    player, 
    game_state, 
    worker, 
    pos, 
    worker_actions,
    hparams
):
    if not utils.can_worker_build_on(game_state.map, worker, pos):
        return (0.0, 'build')

    build_points = 0.0
    ndirs = list(set(utils.dirs) - set([utils.DIRECTIONS.CENTER]))

    citytile_build_weight = hparams.citytile_build_weight
    resource_build_weight = hparams.resource_build_weight
    if len(player.cities.keys()) == 0:
        resource_build_weight = resource_build_weight * 2.0

    for _dir in ndirs:
        neighbor_pos = pos.translate(_dir, 1)
        if utils.is_outside_map(game_state.map, neighbor_pos):
            continue

        # City tile weight is <citytile_build_weight>.
        neighbor_cell = game_state.map.get_cell_by_pos(neighbor_pos)
        if neighbor_cell.citytile is not None and neighbor_cell.citytile.team == player.team:
            build_points = build_points + citytile_build_weight
        
        # Resource weight is [0, <resource_build_weight>] based on
        # the availability of the resources.
        elif neighbor_cell.resource is not None:
            if not is_researched(player, neighbor_cell.resource):
                continue

            resource = neighbor_cell.resource
            resource_weight = resource_build_weight #* resource.amount/100
            build_points = build_points + resource_weight

    build_points = decay_distance(
        game_state, 
        build_points, 
        worker.pos, 
        pos,
        hparams.distance_decay
    )
    return (build_points, 'build')

def rule_avoid_units(
    player, 
    game_state, 
    worker, 
    pos, 
    worker_actions,
    hparams
):
    units = utils.get_all_units(game_state.players)
    unit_in_pos = utils.get_units_in_pos(pos, units)
    if unit_in_pos != worker:
        return (-1.0, 'move')
    return (0.0, 'move')

def rule_avoid_field_if_no_fuel(
    player, 
    game_state, 
    worker, 
    pos, 
    worker_actions,
    hparams
):
    is_night = (game_state.turn % utils.WHOLE_DAY_LENGTH) > utils.DAY_LENGTH
    distance_to_cell = worker.pos.distance_to(pos)

    has_fuel = utils.cargo_to_fuel_amount(worker.cargo)
    #if not is_night:
    #    return (0.0, 'move')
    
    turns_to_night = 0
    t = (game_state.turn % utils.WHOLE_DAY_LENGTH)
    if t < utils.DAY_LENGTH:
        turns_to_night = utils.DAY_LENGTH - t

    # [0, 1] based on distance to night turn.
    n = hparams.max_distance_to_night
    cell_weight_by_turn = (n - min(n, turns_to_night))/n

    # [0, 1] based on distance to current position
    #cell_weight_by_distance = 

    cell = game_state.map.get_cell_by_pos(pos)
    if not cell.has_resource():
        return (-1.0*cell_weight_by_turn, 'move')

    return (0.0, 'move')

def rule_avoid_city_tile_if_building(
    player, 
    game_state, 
    worker, 
    pos, 
    worker_actions,
    hparams
):
    if worker.id not in worker_actions:
        return (0.0, 'move')

    cell = game_state.map.get_cell_by_pos(pos)

    last_action = worker_actions[worker.id]
    last_action_is_build = last_action.target_action == 'build' 
    is_pos_citytile = cell.citytile is not None

    if last_action_is_build and is_pos_citytile:
        return (-1.0, 'move')

    return (0.0, 'move')

def rule_transfer_to_cart(
    player,
    game_state,
    worker,
    pos,
    worker_actions,
    hparams
):
    if pos.distance_to(worker.pos) > hparams.max_distance_to_night:
        return (0.0, 'move')

    carts_in_pos = [
        unit for unit in utils.get_units_in_pos(pos, player.units)
        if unit.is_cart()
    ]

    if len(carts_in_pos) == 0:
        return (0.0, 'move')

    cart = carts_in_pos[0]
    if cart.get_cargo_space_left() > 0:
        return (1.0, f'transfer;{cart.id}')

    return (0.0, 'move')

def rule_avoid_other_target_positions(
    player,
    game_state,
    worker,
    pos,
    worker_actions,
    hparams
):
    for key, action in worker_actions.items():
        if action.worker_id == worker.id:
            continue

        if action.new_pos == pos or action.target_pos == pos:
            return (-1.0, 'move')
    
    return (0.0, 'move')


def rule_patrol(
    player,
    game_state,
    worker,
    pos,
    worker_actions,
    hparams
):
    pass

def rule_random(
    player,
    game_state,
    worker,
    pos,
    worker_actions,
    hparams
):
    return ((random.random()-0.5)*2.0, 'move')

def rule_avoid_far_cells(
    player,
    game_state,
    worker, 
    pos, 
    worker_actions,
    hparams
):
    td = -utils.normalized_distance(game_state,worker.pos, pos)
    return (td, 'move')

def decay_distance(game_state, cell_value, posA, posB, distance_decay):
    dist = utils.normalized_distance(game_state, posA, posB)

    # Make more distant cells less desirable
    cell_value = cell_value * pow(1.0 - dist, distance_decay)
    return cell_value

rule_array = [
    rule_random,
    rule_collect_resources,
    rule_deliver_resources,
    rule_build,
    rule_avoid_units,
    rule_avoid_field_if_no_fuel,
    rule_avoid_other_target_positions
]