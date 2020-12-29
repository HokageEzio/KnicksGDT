import praw
import requests
import traceback
import bs4
import re
import random
from apscheduler.schedulers.blocking import BlockingScheduler
import json
from datetime import date, timedelta, datetime
import config
import logging

sched = BlockingScheduler({'apscheduler.timezone': 'UTC'})
#logging.basicConfig()
#logging.getLogger('apscheduler').setLevel(logging.DEBUG)

# Team Dictionary helps to make urls for boxscore and for full-forms of abbrevation of teams
teamDict = {
    "ATL": ["Atlanta Hawks", "01", "atlanta-hawks-",
            "/r/atlantahawks", "1610612737", "Hawks"],
    "BKN": ["Brooklyn Nets", "17", "brooklyn-nets-",
            "/r/gonets", "1610612751", "Nets"],
    "BOS": ["Boston Celtics", "02", "boston-celtics-",
            "/r/bostonceltics", "1610612738", "Celtics"],
    "CHA": ["Charlotte Hornets", "30", "charlotte-hornets-",
            "/r/charlottehornets", "1610612766", "Hornets"],
    "CHI": ["Chicago Bulls", "04", "chicago-bulls-",
            "/r/chicagobulls", "1610612741", "Bulls"],
    "CLE": ["Cleveland Cavaliers", "05", "cleveland-cavaliers-",
            "/r/clevelandcavs", "1610612739", "Cavaliers"],
    "DAL": ["Dallas Mavericks", "06", "dallas-mavericks-",
            "/r/mavericks", "1610612742", "Mavericks"],
    "DEN": ["Denver Nuggets", "07", "denver-nuggets-",
            "/r/denvernuggets", "1610612743", "Nuggets"],
    "DET": ["Detroit Pistons", "08", "detroit-pistons-",
            "/r/detroitpistons", "1610612765", "Pistons"],
    "GSW": ["Golden State Warriors", "09", "golden-state-warriors-",
            "/r/warriors", "1610612744", "Warriors"],
    "HOU": ["Houston Rockets", "10", "houston-rockets-",
            "/r/rockets", "1610612745", "Rockets"],
    "IND": ["Indiana Pacers", "11", "indiana-pacers-",
            "/r/pacers", "1610612754", "Pacers"],
    "LAC": ["Los Angeles Clippers", "12", "los-angeles-clippers-",
            "/r/laclippers", "1610612746", "Clippers"],
    "LAL": ["Los Angeles Lakers", "13", "los-angeles-lakers-",
            "/r/lakers", "1610612747", "Lakers"],
    "MEM": ["Memphis Grizzlies", "29", "memphis-grizzlies-",
            "/r/memphisgrizzlies", "1610612763", "Grizzlies"],
    "MIA": ["Miami Heat", "14", "miami-heat-",
            "/r/heat", "1610612748", "Heat"],
    "MIL": ["Milwaukee Bucks", "15", "milwaukee-bucks-",
            "/r/mkebucks", "1610612749", "Bucks"],
    "MIN": ["Minnesota Timberwolves", "16", "minnesota-timberwolves-",
            "/r/timberwolves", "1610612750", "Timberwolves"],
    "NOP": ["New Orleans Pelicans", "03", "new-orleans-pelicans-",
            "/r/nolapelicans", "1610612740", "Pelicans"],
    "NYK": ["New York Knicks", "18", "new-york-knicks-",
            "/r/nyknicks", "1610612752", "Knicks"],
    "OKC": ["Oklahoma City Thunder", "25", "oklahoma-city-thunder-",
            "/r/thunder", "1610612760", "Thunder"],
    "ORL": ["Orlando Magic", "19", "orlando-magic-",
            "/r/orlandomagic", "1610612753", "Magic"],
    "PHI": ["Philadelphia 76ers", "20", "philadelphia-76ers-",
            "/r/sixers", "1610612755", "76ers"],
    "PHX": ["Phoenix Suns", "21", "phoenix-suns-",
            "/r/suns", "1610612756", "Suns"],
    "POR": ["Portland Trail Blazers", "22", "portland-trail-blazers-",
            "/r/ripcity", "1610612757", "Trail Blazers"],
    "SAC": ["Sacramento Kings", "23", "sacramento-kings-",
            "/r/kings", "1610612758", "Kings"],
    "SAS": ["San Antonio Spurs", "24", "san-antonio-spurs-",
            "/r/nbaspurs", "1610612759", "Spurs"],
    "TOR": ["Toronto Raptors", "28", "toronto-raptors-",
            "/r/torontoraptors", "1610612761", "Raptors"],
    "UTA": ["Utah Jazz", "26", "utah-jazz-",
            "/r/utahjazz", "1610612762", "Jazz"],
    "WAS": ["Washington Wizards", "27", "washington-wizards-",
            "/r/washingtonwizards", "1610612764, ", "Wizards"],
    "ADL": ["Adelaide 36ers", "00", "adelaide-36ers",
            "/r/nba", "15019"],
    "SLA": ["Buenos Aires San Lorenzo", "00", "buenos-aires-san-lorenzo",
            "/r/nba", "12330"],
    "FRA": ["Franca Franca", "00", "franca-franca",
            "/r/nba", "12332"],
    "GUA": ["Guangzhou Long-Lions", "00", "guangzhou-long-lions",
            "/r/nba", "15018"],
    "MAC": ["Haifa Maccabi Haifa", "00", "haifa-maccabi-haifa",
            "/r/nba", "93"],
    "MEL": ["Melbourne United", "00", "melbourne-united",
            "/r/nba", "15016"],
    "NZB": ["New Zealand Breakers", "00", "new-zealand-breakers",
            "/r/nba", "15020"],
    "SDS": ["Shanghai Sharks", "00", "shanghai-sharks",
            "/r/nba", "12329"]
}

