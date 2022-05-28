from models import runModes
import argparse

def main():
  parser = argparse.ArgumentParser(description="fnTranking's helper for MongoDB databases", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("mode", type=str, choices=['populateDbs', 'getDiffs', 'all'], help="Runs script")
  args = parser.parse_args()
  config = vars(args)
  runModes(config['mode'])


if __name__ == "__main__":
  main()