import os, ast
from pymongo import MongoClient
from os.path import join, dirname
from dotenv import load_dotenv
from difflib import SequenceMatcher

from methods.populateDbs import getTop100orUnder_players, getTop100orUnder_twitterTags, safeGetPlayerInfos #type: ignore
from methods.utils import addNullRecords, fixUnderTop50 #type: ignore
from methods.getDiffs import getHighestPrGain, getHighestRankGain, getHighestRankLose, newLeader, top5Diffs #type: ignore

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

TRN_API_KEY: str = os.environ['TRN_API_KEY']
FN_DB: str = os.environ['FN_DB']
REGIONS = ast.literal_eval(os.environ.get("REGIONS")) # type: ignore
FN_COLLECTIONS = [f'fn{region}players' for region in REGIONS]
CLIENT = MongoClient('localhost', 27017) # type: MongoClient
DB = CLIENT[FN_DB]

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
        print(SequenceMatcher(None, twitterTags[iTwitterTag], playerInfos['name'].lower()).ratio())
        if (SequenceMatcher(None, twitterTags[iTwitterTag], playerInfos['name'].lower()).ratio() > 0.32): #check Twitter tag and username similatity
          if DB[serverRegion].count_documents({"twitter": twitterTags[iTwitterTag]}) == 1: #player already stored
            DB[serverRegion].update_one({ "twitter": twitterTags[iTwitterTag] }, { "$push": {"usernames": playerInfos['name'], "pr": playerInfos['points'], 'rank': playerInfos['rank']}})
          else: 
            DB[serverRegion].insert_one({'twitter': twitterTags[iTwitterTag], "usernames": [playerInfos['name']]})
            addNullRecords(twitterTags[iTwitterTag], playerInfos['points'], playerInfos['rank'], region)
            DB[serverRegion].update_one({ "twitter": twitterTags[iTwitterTag] }, { "$set": {"pr": [playerInfos['points']], 'rank': [playerInfos['rank']]}})
            print(playerInfos['name'] + f" (twitter: '{twitterTags[iTwitterTag]}') has entered in the top50 for the first time!")
          iTwitterTag = iTwitterTag + 1
        else:
          twitterInput = input(f"""is '{twitterTags[iTwitterTag]}' {playerInfos['name']}'s Twitter tag? Is so, type 'y', otherwise enter his tag: """)
          if twitterInput == 'y':
            if DB[serverRegion].count_documents({"twitter": twitterTags[iTwitterTag]}) == 1: #player already stored
              DB[serverRegion].update_one({ "twitter": twitterTags[iTwitterTag] }, { "$push": {"usernames": playerInfos['name'], "pr": playerInfos['points'], 'rank': playerInfos['rank']}})
            else:
              DB[serverRegion].insert_one({'twitter': twitterTags[iTwitterTag], "usernames": [playerInfos['name']]})
              addNullRecords(twitterTags[iTwitterTag], playerInfos['points'], playerInfos['rank'], region)
              print(playerInfos['name'] + f" (twitter: '{twitterTags[iTwitterTag]}') has entered in the top50 for the first time!")
          else:
            if DB[serverRegion].count_documents({"twitter": twitterInput}) == 1: #player already stored
              DB[serverRegion].update_one({ "twitter": twitterInput }, { "$push": {"usernames": playerInfos['name'], "pr": playerInfos['points'], 'rank': playerInfos['rank']}})
            else: 
              DB[serverRegion].insert_one({'twitter': twitterInput, "usernames": [playerInfos['name']]})
              addNullRecords(twitterInput, playerInfos['points'], playerInfos['rank'], region)
              DB[serverRegion].update_one({ "twitter": twitterInput }, { "$set": {"pr": [playerInfos['points']], 'rank':[ playerInfos['rank']]}})
              iTwitterTag = iTwitterTag -1
          iTwitterTag = iTwitterTag + 1

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
