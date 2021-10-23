import dataclasses
from argparse import ArgumentParser
import numpy as np

import hyperparams as hparams
from rules import rule_array
from .hparam_generator import save_agent

rule_names = [r.__name__ for r in rule_array]
N_VALUES = 5

def generate_hparams_weight_space(
    hp : hparams.Hyperparams,
    target_var : str,
    var_range = (0.0, 1.0),
    nvalues = 5
):
    is_rule = 'rule' in target_var
    if is_rule:
        index = rule_names.index(target_var)
    nmin  = var_range[0]
    nmax  = var_range[1]
    values = np.linspace(nmin, nmax, num=nvalues)

    for v in values:
        new_hp = dataclasses.replace(hp)
        if is_rule:
            new_hp.worker_rule_weights.weights[index] = v
        else:
            new_hp.__dict__[target_var] = v
        print(f'Generating: \n{new_hp}')

        agent_name = f'{target_var}_{str(round(v,2)).replace(".", "_")}'
        save_agent(new_hp, agent_name)

if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('-r')
    parser.add_argument('-min')
    parser.add_argument('-max')
    parser.add_argument('-nvalues')
    args = parser.parse_args()

    var_range = (
        0.0 if args.min is None else float(args.min),
        1.0 if args.max is None else float(args.max)
    )

    nvalues = 5 if args.nvalues is None else int(args.nvalues)

    if args.r is not None:
        generate_hparams_weight_space(
            hparams.Hyperparams(), 
            args.r, 
            var_range, 
            nvalues
        )
    elif args.l is not None:
        print(rule_array)