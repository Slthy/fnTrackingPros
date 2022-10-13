import os, ast
from pymongo import MongoClient
from os.path import join, dirname
from dotenv import load_dotenv
dotenv_path = join(dirname(__file__), '../.env')
load_dotenv(dotenv_path)

TRN_API_KEY: str = os.environ['TRN_API_KEY']
FN_DB: str = os.environ['FN_DB']
REGIONS = ast.literal_eval(os.environ.get("REGIONS")) # type: ignore
FN_COLLECTIONS = [f'fn{region}players' for region in REGIONS]
CLIENT = MongoClient('localhost', 27017) # type: MongoClient
DB = CLIENT[FN_DB]

def getHighestPrGain (data: dict) -> dict :
  highestDelta = {}
  try:
    highestDelta = {
      "twitter" : data[0]['twitter'],
      "delta" : (data[0]['pr'][-2] - data[0]['pr'][-1])
    }
  except IndexError: #collection has only one record per player (setup run)
    print('Too few records (1), come back next week :)')
    exit()
  for player in data:
    try:
      if player['pr'][-2] != 0: #checks if the previous week the player was in the top50
        prDelta = (player['pr'][-1] - player['pr'][-2])
        if prDelta > highestDelta['delta']:
          highestDelta['twitter'] = player['twitter']
          highestDelta['delta'] = prDelta
    except IndexError: #player has only one record
      pass
  return highestDelta


def getHighestRankGain (data: dict) -> dict :
  highestDelta = {
    "twitter" : data[0]['twitter'],
    "delta" : (data[0]['rank'][-2] - data[0]['rank'][-1])
  } 
  for player in data:
    try:
      if player['pr'][-2] != 0: #checks if the previous week the player was in the top50
        rankDelta = (player['rank'][-2] - player['rank'][-1])
        if rankDelta > highestDelta['delta']:
          highestDelta['twitter'] = player['twitter']
          highestDelta['delta'] = rankDelta
    except IndexError: #player has only one record
      pass
  return highestDelta


def getHighestRankLose(data: dict) -> dict :
  lowestDelta = {
    "twitter" : data[0]['twitter'],
    "delta" : (data[0]['rank'][-2] - data[0]['rank'][-1])
  }
  for player in data:
    try:
      if player['pr'][-2] != 0: #checks if the previous week the player was in the top50
        rankDelta = (player['rank'][-2] - player['rank'][-1])
        if rankDelta < lowestDelta['delta']:
          lowestDelta['twitter'] = player['twitter']
          lowestDelta['delta'] = rankDelta
    except IndexError: #player has only one record
      pass
  return lowestDelta

def top5Diffs(data: dict, region: str) -> dict :
  lastWeek = {}
  results = {}
  try:
    lastWeek = {
      'top1' : next((player for player in data if player['rank'][-1] == 1)),
      'top2' : next((player for player in data if player['rank'][-1] == 2)),
      'top3' : next((player for player in data if player['rank'][-1] == 3)),
      'top4' : next((player for player in data if player['rank'][-1] == 4)),
      'top5' : next((player for player in data if player['rank'][-1] == 5))
    }
  except IndexError: #player has only one record
    pass
  for index, top in enumerate(lastWeek.items()):
    if len(top[1]['pr']) == 1: #pr
      results[f'top{index+1}'] = {
        'twitter' : top[1]['twitter'], 
        'news': 'first entry in top5 for: '+top[1]['twitter']}
    else: #mypy workaround, check if "username" field exist, if so do things, else raise exception
      if ((currentWeek := DB[f"fn{region}players"].find_one({'usernames' : lastWeek[f'top{index+1}']['usernames'][-1]})) is not None) and ((previousWeek := DB[f"fn{region}players"].find_one({'usernames' : lastWeek[f'top{index+1}']['usernames'][-1]})) is not None):
        currentWeekRank = currentWeek['rank'][-1]
        previousWeekRank = previousWeek['rank'][-2]
        #print(currentWeekRank, previousWeekRank)
        if currentWeekRank != previousWeekRank:
          results[f'top{index+1}'] = {
            'twitter': lastWeek[f'top{index+1}']['twitter'],
            'playerlastWeekRank': previousWeekRank
          }
      else:
        raise Exception
  return results

def newLeader(data: dict) -> dict :
  try: 
    previousWeekLeader: dict= next((player for player in data if player['rank'][-2] == 1))
    lastWeekLeader: dict= next((player for player in data if player['rank'][-1] == 1))
  except IndexError: #player has only one record
      pass
  diffs: dict = {
    'newLeader' : {
      'twitter' : lastWeekLeader['twitter'],
      'previousRank' : lastWeekLeader['rank'][-2]
      },
    'previousLeader' : {
      'twitter' : previousWeekLeader['twitter'],
      'currentRank' : previousWeekLeader['rank'][-1]
      },
    'isSame' : lastWeekLeader['twitter'] == previousWeekLeader['twitter']
  }
  return diffs