# getting a reddit instance by giving appropiate credentials
reddit = praw.Reddit(
    username=config.username,
    password=config.password,
    client_id=config.client_id,
    client_secret=config.client_secret,
    user_agent="script:rnba-game-thread-bot:v2.0 (by /u/f1uk3r)")

#change it to "nyknicks" for update on main subreddit
sub = "knicklejerk"

def requestApi(url):
    req = requests.get(url)
    return req.json()


def requestSoup(url):
    req = requests.get(url)
    soup = bs4.BeautifulSoup(req.text, 'html.parser')
    return soup
    
def appendPlusMinus(someStat):
    """
    someStat is any stat
    appendPlusMinus just appends sign in front of stat in question 
    and returns it
    """
    if someStat.isdigit():
        if int(someStat) > 0:
            return "+" + str(someStat)
        return str(someStat)
    else:
        return str(someStat)

#game thread fuctions starts from here
def initialGameThreadText(basicGameData, date, teamDict, dateTitle):
    """
    Variable basicGameData have live data
    Variable date is today's date
    Variable teamDict is the variable Dictionary at the top
    Function beforeGamePost setups the body of the thread before game starts
    and return body and title of the post
    """
    try:
        timeEasternRaw = basicGameData["startTimeEastern"]
        timeOnlyEastern = timeEasternRaw[:5]
        if timeOnlyEastern[:2].isdigit():
            timeEasternHour = int(timeOnlyEastern[:2])
            timeMinute = timeOnlyEastern[3:]
        else:
            timeEasternHour = int(timeOnlyEastern[:1])
            timeMinute = timeOnlyEastern[2:]
        timeCentralHourFinal = timeEasternHour - 1
        timeMountainHourFinal = timeCentralHourFinal - 1
        broadcasters = basicGameData['watch']['broadcast']['broadcasters']
        if broadcasters['national']==[]:
            nationalBroadcaster = "-"
        else:
            nationalBroadcaster = broadcasters['national'][0]['shortName']
        if basicGameData['hTeam']['triCode'] == "NYK":
            knicksBroadcaster = broadcasters['hTeam'][0]['shortName']
            otherBroadcaster = broadcasters['vTeam'][0]['shortName']
            otherSubreddit = teamDict[basicGameData["vTeam"]["triCode"]][3]
            homeAwaySign = "vs"
            knicksWinLossRecord = f"({basicGameData['hTeam']['win']}-{basicGameData['hTeam']['loss']})"
            otherWinLossRecord = f"({basicGameData['vTeam']['win']}-{basicGameData['vTeam']['loss']})"
            otherTeamName = teamDict[basicGameData["vTeam"]["triCode"]][0]
        else:
            knicksBroadcaster = broadcasters['vTeam'][0]['shortName']
            otherBroadcaster = broadcasters['hTeam'][0]['shortName']
            otherSubreddit = teamDict[basicGameData["hTeam"]["triCode"]][3]
            homeAwaySign = "@"
            knicksWinLossRecord = f"({basicGameData['vTeam']['win']}-{basicGameData['vTeam']['loss']})"
            otherWinLossRecord = f"({basicGameData['hTeam']['win']}-{basicGameData['hTeam']['loss']})"
            otherTeamName = teamDict[basicGameData["hTeam"]["triCode"]][0]
        nbaGameThreadLink =""
        for submission in (reddit.subreddit('nba').search("game thread", sort="new", time_filter="day")):
            if f"GAME THREAD: {teamDict[basicGameData['vTeam']['triCode']][0]}" in submission.title and teamDict[basicGameData['hTeam']['triCode']][0] in submission.title:
                nbaGameThreadLink = submission.url
    

        beforeGameBody = f"""##General Information
    **TIME**     |**BROADCAST**                            |**Location and Subreddit**        |
    :------------|:------------------------------------|:-------------------|
    {timeEasternHour}:{timeMinute} PM Eastern |{knicksBroadcaster}|{basicGameData["arena"]["name"]}| 
    {timeCentralHourFinal}:{timeMinute} PM Central |{otherBroadcaster}|{otherSubreddit}|
    {timeMountainHourFinal}:{timeMinute} PM Mountain|{nationalBroadcaster}|r/nba|

-----
[r/NBA Game Thread]({nbaGameThreadLink})


"""

        title = f"[Game Thread] The New York Knicks {knicksWinLossRecord} {homeAwaySign} The {otherTeamName} {otherWinLossRecord} - ({dateTitle})"
        return beforeGameBody, title
    except:
        return "", ""


