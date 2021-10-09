
import logging

logging.basicConfig(filename='log.log',level=logging.DEBUG)

def log(msg):
    logging.info(msg)

def get_city_tiles(game_state, player):
    city_tiles = []
    for k, city in player.cities.items():
        for city_tile in city.citytiles:
            log(city_tile)
            city_tiles.append(city_tile)

    return city_tiles

def get_turns_to_night(game_state):
    return abs(min(0, (game_state.turn % 40) - 30))

def get_cells(player, game_state, cell_type):  # resource, researched resource, player citytile, enemy citytile, empty
    """
    Given a cell type, returns a list of Cell objects of the given type
    Options are: ['resource', 'researched resource', 'player citytile', 'enemy citytile', 'empty']
    """
    width = game_state.map.width
    height = game_state.map.height

    cells_of_type = []
    for y in range(height):
        for x in range(width):
            cell = game_state.map.get_cell(x, y)
            if (
                    ( cell_type == 'resource' and cell.has_resource() ) \
                or ( cell_type == 'researched resource' and cell.has_resource() and researched(cell.resource) ) \
                or ( cell_type == 'player citytile' and cell.citytile is not None and cell.citytile.team == player ) \
                or ( cell_type == 'enemy citytile' and cell.citytile is not None and cell.citytile.team != player ) \
                or ( cell_type == 'empty' and cell.citytile is None and not cell.has_resource() )
            ):
                cells_of_type.append(cell)
    
    return cells_of_type

