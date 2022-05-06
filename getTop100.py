def main():
  import time
  from models import getTop100orUnder, getProData

  entries = 100
  top100_PRplayers = getTop100orUnder('pc', 'EU', 'year', 100)

  for index, player in zip(range(entries), top100_PRplayers):
      print(index, player)
      playerInfos = getProData('pc', 'EU', player)
      print(playerInfos == """{"message":"API rate limit exceeded"}""")
      if playerInfos == """{"message":"API rate limit exceeded"}""":
        print('\tAPI rate limit exceeded...')
        time.sleep(61)
        print('\r...resuming')
        playerInfos = getProData('pc', 'EU', player)
      print(f'{playerInfos}\n')

if __name__ == "__main__":
  main()