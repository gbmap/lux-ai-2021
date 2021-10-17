import hashlib
import os
import datetime

import hyperparams

main_template = """
from agent import run
from hyperparams import Hyperparams, UnitRuleWeights, load
from utils import log

FILENAME = '<file>'
config = {
    'hparams': load(FILENAME)
}

if __name__ == "__main__":
    run(config)
"""

def generate_agents(n : int, dir : str = './agents'):
    if dir is None:
        dir = '.'

    print('Generating agents...')
    for i in range(n):
        agent_name = hashlib.sha256(
            bytearray(str(datetime.datetime.now()), encoding='utf-8')
        ).hexdigest()[:10]
        agent_filename = f'{dir}/{agent_name}.agent'
        hparams = hyperparams.from_space(hyperparams.space)
        hyperparams.save(agent_filename, hparams)
        print(f'Generated at: {agent_filename}')

        with open(f'{agent_name}.py', 'w') as f:
            f.write(main_template.replace('<file>', agent_filename))

def get_agents_in_cwd():
    agent_files = [ f'{f}' for f in os.listdir('./') if '.agent' in f ]
    files = [ f'{f.replace(".agent", "")}.py' for f in agent_files ]
    return agent_files, files

def clear_agents():
    agent_files, files = get_agents_in_cwd() 
    [ os.remove(f) for f in agent_files]
    [ os.remove(f) for f in files]

def print_tournament_cmd():
    _, files = get_agents_in_cwd()
    print(f'sudo lux-ai-2021 --tournament {files}'.replace(',', '').replace('[', '').replace(']','').replace('\'', ''))

def print_agent_cfg(file : str):
    print(hyperparams.load(file))
