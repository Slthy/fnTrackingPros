import requests, os, json, time, ast
from os.path import join, dirname
from dotenv import load_dotenv
from bs4 import BeautifulSoup # type: ignore
dotenv_path = join(dirname(__file__), '../.env')
load_dotenv(dotenv_path)

TRN_API_KEY: str = os.environ['TRN_API_KEY']
FN_DB: str = os.environ['FN_DB']
REGIONS = ast.literal_eval(os.environ.get("REGIONS")) # type: ignore
FN_COLLECTIONS = [f'fn{region}players' for region in REGIONS]


GET_HTML = lambda region : requests.get(f'https://fortnitetracker.com/events/powerrankings?platform=pc&region={region}&time=current', headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'}).text

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