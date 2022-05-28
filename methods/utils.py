import os, ast
from pymongo import MongoClient
from os.path import join, dirname
from dotenv import load_dotenv
dotenv_path = join(dirname(__file__), '../.env')
load_dotenv(dotenv_path)

TRN_API_KEY: str = os.environ['TRN_API_KEY']
FN_DB: str = os.environ['FN_DB']
REGIONS = ast.literal_eval(os.environ.get("REGIONS")) # type: ignore

CLIENT = MongoClient('localhost', 27017) # type: MongoClient
DB = CLIENT[FN_DB]

def findMaxRecords(region: str) -> int:
  if (lenMax := DB[f"fn{region}players"].find_one({})) is not None:
    try:
      lenMax = len(lenMax['pr'])
      players = DB[f"fn{region}players"].find({})
      for player in players:
        lenMax = len(player['pr']) if len(player['pr']) > lenMax else lenMax
    except: #first run
      pass
    return lenMax
  return 0

def addNullRecords(playersTwitterTag: str, pr: str, rank: str, region: str) -> None:
  try:
    lenMax = findMaxRecords(region)
    for i in range(lenMax - lenMax - 1):
      DB[f'fn{region}players'].update_one({ "twitter": playersTwitterTag }, { "$push": {"pr": 0, 'rank': 0}})
    DB[f'fn{region}players'].update_one({ "twitter": playersTwitterTag }, { "$push": {"pr": pr, 'rank': rank}})
  except: #first run
    pass

def fixUnderTop50():
  for region in REGIONS:
    lenMax = findMaxRecords(region)
    players = DB[f"fn{region}players"].find({})
    for player in players:
      try:
        if (len(player['pr']) < lenMax):
          for i in range(lenMax - len(player['pr'])):
            DB[f'fn{region}players'].update_one({ "usernames": player['usernames'][0] }, { "$push": {"pr": 0, 'rank': 0}})
      except KeyError: #first run
        pass