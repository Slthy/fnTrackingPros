# Presentazione progetto "fnTrackingPros"

### Borsato Alessandro

<hr>

## Scopo del progetto:

Il progetto ha come obiettivo quello di **ricevere**, **immagazzinare** ed **elaborare** dati attraverso l'uso di **API** esterne e **database**. In questo caso, gli script andranno a richiedere dati inerenti i risultati ottenuti dai vari proplayer del videogame "Fortnite", andandoli ad analizzare settimanalmente.
<br>

## Risorse utilizzate:

Il progetto è stato interamente realizzato in `Python` con l'uso del database non relazionale `MongoDB` per lo storage dei dati.

* ### Perchè Python:
    Inizialmente, il progetto era incentrato sull'**esplorazione** di un linguaggio utilizzato prima. Python si è riveltato un ottimo linguaggio per questo tipo di script, anche per grazie la vastità di **moduli** esterni utilizzabili.
    
* ### Perchè MongoDB:
    La scelta di un database **non relazionale orientato ad documenti** è stata dettata dalla natura stessa del progetto: andando ad aggiornare settimanalmente i dati immagazzinati, non è possibile stabilire a monte una struttura fissa per i dati salvati.<br>
    Ecco lo schema dei documenti salvati nel database:
     ```json    
     {
        "_id": id,
        "twitter": String,
        "usernames": Array[ String ],
        "pr": Array [ Int32 ],
        "rank": Array [ Int32 ]
    }
    ``` 
    Esempio di un documento salvato nel database
    ```json    
     { 
         "_id": { "oid": "6291c66c56b6868cafb89d99"} ,  
         "twitter": "taysonFN",  
         "usernames": [ "Falcon TaySon 7" ],  
         "pr": [ 175894, 181776 ],  
         "rank": [ 1, 1 ]
     }
    ```

## Modalità d'uso:

Ogni settimana, lo script ottiene gli `username` dei giocatori rientrati nella top50 della relativa regione.<br>
La configurazione delle chiavi API e delle ulteriori preferenze selezionabili avviene attraverso lo script `setup.py`, mentre è possibile aggiustare in caso di bisogno il database attraverso lo script `helper.py`<br>
Dopo aver configurato correttamente le variabili ambientali necessarie per il funzionamento degli script, è possibile avviare lo script principale `run.py`, scegliendo tra le tre modalità di esecuzione possibili:
   * `updateDbs`:
       Richiede i dati dei giocatori nella top50 della settimana corrente, immagazzinandoli nel database.
   * `getDiffs`:
       Elabora i dati a disposizione e ne restituisce i risultati:
       - `getHighestPrGain`
       - `getHighestRankGain`
       - `getHighestRankLose`
       - `top5Diffs`
       - `newLeader`

<hr>

## Raccolta dati:

### populateDbs():
```python 
def populateDbs() -> None:
  print(f'[*] updating databases')
  for serverRegion, region in zip(FN_COLLECTIONS, REGIONS):
1)  players = getTop100orUnder_players(region, 50)
2)  twitterTags = getTop100orUnder_twitterTags(region, 50)
3)  iTwitterTag = 0
    for player in players:
      playerInfos = safeGetPlayerInfos(region, player)
      if 'username' is in DB: #player already stored
        aggiorna documento
4)      iTwitterTag = iTwitterTag + 1
      else: #first player's record
        if 'username' is similar to 'twitterTag':
          if 'twitterTag' is in DB:: #player already stored
            #Il giocatore ha già un proprio 'documento', ma ha cambiato username
            aggiorna documento
          else: 
            #il giocatore non ha un documento
            crea documento
            aggiungi valori nulli (0) prima della settimana corrente
4)        iTwitterTag = iTwitterTag + 1
        else: #il tag Twitter ottenuto non è simile allo username del giocatore
          #chiedi all'utente di verificare che lo username corrisponda al tag Twitter
          if twitterInput == 'y':
            if 'twitterTag' is in DB: #Il giocatore ha già un proprio 'documento', ma ha cambiato username
              update document
            else:
              #il giocatore non ha un documento
              crea documento
              aggiungi valori nulli (0) prima della settimana corrente
          else:
            if 'twitterInput' is in DB: #player already stored
              update document
            else: 
              #il giocatore non ha un documento
              crea documento
              aggiungi valori nulli (0) prima della settimana corrente
5)          iTwitterTag = iTwitterTag -1
4)        iTwitterTag = iTwitterTag + 1
```

Al punto `1` vengono richiesti all'api i dati relativi ai piazzamenti dei giocatori.<br>
Al punto `2` vengono ricavati dalla pagina frontend dell'api i primi 50 tag Twitter presenti nella pagina. I dati vengono salvati in un array.<br>
Come si può notare, viene data una particolare attenzione ai all'assegnazione dei tag twitter ai dati dei giocatori. Nelle collezioni vengono prese come "chiavi" proprio gli username Twitter dei giocatori in quanto ogni player ha solo un account twitter. Per facilitare l'iterazione lungo l'array `twitterTags`, al punto `3` vine inizializzato e dichiarato un iteratore (`itwitterTags`). Solamente i casi nei quali il tag twitter corrisponde allo username corrente faranno aumentare l'iteratore (`3`). I casi nei quali è l'utente ad inserire il tagTwitter corretto, l'iteratore viene fatto diminuire di uno (`4`) per poi farlo scalare a fine iterazione, facendolo rimanere quindi allo stesso valore di inizio ciclo.<br><br>

<hr><br>

## Elaborazione dati:

### getHighestPrGain():
Restituisce i dati relativi al giocatore che ha acquisito il maggior numero punti `PowerRanking` della regione corrente


```python
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
```

### getHighestRankGain():
Restituisce i dati relativi al giocatore che ha acquisito il maggior numero posizioni nella classifica `PowerRanking` della regione corrente


```python
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
```

### getHighestRankLose():
Restituisce i dati relativi al giocatore che ha perso il maggior numero posizioni nella classifica `PowerRanking`


```python
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
```

### top5Diffs():
Restituisce dati relativi ai cambiamenti avvenuti nella top5 della classifica `PowerRanking` della regione corrente


```python
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
      if ((currentWeek := DB[f"fn{region}players"].find_one({'usernames' : lastWeek[f'top{index+1}']['usernames'][-1]})) is not None) and ((previousWeek := DB[f"fn{region}players"].find_one({'usernames' : lastWeek[f'top{index+1}']['usernames'][-1]})) is not None):
        currentWeekRank = currentWeek['rank'][-1]
        previousWeekRank = previousWeek['rank'][-2]
        #print(currentWeekRank, previousWeekRank)
        if currentWeekRank != previousWeekRank:
          results[f'top{index+1}'] = {
            'twitter': lastWeek[f'top{index+1}']['twitter'],
            'playerlastWeekRank': previousWeekRank
          }
      else:
        raise Exception
  return results
```

### newLeader():
Restituisce i dati relativi al primo player nella classifica `PowerRanking` nel caso nell'ultima settimana si fossero verificati cambiamenti al vertice.


```python
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
```
