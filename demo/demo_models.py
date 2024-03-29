import os, ast, json
from pymongo import MongoClient
from os.path import join, dirname
from dotenv import load_dotenv
from difflib import SequenceMatcher
from decimal import *
from alive_progress import alive_bar #type: ignore

from methods.demo_utils import addNullRecords, fixUnderTop50 #type: ignore
from methods.demo_getDiffs import getHighestPrGain, getHighestRankGain, getHighestRankLose, newLeader, top5Diffs #type: ignore

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

FN_DB: str = os.environ['FN_DB']
REGIONS = ast.literal_eval(os.environ.get("REGIONS")) # type: ignore
FN_COLLECTIONS = [f'fn{region}players' for region in REGIONS]
CLIENT = MongoClient('localhost', 27017) # type: MongoClient
DB = CLIENT[FN_DB]

demo_data: dict = {}
with open('demoData.json', 'r') as f:
  demoData = json.load(f)

data: dict = {
  'WEEK_1': {
    'EU' : {
      'players': demoData['WEEK_1']['EU']['players'],
      'twitterTags': demoData['WEEK_1']['EU']['twitterTags'],
      'playerInfos': demoData['WEEK_1']['EU']['playerInfos']
    },
    'NAW': {
      'players': demoData['WEEK_1']['NAW']['players'],
      'twitterTags': demoData['WEEK_1']['NAW']['twitterTags'],
      'playerInfos': demoData['WEEK_1']['NAW']['playerInfos']
    },
    'NAE': {
      'players': demoData['WEEK_1']['NAE']['players'],
      'twitterTags': demoData['WEEK_1']['NAE']['twitterTags'],
      'playerInfos': demoData['WEEK_1']['NAE']['playerInfos']
    } 
  },
  'WEEK_2': {
    'EU' : {
      'players': demoData['WEEK_2']['EU']['players'],
      'twitterTags': demoData['WEEK_2']['EU']['twitterTags'],
      'playerInfos': demoData['WEEK_2']['EU']['playerInfos']
    },
    'NAW': {
      'players': demoData['WEEK_2']['NAW']['players'],
      'twitterTags': demoData['WEEK_2']['NAW']['twitterTags'],
      'playerInfos': demoData['WEEK_2']['NAW']['playerInfos']
    },
    'NAE': {
      'players': demoData['WEEK_2']['NAE']['players'],
      'twitterTags': demoData['WEEK_2']['NAE']['twitterTags'],
      'playerInfos': demoData['WEEK_2']['NAE']['playerInfos']
    }, 
  }
}

def populateDbs() -> None:
  print(f'[*] updating databases')
  for i in range(2):
    for serverRegion, region in zip(FN_COLLECTIONS, REGIONS):
      print(f'\n\n\t[*]WEEK_{i+1}\t-){region}')
      playerInfos = data[f'WEEK_{i+1}'][region]['playerInfos']
      twitterTags = data[f'WEEK_{i+1}'][region]['twitterTags']
      iTwitterTag = 0
      with alive_bar(len(playerInfos)) as bar:
        for player in playerInfos:
          if DB[serverRegion].count_documents({'usernames': player['name']}) == 1: #player already stored
            DB[serverRegion].update_one({ "usernames": player['name'] }, { "$push": {"pr": player['points'], 'rank': player['rank']}})
            iTwitterTag = iTwitterTag + 1
          else: #first player's record
            if (SequenceMatcher(None, twitterTags[iTwitterTag], player['name'].lower()).ratio() > 0.32): #check Twitter tag and username similatity
              if DB[serverRegion].count_documents({"twitter": twitterTags[iTwitterTag]}) == 1: #player already stored
                DB[serverRegion].update_one({ "twitter": twitterTags[iTwitterTag] }, { "$push": {"usernames": player['name'], "pr": player['points'], 'rank': player['rank']}})
              else: 
                DB[serverRegion].insert_one({'twitter': twitterTags[iTwitterTag], "usernames": [player['name']]})
                addNullRecords(twitterTags[iTwitterTag], player['points'], player['rank'], region)
                DB[serverRegion].update_one({ "twitter": twitterTags[iTwitterTag] }, { "$set": {"pr": [player['points']], 'rank': [player['rank']]}})
              iTwitterTag = iTwitterTag + 1
            else:
              print("\n\n'username-TwitterTag' similarity ratio: " , Decimal(SequenceMatcher(None, twitterTags[iTwitterTag], player['name'].lower()).ratio()).quantize(Decimal('.001'), rounding=ROUND_DOWN))
              twitterInput = input(f"""is '{twitterTags[iTwitterTag]}' {player['name']}'s Twitter tag? Is so, type 'y', otherwise enter his tag: """)
              if twitterInput == 'y':
                if DB[serverRegion].count_documents({"twitter": twitterTags[iTwitterTag]}) == 1: #player already stored
                  DB[serverRegion].update_one({ "twitter": twitterTags[iTwitterTag] }, { "$push": {"usernames": player['name'], "pr": player['points'], 'rank': player['rank']}})
                else:
                  DB[serverRegion].insert_one({'twitter': twitterTags[iTwitterTag], "usernames": [player['name']]})
                  addNullRecords(twitterTags[iTwitterTag], player['points'], player['rank'], region)
              else:
                if DB[serverRegion].count_documents({"twitter": twitterInput}) == 1: #player already stored
                  DB[serverRegion].update_one({ "twitter": twitterInput }, { "$push": {"usernames": player['name'], "pr": player['points'], 'rank': player['rank']}})
                else: 
                  DB[serverRegion].insert_one({'twitter': twitterInput, "usernames": [player['name']]})
                  addNullRecords(twitterInput, player['points'], player['rank'], region)
                  DB[serverRegion].update_one({ "twitter": twitterInput }, { "$set": {"pr": [player['points']], 'rank':[ player['rank']]}})
                  iTwitterTag = iTwitterTag -1
              iTwitterTag = iTwitterTag + 1
          bar()

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
