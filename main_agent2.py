from agent import run
from hyperparams import Hyperparams, UnitRuleWeights, load
from utils import log

FILENAME = './agents/1_9e0abe7248.agent'
params = load(FILENAME)
config = {
    'hparams': params
}

if __name__ == "__main__":
    run(config)