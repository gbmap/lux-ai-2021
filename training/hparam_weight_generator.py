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
    target_rule : str
):
    index = rule_names.index(target_rule)
    nmin  = 0.0
    nmax  = 1.0
    values = np.linspace(nmin, nmax, num=N_VALUES)

    for v in values:
        new_hp = dataclasses.replace(hp)
        new_hp.worker_rule_weights.weights[index] = v
        print(f'Generating: \n{new_hp}')

        agent_name = f'{target_rule}_{str(round(v,2)).replace(".", "_")}'
        save_agent(new_hp, agent_name)

if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('-r')
    args = parser.parse_args()

    if args.r is not None:
        generate_hparams_weight_space(hparams.Hyperparams(), args.r)
    elif args.l is not None:
        print(rule_array)