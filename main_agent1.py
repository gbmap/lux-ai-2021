from agent import run
from hyperparams import Hyperparams, UnitRuleWeights, load
from utils import log

FILENAME = './agents/tournament-1/9.agent'
config = {
    'hparams': Hyperparams()
}

if __name__ == "__main__":
    run(config)