def createGameThread(dateToday, gameId):
    dateTitle = datetime.utcnow().strftime("%B %d, %Y")
    dataBoxScore = requestApi("http://data.nba.net/prod/v1/" + dateToday
                              + "/" + gameId + "_boxscore.json")
    basicGameData = dataBoxScore["basicGameData"]
    bodyPost, title = initialGameThreadText(basicGameData, dateToday, teamDict, dateTitle)
    if bodyPost == "" or title == "":
        sched.add_job(createGameThread, args=[dateToday, gameId], run_date=datetime.utcnow() + timedelta(minutes=1))
    else:
        response = reddit.subreddit(sub).submit(title, selftext=bodyPost, send_replies=False)
        response.mod.distinguish(how="yes")
        response.mod.sticky()
        sched.add_job(updateGameThread, 'date', run_date=datetime.utcnow() + timedelta(minutes=60), max_instances=15,
                      args=[gameId, dateToday, bodyPost], kwargs={'response': response})
        print(gameId + " thread created")


def updateGameThread(gameId, dateToday, bodyPost, response=None):
    dataBoxScore = requestApi("http://data.nba.net/prod/v1/" + dateToday + "/" + gameId + "_boxscore.json")
    try:
        response.edit(boxScoreText(dataBoxScore, bodyPost, dateToday, teamDict))
    except Exception:
        traceback.print_exc()
    if checkIfGameIsFinished(gameId, dateToday):
        print(gameId + " game finished")
    else:
        sched.add_job(updateGameThread, 'date', run_date=datetime.utcnow() + timedelta(minutes=1), max_instances=15,
                      args=[gameId, dateToday, bodyPost], kwargs={'response': response})
        print(gameId + " thread edited")


