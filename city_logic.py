
from utils import get_unit_dict, UNIT_TYPES

def cities_work(player, opponent, game_state, unit_allocation=None):
    actions = []
    can_build_unit = len(player.units) < player.city_tile_count
    for k, city in player.cities.items():
        for city_tile in city.citytiles:
            if not city_tile.can_act():
                continue

            if can_build_unit:
                unit_dict = get_unit_dict(player)
                total     = len(player.units)
                n_workers = unit_dict[UNIT_TYPES["WORKER"]]
                n_carts   = unit_dict[UNIT_TYPES["CART"]]

                if total == 0:
                    actions.append(city_tile.build_worker())
                    continue

                percentage_workers = n_workers / total
                percentage_carts   = n_carts   / total

                # no need for carts while no cart AI
                if percentage_carts < 0.0:
                    actions.append(city_tile.build_cart())
                else:
                    actions.append(city_tile.build_worker())
                #actions.append(unit_allocation.build(player))
                
            else:
                actions.append(city_tile.research())
    
    return actions


