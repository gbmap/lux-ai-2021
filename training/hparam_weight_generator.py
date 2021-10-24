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

def generate_role_distribution(values):
    hp = hparams.Hyperparams()
    for i, key in enumerate(hp.role_distribution):
        hp.role_distribution[key] = values[i]
    save_agent(hp, f'rd_{values[0]}__{values[1]}__{values[2]}'.replace('.','_'))

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-gr', help='Generate rule')
    parser.add_argument('-min', help='Minimum value for generated rule')
    parser.add_argument('-max', help='Maximum value for generated rule')
    parser.add_argument('-nvalues', help='Number of values between -min and -max')
    parser.add_argument('-gd', help='Generate role distribution', nargs=3, type=float)

    args = parser.parse_args()

    if args.gr is not None and args.gd is not None:
        print('Specify either rule (-r) or role distribution (-d)')
        sys.exit(0)

    if args.gr is not None:
        has_min = args.min is not None
        has_max = args.max is not None
        has_nvalues = args.values is not None
        if not has_min:
            print('Defaulting minimum value to 0.0')

        if not has_max:
            print('Defaulting maximum value to 1.0')

        if not has_nvalues:
            print('Defaulting to 5 nvalues')

        var_range = (
            float(args.min) if has_min else 0.0,
            float(args.max) if has_max else 1.0
        )

        nvalues = int(args.nvalues) if has_nvalues else 5

        generate_hparams_weight_space(
            hparams.Hyperparams(), 
            args.r, 
            var_range, 
            nvalues
        )

    elif args.gd is not None:
        generate_role_distribution(args.gd)

    elif args.l is not None:
        print(rule_array)