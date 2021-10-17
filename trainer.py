from argparse import ArgumentParser
import sys

from training.generate_random_agents import generate_agents

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-g')
    parser.add_argument('-d')

    args = parser.parse_args(sys.argv)

    n = int(args['-g'])

    directory = None
    if '-d' in args:
        directory = args['-d']

    generate_agents(n, directory)