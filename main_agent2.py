from agent import run
from hyperparams import Hyperparams, UnitRuleWeights, load
from utils import log

FILENAME = './agents/tournament-1/7.agent'
config = {
    'hparams': load(FILENAME)
}

if __name__ == "__main__":
    run(config)