def checkIfGameIsFinished(gameId, dateToday):
    dataBoxScore = requestApi("http://data.nba.net/prod/v1/" + dateToday + "/" + gameId + "_boxscore.json")
    basicGameData = dataBoxScore["basicGameData"]
    if ((basicGameData["clock"] == "0.0" or basicGameData["clock"] == "")
            and basicGameData["period"]["current"] >= 4
            and (basicGameData["vTeam"]["score"] != basicGameData["hTeam"]["score"])):
        return True
    else:
        return False


def processGameThread():
    knicksSchedule = requestApi("http://data.nba.net/prod/v1/2020/teams/1610612752/schedule.json")
    allKnicksGames = knicksSchedule["league"]["standard"]
    for i in range(len(allKnicksGames)):
        if i < len(allKnicksGames)-1:
            if (allKnicksGames[i]["vTeam"]["score"] == "" and allKnicksGames[i]["hTeam"]["score"] == ""):
                startTime = datetime.strptime(allKnicksGames[i]["startTimeUTC"][:19],'%Y-%m-%dT%H:%M:%S') - timedelta(minutes=45)
                startTimeNextGame = datetime.strptime(allKnicksGames[i+1]["startTimeUTC"][:19],'%Y-%m-%dT%H:%M:%S') - timedelta(hours=2)
                sched.add_job(createGameThread, args=[allKnicksGames[i]['startDateEastern'], allKnicksGames[i]['gameId']], run_date=startTime)
                sched.add_job(processGameThread, run_date=startTimeNextGame)
                break
        else:
            if (allKnicksGames[i]["vTeam"]["score"] == "" and allKnicksGames[i]["hTeam"]["score"] == ""):
                startTime = datetime.strptime(allKnicksGames[i]["startTimeUTC"][:19],'%Y-%m-%dT%H:%M:%S') - timedelta(minutes=45)
                sched.add_job(createGameThread, args=[allKnicksGames[i]['startDateEastern'], allKnicksGames[i]['gameId']], run_date=startTime)
    print("processGameThread() is scheduled to run tomorrow")

