import SteamAPI
import WikipediaAPI
#import Database
import json
import pretty_errors
from currency_converter import CurrencyConverter

def writeJson(name, data):
    if not name.endswith('.json'):
        name += '.json'
    
    with open("files/" + name, 'w') as outfile:
        json.dump(data, outfile, indent=2)

def readJson(name):
    if not name.endswith('.json'):
        name += '.json'

    with open("files/" + name) as jsonFile:
        data = json.load(jsonFile)

    return data

def updateAllGames():
    global allGamesDetail

    allGames = readJson('All games')['response']['games']
    gameIndex = 0
    gamesMax = int(readJson('All games')['response']['game_count'])

    for game in allGames:
        gameIndex += 1

        appID = game['appid']

        if allGamesDetail.get(str(appID)) == None:  # If the key (appID) dues not exist
            app = SteamAPI.getAppDetail(appID)      # Get the app info form the Steam Store API

            #if app[str(appID)]['success'] == False:     # If the awnser from Steam was false remove the game from the all games list
            #    allGamesOld = readJson('All games')
            #    allGamesOld['response']['game_count'] -= 1
            #    gamesMax -= 1
            #    gameIndex -= 1
            #
            #    del allGamesOld['response']['games'][gameIndex - 1]
            #    writeJson('All games', allGamesOld)
            #    print(f'fail on game {game["name"]}')
            #else:
            allGamesDetail[appID] = app[str(appID)]

            print(f'({gameIndex:3}/{gamesMax}) | {str(app[str(appID)]["success"]):5} | {game["name"]} ')

            writeJson('All games detail', allGamesDetail)
        else:
            print(f'Skip {game["name"]}')

def convertCurrency(initialFormat, code, final_formatted):
    currencyList = readJson('currency')
    currency = CurrencyConverter()

    if code not in currencyList:
        print()
        print()
        print('Enter desimal value for', code, 'Final formatt:', final_formatted)
        newCode = int(input())
        
        currencyList[code] = newCode
        writeJson('Currency', currencyList)

    price = initialFormat/(10 ** currencyList[code])

    return {
        'price': price,
        'priceNOK': currency.convert(price, code, 'NOK')
    }

def createGame(newGameDetail):
    allGames = readJson("All games")["response"]["games"]
    allGamesLen = len(allGames)

    companyNames = readJson('companyNames')
    modifyNames = companyNames['modify']
    skipNames = companyNames['skip']
    failedNames = companyNames['failed']

    def addCompany(compName):
        oCompName = compName

        if compName not in newGameDetail['company']:
            if compName in modifyNames:
                compName = modifyNames[compName]
            elif compName in skipNames:
                return
            elif compName in failedNames:
                return

            print('Adding company')

            companyName = compName.replace(' ', '_')

            try:
                companyPage = WikipediaAPI.searchForWikiPage(companyName)
                companyData = WikipediaAPI.getWikiData(companyPage)

                newGameDetail['company'][oCompName] = companyData
            except:
                companyNames['failed'].append(oCompName)
                print('Failed to add company:', compName)

                writeJson('companyNames', companyNames)

    i = 0
    for game in allGames:
        if i == 1000:
            break

        appID = int(game["appid"])

        if str(appID) in newGameDetail['games']:
            if newGameDetail['games'][str(appID)]['developer'] == None:
                continue

            for developer in newGameDetail['games'][str(appID)]['developer']:
                addCompany(developer)
                
            for publicher in newGameDetail['games'][str(appID)]['publisher']:
                addCompany(publicher)


            print(f"{i:3}/{allGamesLen} | Skiping: {newGameDetail['games'][str(appID)]['name']}")
        else:
            gameDetail = SteamAPI.getAppDetail(appID)[str(appID)]
            
            if gameDetail['success'] == False:
                continue
            
            gameDetail = gameDetail['data']

            print(f"{i:3}/{allGamesLen} | Adding: {gameDetail['name']}")

            if "price_overview" in gameDetail:
                price = convertCurrency(gameDetail['price_overview']['initial'], gameDetail['price_overview']['currency'], gameDetail['price_overview']['final_formatted'])

            gameDict = {
                'name': gameDetail['name'],
                'gameType': gameDetail['type'],
                'developer': (gameDetail['developers']) if "developers" in gameDetail else None,
                'publisher': gameDetail['publishers'],
                'platforms': [key for key in gameDetail['platforms'] if gameDetail['platforms'][key] == True],
                'releaceDate': gameDetail['release_date']['date'].replace("\u00a0", " "),
                'categories': ([key['description'] for key in gameDetail['categories']]) if "description" in gameDetail else None,
                'genres': ([key['description'] for key in gameDetail['genres']]) if "genres" in gameDetail else None,
                'metacritic': gameDetail['metacritic']['score'] if "metacritic" in gameDetail else None,
                'price': {
                    'initial': gameDetail['price_overview']['initial'] if "price_overview" in gameDetail else None,
                    'final_formatted': price['price'] if "price_overview" in gameDetail else None,
                    "price_NOK": price['priceNOK'] if "price_overview" in gameDetail else None,
                    'currency': gameDetail['price_overview']['currency'] if "price_overview" in gameDetail else None
                },
                'recommendations': gameDetail['recommendations'] if "recommendations" in gameDetail else None,
                'numDLC': len(gameDetail['dlc']) if "dlc" in gameDetail else None,
                'controllerSupport': gameDetail['controller_support'] if "controller_support" in gameDetail else 'none'

            }
            
            newGameDetail['games'][appID] = gameDict

            if gameDict['developer'] != None:

                for developer in gameDict['developer']:
                    addCompany(developer)

            for publicher in gameDict['publisher']:
                addCompany(publicher)


        writeJson('allGamesDetail', newGameDetail)

        i += 1

    return newGameDetail    

#newGameDetail = dict()
#newGameDetail['games'] = dict()
#newGameDetail['company'] = dict()

#companyNames = dict()
#writeJson('All Games', SteamAPI.getOwnedGames())
newGameDetail = readJson('allGamesDetail')
writeJson('AllGamesDetail', createGame(newGameDetail))

# MySQL tutorial
# https://www.datacamp.com/community/tutorials/mysql-python