from typing import Dict
import requests, os, ast, time, json
from datetime import date
from pymongo import MongoClient
from bs4 import BeautifulSoup
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

FN_COLLECTIONS = ast.literal_eval(os.environ.get("FN_COLLECTIONS")) # type: ignore
TRN_API_KEY: str = os.environ['TRN_API_KEY']
FN_DB: str = os.environ['FN_DB']
CREATED_IN: str = os.environ['createdIn']

client = MongoClient('localhost', 27017) # type: MongoClient

GET_HTML = lambda region : requests.get(f'https://fortnitetracker.com/events/powerrankings?platform=pc&region={region}&time=current', headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'}).text

def getPlayerInfos(region: str, name: str) -> dict:
  headers={'TRN-Api-Key': TRN_API_KEY}
  try:
    return json.loads(requests.get(f'https://api.fortnitetracker.com/v1/powerrankings/pc/{region}/{name}', headers).text)
  except:
    raise Exception

def getTop100orUnder_players(region: str, entries: int) -> list:
  html = GET_HTML(region)
  if entries <= 100:
    return [player.text for player in BeautifulSoup(html, features="lxml").find_all("span", class_="trn-lb-entry__name")[:entries]]
  else:
    raise ValueError('Cant handle more than 100 entries')

def getTop100orUnder_twitterTags(region: str, entries: int) -> list:
  html = GET_HTML(region)
  if entries <= 100:
    tags: list[str] = []
    for link in BeautifulSoup(html, features="lxml").findAll('a', {'class': 'trn-lb-entry__twitter'})[:entries]:
      try:
        link = link['href'].removeprefix('https://www.twitter.com/')
        tags.append(link)
      except KeyError:
        pass
    return tags
  else:
    raise ValueError('Cant handle more than 100 entries')
  
def createDbs() -> None:  
  if 'fnTracking' in client.list_database_names():
    print('already run setup')
  else:
    print('[*]creating databases\n')
    today = date.today()
    f = open(".env", "a")
    f.write(f"""\ncreatedIn = "{today.strftime("%b-%d-%Y")}" """)
    f.close()
    for serverName in FN_COLLECTIONS:
      db = client[FN_DB]
      db[serverName].insert_one({"createdIn": today.strftime("%b-%d-%Y")})

def safeGetPlayerInfos(region: str, player: str) -> dict:
  playerInfos = getPlayerInfos(region, player)
  exceededAPIlimitString = json.loads('{"message":"API rate limit exceeded"}')
  trnIsUpdating = json.loads('{"status": "Try again in a few minutes. PR is updating"}')
  while playerInfos == exceededAPIlimitString or playerInfos == trnIsUpdating:
    print('\tNeed to cooldown... || API rate limit exceeded') if playerInfos == exceededAPIlimitString else print('\tNeed to cooldown... || PR is updating, consider another time to update db')
    time.sleep(61)
    print('\t...resuming')
    playerInfos = getPlayerInfos(region, player)
  return playerInfos

def updateDbs() -> None:
  print(f'[*] updating databases')
  for serverRegion in FN_COLLECTIONS:
    region = serverRegion.removeprefix('fn').removesuffix('players')
    print(f'\t[*] {region}')
    players = getTop100orUnder_players(region, 50)
    twitterTags = getTop100orUnder_twitterTags(region, 50)
    for player, twitterTag in zip(players, twitterTags):
      print(player, twitterTag)
      playerInfos = safeGetPlayerInfos(region, player)
      db = client[FN_DB]
      if db[serverRegion].count_documents({'usernames': playerInfos['name']}) == 0: #if username is already in db
        twitterInput = input(f"""is '{playerInfos['twitter']}' {playerInfos['name']}'s twitter tag? If so, type 'y', else please enter his Twitter tag: """)
        if twitterInput != 'y':
          playerInfos['twitter'] = twitterInput
          if db[serverRegion].count_documents({'twitter': playerInfos['twitter']}) == 0:
            db[serverRegion].insert_one({'twitter': twitterTag, "usernames": [playerInfos['name']], "pr" : [playerInfos['points']], "rank" : [playerInfos['rank']]})
          else:
            db[serverRegion].update_one({ "twitter": playerInfos['twitter'] }, { "$push": {"usernames": playerInfos['name'], "pr": playerInfos['points'], 'rank': playerInfos['rank'] } })
        else:
          if db[serverRegion].count_documents({'twitter': playerInfos['twitter']}) == 0:
            db[serverRegion].insert_one({'twitter': twitterTag, "usernames": [playerInfos['name']], "pr" : [playerInfos['points']], "rank" : [playerInfos['rank']]})
          else:
            db[serverRegion].update_one({ "twitter": playerInfos['twitter'] }, { "$push": {"usernames": playerInfos['name'], "pr": playerInfos['points'], 'rank': playerInfos['rank'] } })
      else: 
        db[serverRegion].update_one({ "usernames": playerInfos['name'] }, { "$push": {"pr": playerInfos['points'], 'rank': playerInfos['rank']}})

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

def top5Diffs(data: dict) -> dict :
  highestDelta = {
    "twitter" : data[0]['twitter'],
    "delta" : (data[0]['pr'][-1] - data[0]['pr'][-2])
  }
  return highestDelta

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
  print(f'[*] getting diffs')
  '''for serverRegion in FN_COLLECTIONS:
    region = serverRegion.removeprefix('fn').removesuffix('players')
    print(f'\t[*] {region}')
    db = client[FN_DB]'''
  serverRegion = 'fnNAEplayers'
  db = client[FN_DB]
  cursor = db[serverRegion] # choosing the collection you need

  data = []
  for document in cursor.find():
    data.append(document)
  data.pop(0)

  print(getHighestPrGain(data))
  print(getHighestRankGain(data))
  print(getHighestRankLose(data))
  print(newLeader(data))
