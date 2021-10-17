import hyperparams as hparams
import numpy as np
import itertools

SPACE_INTERVAL = 5

def value_to_space(key, value):
    return np.linspace(
        start=value[0], stop=value[1], num=SPACE_INTERVAL, dtype=type(value)
    )

def generate_values():
    hparams_space = {}
    n_dimensions = 0
    for key, value in hparams.space.items():
        if type(value) is list:
            n_dimensions = n_dimensions + len(value)
            var_space = [value_to_space(key, v) for v in value]
        else:
            n_dimensions = n_dimensions + 1 
            var_space = value_to_space(key, value)        

        hparams_space[key] = var_space
    return hparams_space, n_dimensions

def generate_all_possible_indexes(values):
    indexes = [ 
        list(range(len(value))) for key, value in values.items()
    ]
    return list(itertools.product(*indexes))

def indexes_to_hparams(indexes, hparams_space):
    hparam_list = []
    keys = list(hparams_space.keys())
    for ni, i in enumerate(indexes):
        print(ni, i)
        # values = hparams_space[keys[ni]]
        # hparam_list.append(
        #     hparams.Hyperparams(*[
        #         values[i[j]] for j in range(len(i))
        #     ])
        # )

    return hparam_list


if __name__ == '__main__':
    hparams_space, n_dimensions = generate_values()

    print(hparams_space)
    print('\n')

    indexes = generate_all_possible_indexes(hparams_space)
    hparam_list = indexes_to_hparams(indexes, hparams_space)
    print(hparam_list)
    #print(indexes)

    