def createTitleOfPostGameThread(dateToday, gameId):
    defeatSynonyms = ['defeat', 'beat', 'triumph over', 'blow out', 'level out', 'destroy', 'crush', 'walk all over', 'exterminate', 'slaughter', 'massacre' 'obliterate', 'eviscerate', 'annihilate', 'edge out', 'steal one against', 'hang on to defeat', 'snap']
    dataBoxScore = requestApi("http://data.nba.net/prod/v1/" + dateToday + "/" + gameId + "_boxscore.json")
    basicGameData = dataBoxScore["basicGameData"]
    visitorTeamScore = basicGameData["vTeam"]["score"]
    homeTeamScore = basicGameData["hTeam"]["score"]
    if (basicGameData['hTeam']['triCode'] == "NYK" and homeTeamScore > visitorTeamScore) or (basicGameData['vTeam']['triCode'] == "NYK" and homeTeamScore < visitorTeamScore):
        if (abs(int(visitorTeamScore)-int(homeTeamScore))<3):
            defeatWord = random.choice(defeatSynonyms[14:16])
        elif (abs(int(visitorTeamScore)-int(homeTeamScore))<6):
            defeatWord = random.choice(defeatSynonyms[16:])
        elif (abs(int(visitorTeamScore)-int(homeTeamScore))>20):
            defeatWord = random.choice(defeatSynonyms[3:9])
        elif (abs(int(visitorTeamScore)-int(homeTeamScore))>40):
            defeatWord = random.choice(defeatSynonyms[9:14])
        else:
            defeatWord = random.choice(defeatSynonyms[:3])
    else:
        defeatWord = random.choice(defeatSynonyms[:3])
    print(defeatWord)

    #when game is activated, win-loss fields aren't updated. Check isGameActivated and update win-loss manually.
    if basicGameData["isGameActivated"] == False:
        visitorTeam = teamDict[basicGameData["vTeam"]["triCode"]][0] + " (" + basicGameData["vTeam"]["seriesWin"] + "-" + basicGameData["vTeam"]["seriesLoss"] + ")"
        homeTeam = teamDict[basicGameData["hTeam"]["triCode"]][0] + " (" + basicGameData["hTeam"]["seriesWin"] + "-" + basicGameData["hTeam"]["seriesLoss"] + ")"
    elif basicGameData["isGameActivated"] == True and ((int(visitorTeamScore) > int(homeTeamScore)) and len(basicGameData["vTeam"]["linescore"])>=4):
        visitorTeam = teamDict[basicGameData["vTeam"]["triCode"]][0] + " (" + str(int(basicGameData["vTeam"]["seriesWin"])+1) + "-" + basicGameData["vTeam"]["seriesLoss"] + ")"
        homeTeam = teamDict[basicGameData["hTeam"]["triCode"]][0] + " (" + basicGameData["hTeam"]["seriesWin"] + "-" + str(int(basicGameData["hTeam"]["seriesLoss"])+1) + ")"
    elif basicGameData["isGameActivated"] == True and ((int(visitorTeamScore) < int(homeTeamScore)) and len(basicGameData["vTeam"]["linescore"])>=4):
        visitorTeam = teamDict[basicGameData["vTeam"]["triCode"]][0] + " (" + basicGameData["vTeam"]["seriesWin"] + "-" + str(int(basicGameData["vTeam"]["seriesLoss"])+1) + ")"
        homeTeam = teamDict[basicGameData["hTeam"]["triCode"]][0] + " (" + str(int(basicGameData["hTeam"]["seriesWin"])+1) + "-" + basicGameData["hTeam"]["seriesLoss"] + ")"
    print(visitorTeam, homeTeam)

    #title is created here, 
    if (int(visitorTeamScore) > int(homeTeamScore)) and len(basicGameData["vTeam"]["linescore"])==4:
        title = f"[Post Game Thread] The {visitorTeam} {defeatWord} the {homeTeam}, {visitorTeamScore}-{homeTeamScore}"
    elif (int(visitorTeamScore) > int(homeTeamScore)) and len(basicGameData["vTeam"]["linescore"])==5:
        title = f"[Post Game Thread] The {visitorTeam} {defeatWord} the {homeTeam} in OT, {visitorTeamScore}-{homeTeamScore}"
    elif (int(visitorTeamScore) > int(homeTeamScore)) and len(basicGameData["vTeam"]["linescore"])>5:
        title = f"[Post Game Thread] The {visitorTeam} {defeatWord} the {homeTeam} in {len(basicGameData['vTeam']['linescore'])-4}OTs, {visitorTeamScore}-{homeTeamScore}"
    elif (int(visitorTeamScore) < int(homeTeamScore)) and len(basicGameData["vTeam"]["linescore"])==4:
        title = f"[Post Game Thread] The {homeTeam} {defeatWord} the visiting {visitorTeam}, {homeTeamScore}-{visitorTeamScore}"
    elif (int(visitorTeamScore) < int(homeTeamScore)) and len(basicGameData["vTeam"]["linescore"])==5:
        title = f"[Post Game Thread] The {homeTeam} {defeatWord} the visiting {visitorTeam} in OT, {homeTeamScore}-{visitorTeamScore}"
    elif (int(visitorTeamScore) < int(homeTeamScore)) and len(basicGameData["vTeam"]["linescore"])>5:
        title = f"[Post Game Thread] The {homeTeam} {defeatWord} the visiting {visitorTeam} in {len(basicGameData['vTeam']['linescore'])-4}OTs, {homeTeamScore}-{visitorTeamScore}"
    print(title)
    return(title)

