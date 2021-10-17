

class UnitActionRequest:
    def __init__(
        self,
        unit, 
        player, 
        opponent, 
        game_state, 
        unit_action_map, 
        rules
    ):
        self.unit = unit
        self.player = player
        self.opponent = opponent
        self.game_state = game_state
        self.unit_actions = unit_action_map
        self.rules = rules