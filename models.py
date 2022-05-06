from typing import Dict
import requests, os, ast, time, json
from datetime import date
from pymongo import MongoClient
from bs4 import BeautifulSoup
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

TRN_API_KEY: str = os.environ['TRN_API_KEY']
FN_DB: str = os.environ['FN_DB']

GET_HTML = lambda region : requests.get(f'https://fortnitetracker.com/events/powerrankings?platform=pc&region={region}&time=current', headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'}).text

def getPlayerInfos(region: str, name: str) -> dict:
  headers={'TRN-Api-Key': TRN_API_KEY}
  try:
    return json.loads(requests.get(f'https://api.fortnitetracker.com/v1/powerrankings/pc/{region}/{name}', headers).text)
  except:
    print(requests.get(f'https://api.fortnitetracker.com/v1/powerrankings/pc/{region}/{name}', headers).text)

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
  dotenv_path = join(dirname(__file__), '.env')
  load_dotenv(dotenv_path)
  FN_COLLECTIONS = ast.literal_eval(os.environ.get("FN_COLLECTIONS")) # type: ignore
  client = MongoClient('localhost', 27017) # type: MongoClient
  
  if 'fnTracking' in client.list_database_names():
    print('already run setup')
  else:
    print('[*]creating databases\n')
    today = date.today()
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
  dotenv_path = join(dirname(__file__), '.env')
  load_dotenv(dotenv_path)
  FN_COLLECTIONS = ast.literal_eval(os.environ.get("FN_COLLECTIONS")) # type: ignore
  client = MongoClient('localhost', 27017) # type: MongoClient
  for serverRegion in FN_COLLECTIONS:
    region = serverRegion.removeprefix('fn').removesuffix('players')
    print(f'\t[*] {region}')
    players = getTop100orUnder_players(region, 50)
    twitterTags = getTop100orUnder_twitterTags(region, 50)
    for player, twitterTag in zip(players, twitterTags):
        print(player, twitterTag)
        playerInfos = safeGetPlayerInfos(region, player)
        playerInfos['twitter'] = twitterTag 
        db = client[FN_DB]

        if db[serverRegion].count_documents({ 'twitter': twitterTag }, limit = 1) == 0:
          db[serverRegion].insert_one({'twitter': twitterTag, "usernames": [playerInfos['name']], "pr" : [playerInfos['points']], "rank" : [playerInfos['rank']]})
        else: 
          #TODO: cerca lui nelle liste gli username o dovrei cercarli io?
          record: dict = db[serverRegion].find({ "twitter": twitterTag })
          record['pr'].append(playerInfos['points'])
          record['rank'].append(playerInfos['rank'])
