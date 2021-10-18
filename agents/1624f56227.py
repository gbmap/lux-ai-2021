
from agent import run
from hyperparams import Hyperparams, UnitRuleWeights, load
from utils import log

FILENAME = './1624f56227.agent'
config = {
    'hparams': load(FILENAME)
}

if __name__ == "__main__":
    run(config)
