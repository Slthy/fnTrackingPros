def main():
  import os, requests
  from os.path import join, dirname
  from dotenv import load_dotenv
  
  dotenv_path = join(dirname(__file__), 'version')
  load_dotenv(dotenv_path)
  VERSION: str = os.environ['VERSION']
  print(f'fnTracking v{VERSION}')
  trnKey = input('Enter your TRN Api key: ')
  fn_db = input('Enter a name for the database: ')
  regions = []
  regions.append('EU') if ((input('Do you want to track EU players? y/n: ')) == 'y') else None
  regions.append('NAW') if ((input('Do you want to track NAW players? y/n: ')) == 'y') else None
  regions.append('NAE') if ((input('Do you want to track NAE players? y/n: ')) == 'y') else None
  regions.append('BR') if ((input('Do you want to track BR players? y/n: ')) == 'y') else None
  regions.append('ME') if ((input('Do you want to track ME players? y/n: ')) == 'y') else None
  regions.append('ASIA') if ((input('Do you want to track ASIA players? y/n: ')) == 'y') else None

  #check api key
  if (requests.get(f'https://api.fortnitetracker.com/v1/powerrankings/pc/NAE/Ninja', {'TRN-Api-Key': trnKey}).json() != {'message': 'Invalid authentication credentials'}):
    f = open(".env", "a")
    f.write(f"""TRN_API_KEY = "{trnKey}"\nFN_DB = "{fn_db}"\nREGIONS = {regions}\nFN_COLLECTIONS={[f'fn{region}players' for region in regions ]}""")
    f.close()
  else:
    print('Enter a valid TRA Api key.\nbye :)')

  from models import runModes
  #runModes('all')


if __name__ == "__main__":
  main()