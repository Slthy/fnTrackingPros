def main():
  import os, argparse, ast
  from pymongo import MongoClient
  from os.path import join, dirname
  from dotenv import load_dotenv
  
  dotenv_path = join(dirname(__file__), '.env')
  load_dotenv(dotenv_path)

  REGIONS = ast.literal_eval(os.environ.get("REGIONS")) # type: ignore
  
  parser = argparse.ArgumentParser(description="fnTranking's helper for MongoDB databases", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("-c", "--collection", type=str, default='all',
                      choices=REGIONS,
                      help="Runs MongoDB '$slice' query on a specific db collection (default='all')")
  parser.add_argument("items-to-keep", type=int, 
                      help="Select how many elements do you want to keep in the 'pr' and 'rank' arrays of the selected collection/s")
  args = parser.parse_args()
  config = vars(args)

  client = MongoClient('localhost', 27017) # type: MongoClient
  db = client['fnTracking']
  collections = []
  serverRegions = ['NAW', 'NAE', 'EU']

  if config['collection'] in serverRegions:
    collections = [f"fn{config['collection']}players"]
  elif config['collection'] == 'all':
    collections = ['fnNAEplayers', 'fnNAWplayers', 'fnEUplayers']
  else:
    userInput = input("invalid region, please enter a valid region or the query will be performed on all the db's collections: ")
    if userInput in serverRegions:
      collections = [f'fn{userInput}players']
    else:
      collections = ['fnNAEplayers', 'fnNAWplayers', 'fnEUplayers']
  
  print('querying all the collections') if (len(collections) > 1) else print(f"querying on {collections[0]}") 
  
  for collection in collections:
    db[collection].update_many( {}, {'$push': { "pr": {'$each': [ ], '$slice' : config['items-to-keep']}, 
                                                "rank": {'$each': [ ], '$slice' : config['items-to-keep']}}})


if __name__ == "__main__":
  main()