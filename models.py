from re import L
import requests, os, ast, time, json
from pymongo import MongoClient
from bs4 import BeautifulSoup # type: ignore
from os.path import join, dirname
from dotenv import load_dotenv
from difflib import SequenceMatcher

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

TRN_API_KEY: str = os.environ['TRN_API_KEY']
FN_DB: str = os.environ['FN_DB']
REGIONS = ast.literal_eval(os.environ.get("REGIONS")) # type: ignore
FN_COLLECTIONS = [f'fn{region}players' for region in REGIONS]
CLIENT = MongoClient('localhost', 27017) # type: MongoClient
DB = CLIENT[FN_DB]

GET_HTML = lambda region : requests.get(f'https://fortnitetracker.com/events/powerrankings?platform=pc&region={region}&time=current', headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'}).text

def findMaxRecords(region: str) -> int:
  if (lenMax := DB[f"fn{region}players"].find_one({})) is not None:
    lenMax = len(lenMax['pr'])
    players = DB[f"fn{region}players"].find({})
    for player in players:
      lenMax = len(player['pr']) if len(player['pr']) > lenMax else lenMax
    return lenMax
  return 0

def getPlayerInfos(region: str, name: str):
  html = requests.get(f'https://api.fortnitetracker.com/v1/powerrankings/pc/{region}/{name}', {'TRN-Api-Key': TRN_API_KEY})
  try:
    return json.loads(html.text)
  except:
    print(f'https://api.fortnitetracker.com/v1/powerrankings/pc/{region}/{name}')
    print(f'Api-side issue, please revert changes using the helper.py script and try again later. Error code: {html.status_code}')

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

def addNullRecords(playersTwitterTag: str, pr: str, rank: str, region: str) -> None:
  lenMax = findMaxRecords(region)
  for i in range(lenMax - lenMax - 1):
    DB[f'fn{region}players'].update_one({ "twitter": playersTwitterTag }, { "$push": {"pr": 0, 'rank': 0}})
  DB[f'fn{region}players'].update_one({ "twitter": playersTwitterTag }, { "$push": {"pr": pr, 'rank': rank}})

def populateDbs() -> None:
  print(f'[*] updating databases')
  for serverRegion, region in zip(FN_COLLECTIONS, REGIONS):
    print(f'\t[*] {region}')
    players = getTop100orUnder_players(region, 50)
    twitterTags = getTop100orUnder_twitterTags(region, 50)
    iTwitterTag = 0
    for player in players:
      playerInfos = safeGetPlayerInfos(region, player)
      if DB[serverRegion].count_documents({'usernames': playerInfos['name']}) == 1: #player already stored
        DB[serverRegion].update_one({ "usernames": playerInfos['name'] }, { "$push": {"pr": playerInfos['points'], 'rank': playerInfos['rank']}})
        iTwitterTag = iTwitterTag + 1
      else: #first player's record
        if (SequenceMatcher(None, twitterTags[iTwitterTag], playerInfos['name'].lower()).ratio() > 0.4): #check Twitter tag and username similatity
          DB[serverRegion].insert_one({'twitter': twitterTags[iTwitterTag], "usernames": [playerInfos['name']]})
          addNullRecords(twitterTags[iTwitterTag], playerInfos['points'], playerInfos['rank'], region)
          print(playerInfos['name'] + f" (twitter: '{twitterTags[iTwitterTag]}') has entered in the top50 for the first time!")
        else:
          twitterInput = input(f"""is '{twitterTags[iTwitterTag]}' {playerInfos['name']}'s Twitter tag? Is so, type 'y', otherwise enter his tag: """)
          if twitterInput == 'y':
            DB[serverRegion].insert_one({'twitter': twitterTags[iTwitterTag], "usernames": [playerInfos['name']]})
            addNullRecords(twitterTags[iTwitterTag], playerInfos['points'], playerInfos['rank'], region)
            print(playerInfos['name'] + f" (twitter: '{twitterTags[iTwitterTag]}') has entered in the top50 for the first time!")
          else:
            DB[serverRegion].insert_one({'twitter': twitterInput, "usernames": [playerInfos['name']]})
            addNullRecords(twitterInput, playerInfos['points'], playerInfos['rank'], region)
            print(playerInfos['name'] + f" (twitter: '{twitterInput}') has entered in the top50 for the first time!")
            iTwitterTag = iTwitterTag - 1
        iTwitterTag = iTwitterTag + 1

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
      if ((playerlastWeek := DB[f"fn{region}players"].find_one({'usernames' : lastWeek[f'top{index+1}']['usernames'][-1]})) is not None) and ((previousWeek := DB[f"fn{region}players"].find_one({'usernames' : lastWeek[f'top{index+1}']['usernames'][-1]})) is not None):
        playerlastWeekRank = playerlastWeek['rank'][-1]
        playerlastWeek = previousWeek['rank'][-2]
        if playerlastWeekRank != playerlastWeek:
          results[f'top{index+1}'] = {
            'twitter': lastWeek[f'top{index+1}']['twitter'],
            'playerlastWeekRank': playerlastWeekRank
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

def fixUnderTop50():
  for region in REGIONS:
    lenMax = findMaxRecords(region)
    players = DB[f"fn{region}players"].find({})
    for player in players:
      if (len(player['pr']) < lenMax):
        for i in range(lenMax - len(player['pr'])):
          DB[f'fn{region}players'].update_one({ "usernames": player['usernames'][0] }, { "$push": {"pr": 0, 'rank': 0}})


def getDiffs():
  print('[*] Diffs:\n')
  for serverRegion, region in zip(FN_COLLECTIONS, REGIONS):
    print('\t[*]', region)
    data = [document for document in DB[serverRegion].find()]
    print('\t\t[*]getHighestPrGain', getHighestPrGain(data))
    print('\t\t[*]getHighestRankGain', getHighestRankGain(data))
    print('\t\t[*]getHighestRankLose', getHighestRankLose(data)) if getHighestRankLose(data)['delta'] < 0 else None
    print('\t\t[*]newLeader', newLeader(data)) if newLeader(data)['isSame'] != True else None
    print('\t\t[*]top5Diffs', top5Diffs(data, region)) if top5Diffs(data, region) != {} else None

def runModes(mode: str):
  if mode == 'populateDbs':
    populateDbs()
    fixUnderTop50()
  elif mode == 'getDiffs':
    getDiffs()
  else:
    populateDbs()
    getDiffs()
