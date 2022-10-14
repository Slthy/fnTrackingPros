import os, requests, re
from os.path import join, dirname
from dotenv import load_dotenv

version_path = join(dirname(__file__), 'version')
load_dotenv(version_path)
VERSION: str = os.environ['VERSION']
print(f'fnTracking v{VERSION}')
trnKey = input('Enter your TRN Api key: ')
fn_db = input('Enter a name for the database: ')

#get user's region preferences
regions = []
regions.append('EU') if ((input('Do you want to track EU players? y/n: ')) == 'y') else None
regions.append('NAW') if ((input('Do you want to track NAW players? y/n: ')) == 'y') else None
regions.append('NAE') if ((input('Do you want to track NAE players? y/n: ')) == 'y') else None
regions.append('BR') if ((input('Do you want to track BR players? y/n: ')) == 'y') else None
regions.append('ME') if ((input('Do you want to track ME players? y/n: ')) == 'y') else None
regions.append('ASIA') if ((input('Do you want to track ASIA players? y/n: ')) == 'y') else None

#check trn_api_key
regexValidationPattern = "\{'region': 'NAE', 'name': 'Ninja', 'platform': 'PC', 'points': [0-9]+, 'cashPrize': [0-9]*\.[0-9]+, 'events': [0-9]+, 'rank': [0-9]+, 'percentile': [0-9]*\.[0-9]+, 'countryCode': 'US', 'twitter': 'Ninja'\}"
key_validity_response = requests.get(f'https://api.fortnitetracker.com/v1/powerrankings/pc/NAE/Ninja', {'TRN-Api-Key': trnKey})
if re.fullmatch(regexValidationPattern, str(key_validity_response.json())):
  with open(".env", "a") as f:
    f.write(f"""TRN_API_KEY = "{trnKey}"\nFN_DB = "{fn_db}"\nREGIONS = {regions}""") 
elif key_validity_response.json()["message"] == "Invalid authentication credentials":
  print('Enter a valid TRA Api key.\nbye :)') 
else:
  print(f'unrecognized error, status code: {key_validity_response.status_code} - {key_validity_response.json()}')
