from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Any
import random
import json
import pickle

@dataclass
class UnitRuleWeights:
    weights : List[float] = field(
        default_factory = lambda: [0.0, 1.0, 0.25, 1.0, 0.5, 0.2, 0.5, 0.75, 0.0]
    )

@dataclass 
class Hyperparams():
    # Value of resource cell when collecting
    # resources.
    resource_collect_weight : float = 0.025

    # Value of resource cell when building
    resource_build_weight : float = 0.35

    # Value of citytile cell when building
    citytile_build_weight : float = 0.25

    # the maximum distance to the first
    # night turn when calculating
    # open field avoidance
    max_distance_to_night : int = 5

    # minimum distance to consider
    # transfering resources to nearby carts
    min_distance_to_cart_transfer : int = 2

    # max number of carts to be built
    max_carts : int = 0

    # distance decay exponent
    distance_decay : float = 3.5

    worker_rule_weights : UnitRuleWeights = UnitRuleWeights(
        [0.0, 1.0, 0.25, 1.0, 0.5, 0.2, 0.5, 0.75, 0.0]
    )

    cart_rule_weights : UnitRuleWeights = UnitRuleWeights(
        [1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0]
    )

    role_distribution : Dict[str, float] = field(default_factory=lambda:{
        'builder': 0.8,
        'collector': 0.2,
        'clown': 0.0
    })

    role_rules : Dict[str, UnitRuleWeights] = field(default_factory=lambda:{
        'builder': UnitRuleWeights(
            [0.0, 0.75, 0.0, 1.0, 0.5, 0.5, 0.75, 0.75]
        ),
        'collector': UnitRuleWeights(
            [0.0, 0.95, 1.0, 0.1, 0.5, 0.5, 0.75, 0.0]
        ),
        'clown': UnitRuleWeights()
    })

    def __repr__(self):
        s = 'Hyperparameters ('
        for key, value in self.__dict__.items():
            s = f'{s}\n\t{key}: {self.__dict__[key].__repr__()}'
        s = f'{s}\n)'
        return s
            
space = {
    'resource_collect_weight': (0.0, 1.0),
    'resource_build_weight' : (0.0, 1.0),
    'citytile_build_weight' : (0.0, 1.0),
    'max_distance_to_night' : (1, 10),
    'min_distance_to_cart_transfer' : (1, 10),
    'max_carts' : (0, 10),
    'distance_decay' : (0.0, 10.0),
    'worker_rule_weights' : [
        (0.0, 5.0),
        (0.0, 5.0),
        (0.0, 5.0),
        (0.0, 5.0),
        (0.0, 5.0),
        (0.0, 5.0),
        (0.0, 5.0)
    ],

    'cart_rule_weights' : [
        (0.0, 5.0),
        (0.0, 5.0),
        (0.0, 5.0),
        (0.0, 5.0),
        (0.0, 5.0),
        (0.0, 5.0),
        (0.0, 5.0)
    ]
}

def from_space(space : Dict[str, Tuple[Any,Any]]) -> Hyperparams:
    hp = Hyperparams()
    for key, value in space.items():
        if type(value) is list:
            hp.__dict__[key] = UnitRuleWeights([
                type_to_generator(type(vi[0]))(vi[0], vi[1]) for vi in value
            ])
        else:
            hp.__dict__[key] = type_to_generator(
                type(value[0]))(value[0], value[1]
            )

    return hp

def type_to_generator(t : type):
    if t is int:
        return random.randint
    elif t is float:
        return random.uniform

    return random.uniform

def load(name : str) -> Hyperparams:
    return pickle.load(open(name, 'rb'))

def save(name : str, hp : Hyperparams) -> bool:
    pickle.dump(hp, open(name, 'wb'))

if __name__ == '__main__':
    hp = Hyperparams()
    save('2.agent', hp)
    hp2 = load('2.agent')

    print(hp == hp2)