def createPostGameThread(dateToday, gameId):
    boxScoreData = requestApi("http://data.nba.net/prod/v1/" + dateToday + "/" + gameId + "_boxscore.json")
    body = boxScoreText(boxScoreData, '', dateToday, teamDict)
    title = createTitleOfPostGameThread(dateToday, gameId)
    if body == "" or title == "":
        sched.add_job(createPostGameThread, args=[dateToday, gameId], run_date=datetime.utcnow() + timedelta(minutes=1))
    else:
        response = reddit.subreddit(sub).submit(title, selftext=body, send_replies=False)
        print(gameId + " Post game thread created")
    return response

def checkGameStatusForPGT(dateToday, gameId):
    if checkIfGameIsFinished(gameId, dateToday):
        sched.add_job(createPostGameThread, 'date', run_date=datetime.utcnow() + timedelta(minutes=1), args=[dateToday, gameId])
    else:
        sched.add_job(checkGameStatusForPGT, 'date', run_date=datetime.utcnow() + timedelta(minutes=1), max_instances=15, args=[dateToday, gameId])
    print("pgt status checked")

def processPostGameThread():
    knicksSchedule = requestApi("http://data.nba.net/prod/v1/2020/teams/1610612752/schedule.json")
    allKnicksGames = knicksSchedule["league"]["standard"]
    for i in range(len(allKnicksGames)):
        if i < len(allKnicksGames)-1:
            if (allKnicksGames[i]["vTeam"]["score"] == "" and allKnicksGames[i]["hTeam"]["score"] == ""):
                startTime = datetime.strptime(allKnicksGames[i]["startTimeUTC"][:19],'%Y-%m-%dT%H:%M:%S') + timedelta(minutes=90)
                startTimeNextGame = datetime.strptime(allKnicksGames[i+1]["startTimeUTC"][:19],'%Y-%m-%dT%H:%M:%S') - timedelta(hours=2)
                sched.add_job(checkGameStatusForPGT, args=[allKnicksGames[i]['startDateEastern'], allKnicksGames[i]['gameId']], run_date=startTime)
                sched.add_job(processPostGameThread, run_date=startTimeNextGame)
                break
        else:
            if (allKnicksGames[i]["vTeam"]["score"] == "" and allKnicksGames[i]["hTeam"]["score"] == ""):
                startTime = datetime.strptime(allKnicksGames[i]["startTimeUTC"][:19],'%Y-%m-%dT%H:%M:%S') - timedelta(minutes=45)
                sched.add_job(checkGameStatusForPGT, args=[allKnicksGames[i]['startDateEastern'], allKnicksGames[i]['gameId']], run_date=startTime)

