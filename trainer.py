from argparse import ArgumentParser
import sys

from training.cmd import generate_agents, print_tournament_cmd, print_agent_cfg, clear_agents

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-c')
    parser.add_argument('-g')
    parser.add_argument('-d')
    parser.add_argument('-pa', help='Prints agent')
    parser.add_argument('--tournament_cmd')

    args = parser.parse_args()

    if args.c is not None:
        clear_agents()
        sys.exit(0)

    if args.tournament_cmd is not None:
        print_tournament_cmd()
        sys.exit(0)

    if args.pa is not None:
        print_agent_cfg(args.pa)
        sys.exit(0)

    n = int(args.g)

    directory = None
    if args.d is not None:
        directory = args.d

    generate_agents(n, directory)
