import requests, os, ast, time, json
from typing import Any
from pymongo import MongoClient
from bs4 import BeautifulSoup # type: ignore
from os.path import join, dirname
from dotenv import load_dotenv
from difflib import SequenceMatcher

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

TRN_API_KEY: str = os.environ['TRN_API_KEY']
FN_DB: str = os.environ['FN_DB']
FN_COLLECTIONS = ast.literal_eval(os.environ.get("FN_COLLECTIONS")) # type: ignore
REGIONS = ast.literal_eval(os.environ.get("REGIONS")) # type: ignore

client = MongoClient('localhost', 27017) # type: MongoClient
db = client[FN_DB]

GET_HTML = lambda region : requests.get(f'https://fortnitetracker.com/events/powerrankings?platform=pc&region={region}&time=current', headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'}).text

def getPlayerInfos(region: str, name: str):
  html = requests.get(f'https://api.fortnitetracker.com/v1/powerrankings/pc/{region}/{name}', {'TRN-Api-Key': TRN_API_KEY})
  try:
    return json.loads(html.text)
  except:
    print(f'Api-side issue, please revert changes using the helper.py script and try again later. Error code: {html.status_code}')
    exit()

def getTop100orUnder_players(region: str, entries: int) -> list:
  if entries <= 100:
    return [player.text for player in BeautifulSoup(GET_HTML(region), features="lxml").find_all("span", class_="trn-lb-entry__name")[:entries]]
  else:
    raise ValueError('Cant handle more than 100 entries')

def getTop100orUnder_twitterTags(region: str, entries: int) -> list:
  if entries <= 100:
    tags: list[str] = []
    for link in BeautifulSoup(GET_HTML(region), features="lxml").findAll('a', {'class': 'trn-lb-entry__twitter'})[:entries]:
      try:
        link = link['href'].removeprefix('https://www.twitter.com/')
        tags.append(link)
      except KeyError:
        pass
    return tags
  else:
    raise ValueError('Cant handle more than 100 entries')

def safeGetPlayerInfos(region: str, player: str) -> dict:
  playerInfos = getPlayerInfos(region, player)
  errors = [json.loads('{"message":"API rate limit exceeded"}'), json.loads('{"status": "Try again in a few minutes. PR is updating"}')]
  while playerInfos == errors[0] or playerInfos == errors[1]:
    print('\tNeed to cooldown... || API rate limit exceeded') if playerInfos == errors[0] else print('\tNeed to cooldown... || PR is updating, consider another time to update db')
    time.sleep(61)
    print('\t...resuming')
    playerInfos = getPlayerInfos(region, player)
  return playerInfos

def populateDbs() -> None:
  print(f'[*] updating databases')
  for serverRegion, region in zip(FN_COLLECTIONS, REGIONS):
    print(f'\t[*] {region}')
    players = getTop100orUnder_players(region, 50)
    twitterTags = getTop100orUnder_twitterTags(region, 50)
    iTwitterTag = 0
    for player in players:
      print(player)
      playerInfos = safeGetPlayerInfos(region, player)
      print(playerInfos)
      if db[serverRegion].count_documents({'usernames': playerInfos['name']}) == 1: #player already stored
        db[serverRegion].update_one({ "usernames": playerInfos['name'] }, { "$push": {"pr": playerInfos['points'], 'rank': playerInfos['rank']}})
      else: #first player's record
        if (SequenceMatcher(None, twitterTags[iTwitterTag], playerInfos['name'].lower()).ratio() > 0.4): #check Twitter tag and username similatity
          db[serverRegion].insert_one({'twitter': twitterTags[iTwitterTag], "usernames": [playerInfos['name']], "pr" : [playerInfos['points']], "rank" : [playerInfos['rank']]})
        else:
          twitterInput = input(f"""is '{twitterTags[iTwitterTag]}' {playerInfos['name']}'s Twitter tag? Is so, type 'y', otherwise enter his tag: """)
          if twitterInput == 'y':
            db[serverRegion].insert_one({'twitter': twitterTags[iTwitterTag], "usernames": [playerInfos['name']], "pr" : [playerInfos['points']], "rank" : [playerInfos['rank']]})
          else:
            db[serverRegion].insert_one({'twitter': twitterInput, "usernames": [playerInfos['name']], "pr" : [playerInfos['points']], "rank" : [playerInfos['rank']]})
            iTwitterTag = iTwitterTag -1
        iTwitterTag = iTwitterTag + 1

def getHighestPrGain (data: dict) -> dict :
  highestDelta = {
    "twitter" : data[0]['twitter'],
    "delta" : (data[0]['pr'][-1] - data[0]['pr'][-2])
  }
  for player in data:
    prDelta = (player['pr'][-1] - player['pr'][-2])
    if prDelta > highestDelta['delta']:
      highestDelta['twitter'] = player['twitter']
      highestDelta['delta'] = prDelta
  return highestDelta


def getHighestRankGain (data: dict) -> dict :
  highestDelta = {
    "twitter" : data[0]['twitter'],
    "delta" : (data[0]['rank'][-2] - data[0]['rank'][-1])
  }
  for player in data:
    rankDelta = (player['rank'][-2] - player['rank'][-1])
    if rankDelta > highestDelta['delta']:
      highestDelta['twitter'] = player['twitter']
      highestDelta['delta'] = rankDelta
  return highestDelta

def getHighestRankLose(data: dict) -> dict :
  lowestDelta = {
    "twitter" : data[0]['twitter'],
    "delta" : (data[0]['rank'][-2] - data[0]['rank'][-1])
  }
  for player in data:
    rankDelta = (player['rank'][-2] - player['rank'][-1])
    if rankDelta < lowestDelta['delta']:
      lowestDelta['twitter'] = player['twitter']
      lowestDelta['delta'] = rankDelta
  return lowestDelta

def top5Diffs(data: dict, region: str) -> dict :
  currentWeek = {
    'top1' : next((player for player in data if player['rank'][-1] == 1)),
    'top2' : next((player for player in data if player['rank'][-1] == 2)),
    'top3' : next((player for player in data if player['rank'][-1] == 3)),
    'top4' : next((player for player in data if player['rank'][-1] == 4)),
    'top5' : next((player for player in data if player['rank'][-1] == 5))
  }

  results: dict[str, Any] = {
    'top1' : {
      'twitter': currentWeek['top1']['twitter'],
      'lastWeekRank': db[f"fn{region}players"].find_one({'usernames' : currentWeek['top1']['usernames'][-1]})['rank'][-2] # type: ignore
    },
    'top2' : {
      'twitter': currentWeek['top2']['twitter'],
      'lastWeekRank': db[f"fn{region}players"].find_one({'usernames' : currentWeek['top2']['usernames'][-1]})['rank'][-2] # type: ignore
    },
    'top3' : {
      'twitter': currentWeek['top3']['twitter'],
      'lastWeekRank': db[f"fn{region}players"].find_one({'usernames' : currentWeek['top3']['usernames'][-1]})['rank'][-2] # type: ignore
    },
    'top4' : {
      'twitter': currentWeek['top4']['twitter'],
      'lastWeekRank': db[f"fn{region}players"].find_one({'usernames' : currentWeek['top4']['usernames'][-1]})['rank'][-2] # type: ignore
    },
    'top5' : {
      'twitter': currentWeek['top5']['twitter'],
      'lastWeekRank': db[f"fn{region}players"].find_one({'usernames' : currentWeek['top5']['usernames'][-1]})['rank'][-2] # type: ignore
    }
  }
  return results

def newLeader(data: dict) -> dict :
  previousWeekLeader: dict= next((player for player in data if player['rank'][-2] == 1))
  currentWeekLeader: dict= next((player for player in data if player['rank'][-1] == 1))
  diffs: dict = {
    'newLeader' : {
      'twitter' : currentWeekLeader['twitter'],
      'previousRank' : currentWeekLeader['rank'][-2]
      },
    'previousLeader' : {
      'twitter' : previousWeekLeader['twitter'],
      'currentRank' : previousWeekLeader['rank'][-1]
      },
    'isSame' : currentWeekLeader['twitter'] == previousWeekLeader['twitter']
  }
  return diffs

def getDiffs():
  print('[*] getting diffs')
  for serverRegion, region in zip(FN_COLLECTIONS, REGIONS):
    print(f'\t[*] {region}')
    
    data = [document for document in db[serverRegion].find()]
    print(top5Diffs(data, region))
    try:
      print(getHighestPrGain(data))
      print(getHighestRankGain(data))
      print(getHighestRankLose(data))
      print(newLeader(data))
      print(top5Diffs(data, region))
    except IndexError:
      print('too few data, wait for a week :)')

def runModes(mode: str):
  if mode == 'populateDbs':
    populateDbs()
  elif mode == 'getDiffs':
    getDiffs()
  else:
    populateDbs()
    getDiffs()