def get_game_thread_westchester(basicGameData, gLeagueTeamDict, dateTitle):
    """
    Variable basicGameData have live data
    Variable teamDict is the variable Dictionary at the top
    Function beforeGamePost setups the body of the thread before game starts
    and return body and title of the post
    """
    try:
        timeEastern = datetime.strptime(basicGameData["etm"],'%Y-%m-%dT%H:%M:%S')
        timeCentral = timeEastern - timedelta(1)
        timeMountain = timeCentral - timedelta(1)
        broadcasters = basicGameData['bd']['b']
        if len(broadcaster) == 1:
            knicksBroadcaster = broadcasters[0]["disp"]
            otherBroadcaster = "-"
            nationalBroadcaster = "-"
        elif len(broadcasters) == 2:
            knicksBroadcaster = broadcasters[0]["disp"]
            otherBroadcaster = broadcasters[1]["disp"]
            nationalBroadcaster = "-"
        elif len(broadcasters) == 3:
            knicksBroadcaster = broadcasters[0]["disp"]
            otherBroadcaster = broadcasters[1]["disp"]
            nationalBroadcaster = broadcasters[2]['disp']
        elif len(broadcaster) == 0:
            knicksBroadcaster = "-"
            otherBroadcaster = "-"
            nationalBroadcaster = "-"
        if basicGameData['h']['ta'] == "WES":
            homeAwaySign = "vs"
            knicksWinLossRecord = f"({basicGameData['h']['re']})"
            otherWinLossRecord = f"({basicGameData['v']['re']})"
            otherTeamName = gLeagueTeamDict[basicGameData["v"]["ta"]][0]
        else:
            homeAwaySign = "@"
            knicksWinLossRecord = f"({basicGameData['v']['re']})"
            otherWinLossRecord = f"({basicGameData['hTeam']['re']})"
            otherTeamName = gLeagueTeamDict[basicGameData["hTeam"]["triCode"]][0]

        beforeGameBody = f"""##General Information
    **TIME**     |**BROADCAST**                            |**Location and Subreddit**        |
    :------------|:------------------------------------|:-------------------|
    {timeEastern.strftime("%I:%M %p")} Eastern |{knicksBroadcaster}|{basicGameData["an"]}| 
    {timeCentral.strftime("%I:%M %p")} Central |{otherBroadcaster}|-|
    {timeMountain.strftime("%I:%M %p")} Mountain|{nationalBroadcaster}|r/nba|

    -----
    [Reddit Stream](https://reddit-stream.com/comments/auto) (You must click this link from the comment page.)
    """

        title = f"[Game Thread] The Westchester Knicks {knicksWinLossRecord} {homeAwaySign} The {otherTeamName} {otherWinLossRecord} - ({dateTitle})"

        return beforeGameBody, title
    except:
        return "", ""

def create_westchester_game_thread(basicGameData):
    gameDate = datetime.strptime(basicGameData["etm"],'%Y-%m-%dT%H:%M:%S')
    dateTitle = gameDate.strftime("%B %d, %Y")
    bodyPost, title = get_game_thread_westchester(basicGameData, gLeagueTeamDict, dateTitle)
    if bodyPost == "" or title == "":
        sched.add_job(createGameThread, args=[basicGameData], run_date=datetime.utcnow() + timedelta(minutes=1))
    else:
        response = reddit.subreddit('nyknicks').submit(title, selftext=bodyPost, send_replies=False)
        print("westchester game thread created")


#def process_westchester_game_thread():
    westchesterSchedule = requestApi("https://s.data.nba.com/data/10s/v2015/json/mobile_teams/dleague/2020/teams/knicks_schedule.json")
    allWestchesterGames = westchesterSchedule["gscd"]["g"]
    for i in range(len(allWestchesterGames)):
        if i < len(allWestchesterGames)-1:
            if (allWestchesterGames[i]["v"]["s"] == "" and allWestchesterGames[i]["h"]["s"] == ""):
                startTime = datetime.strptime(allWestchesterGames[i]["etm"],'%Y-%m-%dT%H:%M:%S') + timedelta(hours=4)
                startTimeNextGame = datetime.strptime(allWestchesterGames[i+1]["etm"],'%Y-%m-%dT%H:%M:%S') + timedelta(hours=3)
                sched.add_job(create_westchester_game_thread, args=[allWestchesterGames[i]], run_date=startTime)
                sched.add_job(process_westchester_game_thread, run_date=startTimeNextGame)
                break
        else:
            if (allWestchesterGames[i]["v"]["s"] == "" and allWestchesterGames[i]["h"]["s"] == ""):
                startTime = datetime.strptime(allWestchesterGames[i]["etm"],'%Y-%m-%dT%H:%M:%S') + timedelta(hours=4)
                sched.add_job(create_westchester_game_thread, args=[allWestchesterGames[i]], run_date=startTime)
    print("process_westchester_game_thread() is scheduled to run tomorrow")


sched.add_job(processGameThread)
#process_westchester_game_thread()
sched.start()
