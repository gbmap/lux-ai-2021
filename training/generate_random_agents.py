

import hyperparams

def generate_agents(n : int, dir : str = './agents/'):
    if dir is None:
        dir = './agents/'

    print('Generating agents...')
    for i in range(n):
        hparams = hyperparams.from_space(space)
        hyperparams.save(f'{dir}{i}.agent')
        print(f'Generated at: {dir}')