
class Hyperparams:
    def __init__(
        self,
        # Value of resource cell when collecting
        # resources.
        resource_collect_weight=0.025,

        # Value of resource cell when building
        resource_build_weight=0.0825,
        
        # value of citytile cell when building
        citytile_build_weight=0.25,

        # the maximum distance to the first
        # night turn when calculating
        # open field avoidance
        max_distance_to_night=5,

        # minimum distance to consider
        # transfering resources to nearby carts
        min_distance_to_cart_transfer=2
    ):
        self.resource_collect_weight = resource_collect_weight
        self.resource_build_weight   = resource_build_weight
        self.citytile_build_weight   = citytile_build_weight
        self.max_distance_to_night   = max_distance_to_night
        self.max_distance_to_night   = min_distance_to_cart_transfer

hparams = Hyperparams()