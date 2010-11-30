#!/usr/bin/python 
# -*- coding: cp1252 -*-
# Premier League Fantasy Football Team Picker
# version 0.2.6 (17 October 2010)
# by Ian Renton
# For details, see http://www.onlydreaming.net/software/premier-league-fantasy-football-team-picker
# This code is released under the GPLv3 licence (http://www.gnu.org/licenses/gpl.html).
# Takes player data from the PL website, and picks the optimum team based
# on players' past performance and current injuries.

import re
import datetime
import sys

print "Content-Type: text/html\n\n"

# Port of MATLAB's nchoosek (unique combination) function.
def nchoosek(items, n):
    if n==0: yield []
    else:
        for (i, item) in enumerate(items):
            for cc in nchoosek(items[i+1:],n-1):
                yield [item]+cc

class Player:
    def __init__(self, fields):
        self.id = int(fields[0])
        self.name = fields[1][1:-1]
        self.position = int(fields[2])
        self.teamID = fields[3]
        self.unavailable = int(fields[4])
        self.doubtful = int(fields[5])
        self.news = fields[6]
        self.code = fields[7]
        self.nextOpponentShort = fields[8]
        self.nextOpponentLong = fields[9]
        self.lastSeason = fields[10]
        self.eventCost = fields[11]
        self.maxCost = fields[12]
        self.minCost = fields[13]
        self.originalCost = fields[14]
        self.team = fields[15][1:-1]
        self.dreamTeam = fields[16]
        self.totalPoints = int(fields[17])
        self.weekPoints = fields[18]
        self.minutesPlayed = fields[19]
        self.goalsScored = fields[20]
        self.assists = fields[21]
        self.goalsConceded = fields[22]
        self.penaltiesSaved = fields[23]
        self.penaltiesMissed = fields[24]
        self.yellowCards = fields[25]
        self.redCards = fields[26]
        self.saves = fields[27]
        self.bonus = fields[28]
        self.ownGoals = fields[29]
        self.cleanSheets = fields[30]
        self.valueSeason = float(fields[31])
        self.form = fields[32]
        self.valueForm = fields[33]
        self.pointsPerGame = fields[34]
        self.price = float(fields[35])
        self.priceRiseSeason = fields[36]
        self.priceRiseWeek = fields[37]
        self.priceDropSeason = fields[38]
        self.priceDropWeek = fields[39]
        self.teamsSelectedByPercent = fields[40]
        self.transfersInSeason = fields[41]
        self.transfersOutSeason = fields[42]
        self.transfersInWeek = fields[43]
        self.transfersOutWeek = fields[44]
        self.capRes = "&nbsp;"

    def __str__(self):
        return '<tr><td><p>%4s</p></td><td><p>%-20s</p></td><td><p>%-20s</p></td><td><p>%4s</p></td><td><p>%4s</p></td><td><p>%-20s</p></td></tr>' % (self.id, self.name, self.team, self.price, self.totalPoints, self.capRes)


class TeamPicker:
    def __init__(self):
        self.process()
        
    def set_initial_text(self):
        # Print header
        introText = "<h2>Optimum Premier League Fantasy Football Team</h2><p style=\"font-weight:bold\">Generated on " + datetime.datetime.now().strftime("%A %d %B %Y at %H:%M:%S.") + "</p>"
        introText = introText + "<p>Created using Premier League Fantasy Football Team Picker, version 0.2.6 (17 October 2010), by Ian Renton.<br>"
        introText = introText + "For details and source code, see <a href=\"http://www.onlydreaming.net/software/premier-league-fantasy-football-team-picker\">http://www.onlydreaming.net/software/premier-league-fantasy-football-team-picker</a></p>"
        self.displayUpdate(introText)

    def displayUpdate(self, line):
        self.f.write(line)

    def process(self):
        import urllib2
        import re
        from collections import defaultdict

        # Download the HTML file
        try:
            print "<p>Grabbing HTML...</p>"
            response = urllib2.urlopen('http://fantasy.premierleague.com/M/stats.mc?element_filter=et_1&stat_filter=&price_filter=&view=')
            html = response.read()
        except IOError, e:
            self.f = open('./ploutput.html', 'w')	
            self.set_initial_text()
            self.displayUpdate('<p style="font-weight:bold">Could not find the player stats list, maybe the URL has changed?</p>')
            return
        else:
            pass

        # Turn it into a list of all players
        print "<p>Extracting Data...</p>"
        allPlayers = self.extractDataLinesFromHTML(html)
        # Remove injured players
        allPlayers = filter(lambda player : ((player.unavailable==0) & (player.doubtful==0)), allPlayers)
        
        # Split data into four separate lists, one for each kind of player.
        players = defaultdict(list)
        for player in allPlayers:
            players[player.position].append(player)
            
        # Produce a set of thresholds for VFM and overall price.  This allows us to cut
        # down the list of players to only those that are good value for money or
        # particularly high-scoring.  This mirrors human behaviour, where the user
        # picks some very high-scoring (but expensive) players, then fills out the rest
        # of the team with cheap but good-value players.
        # These thresholds are necessary to reduce the number of players being considered,
        # as otherwise the number of combinations that the script must consider would be
        # too large for the script to run in sensible time.
        
        print "<p>Thresholding...</p>"
        thresholdDivisor = 1.4
        sensibleDataSet = 0
        while (sensibleDataSet == 0):
            points = lambda player: player.totalPoints
            valueForMoney = lambda player: player.valueSeason

            pointThresholds = defaultdict(float)
            valueThresholds = defaultdict(float)
            for position in players.keys():
                pointThresholds[position] = max(players[position], key=points).totalPoints / thresholdDivisor
                valueThresholds[position] = max(players[position], key=valueForMoney).valueSeason / thresholdDivisor
                #print pointThresholds[position]
                #print valueThresholds[position]

            # This section applies the thresholds calculated in the previous one, to cut down
            # the number of players.
            for position in players.keys():
                players[position] = filter(lambda x : ((x.totalPoints > pointThresholds[position]) | (x.valueSeason > valueThresholds[position])), players[position])
            
            # Using a function to pick unique combinations of players, we here form a list of
            # all possible combinations: 1 2 3 4, 1 2 3 5, 1 2 3 6 and so on.
            defenderChoices = list(nchoosek(players[2],5))

            # Now the same for the midfielders.
            midfielderChoices = list(nchoosek(players[3],5))

            # And now the same for the strikers.
            strikerChoices = list(nchoosek(players[4],3))

            # To reduce the number of combinations, we just pick the two goalkeepers
            # who provide best value for money rather than searching through them all.
            # Possibly a dubious assumption that goalkeepers are the least worth
            # worrying about, but hey, it makes this run a lot quicker.
            players[1].sort(lambda x, y: cmp(y.valueSeason, x.valueSeason))
            goalkeepers = []
            goalkeepers.append(players[1][0])
            goalkeepers.append(players[1][1])

            # For each combination of five defenders, we calculate their combined price
            # and combined points totals.
            # Create two functions that, given a list of permutations of players, will return a list of prices of those players in the same order.
            # Er... I guess if you're not up on your functional programming, this must look a bit hideous...
            prices = lambda permutations: reduce(lambda total, player: total + player.price, permutations, 0)
            points = lambda permutations: reduce(lambda total, player: total + player.totalPoints, permutations, 0)
            #Sorry! Having those simplifies the next bit dramatically though:
            defChoicesPrice = map(prices, defenderChoices)
            defChoicesPoints = map(points, defenderChoices)

            # Same for the midfielders.
            midChoicesPrice = map(prices, midfielderChoices)
            midChoicesPoints = map(points, midfielderChoices)

            # Same for the strikers.
            strChoicesPrice = map(prices, strikerChoices)
            strChoicesPoints = map(points, strikerChoices)

            # If we have too many iterations to be possible in sensible time, go back and reduce
            # thresholdDivisor until we have something sensible.
            totalIterations = len(defenderChoices) * len(midfielderChoices) * len(strikerChoices)
            print thresholdDivisor
            print totalIterations
            if (totalIterations <= 1800000000):
                sensibleDataSet = 1
            else:
                n = 0.1
                if (thresholdDivisor < 2.8):
                    n = 0.05
                if (thresholdDivisor < 1.8):
                    n = 0.05
                if (thresholdDivisor < 1.6):
                    n = 0.025
                thresholdDivisor = thresholdDivisor - n

        # Now we iterate through all possible choices for defenders, midfielders and
        # strikers.  In each case, we check to see if this set is better than the one
        # before, and if so we record it.
        print "Beginning Iterations..."
        bestTotalPoints = 0
        bestChoices = []
        bestFormation = 0
        maxPrice = 100 - goalkeepers[0].price - goalkeepers[1].price
        
        for (i, defs) in enumerate(defenderChoices):
            for (j, mids) in enumerate(midfielderChoices):
                for (k, strs) in enumerate(strikerChoices):
                    if ((defChoicesPrice[i] + midChoicesPrice[j] + strChoicesPrice[k]) <= maxPrice):
                        teamPoints = (defChoicesPoints[i] + midChoicesPoints[j] + strChoicesPoints[k])
                        if (teamPoints > bestTotalPoints):
                            # Check what Premiership teams these players are
                            # from, you're allowed a max of three from each.
                            realTeams = []
                            for player in goalkeepers:
                                realTeams.append(player.team)
                            for player in defs:
                                realTeams.append(player.team)
                            for player in mids:
                                realTeams.append(player.team)
                            for player in strs:
                                realTeams.append(player.team)
                            realTeams.sort(lambda x, y: cmp(y, x))
                            tooManyPlayersFromATeam = False
                            for i in range(3,len(realTeams)):
                                if (realTeams[i] == realTeams[i-1] == realTeams[i-2] == realTeams[i-3]):
                                    tooManyPlayersFromATeam = True

                            if (tooManyPlayersFromATeam == False):
                                bestTotalPoints = teamPoints
                                (bestDefs, bestMids, bestStrs) = (defs, mids, strs)

        # Calculate optimum team's total price.
        bestTotalPrice = goalkeepers[0].price + goalkeepers[1].price
        for p in bestDefs:
            bestTotalPrice += p.price
        for p in bestMids:
            bestTotalPrice += p.price
        for p in bestStrs:
            bestTotalPrice += p.price

        # Sort players by points within each category
        goalkeepers.sort(lambda x, y: cmp(y.totalPoints, x.totalPoints))
        bestDefs.sort(lambda x, y: cmp(y.totalPoints, x.totalPoints))
        bestMids.sort(lambda x, y: cmp(y.totalPoints, x.totalPoints))
        bestStrs.sort(lambda x, y: cmp(y.totalPoints, x.totalPoints))

        # Mark reserves
        goalkeepers[1].capRes = "Reserve"
        bestDefs[4].capRes = "Reserve"
        bestMids[4].capRes = "Reserve"
        bestStrs[2].capRes = "Reserve"

        # Mark captain
        allPlayers = []
        for p in goalkeepers:
            allPlayers.append(p)
        for p in bestDefs:
            allPlayers.append(p)
        for p in bestMids:
            allPlayers.append(p)
        for p in bestStrs:
            allPlayers.append(p)
        allPlayers.sort(lambda x, y: cmp(y.totalPoints, x.totalPoints))
        allPlayers[0].capRes = "Captain"

        # Print the optimum team's details.
        self.f = open('./ploutput.html', 'w')	
        self.set_initial_text()
        self.displayUpdate('<table width="500px" border="1" cellspacing="2">')
        self.displayUpdate('<tr><td><p><b>ID</b></p></td><td><p><b>Name</b></p></td><td><p><b>Club</b></p></td><td><p><b>Price</b></p></td><td><p><b>Points</b></p></td><td><p><b>Cap / Res</b></p></td></tr>')
        self.displayUpdate('<tr><td colspan=6><p><b>Goalkeepers</b></p></td></tr>')
        self.displayUpdate( ''.join(map(str, goalkeepers)))
        self.displayUpdate('<tr><td colspan=6><p><b>Defenders</b></p></td></tr>')
        self.displayUpdate( ''.join(map(str, bestDefs)))
        self.displayUpdate('<tr><td colspan=6><p><b>Midfielders</b></p></td></tr>')
        self.displayUpdate(''.join(map(str, bestMids)))
        self.displayUpdate('<tr><td colspan=6><p><b>Strikers</b></p></td></tr>')
        self.displayUpdate(''.join(map(str, bestStrs)))
        self.displayUpdate('<tr><td colspan=3><p><b>Total</b></p></td><td><p><b>%4s</b></p></td><td><p><b>%4s</b></p></td><td>&nbsp;</td></tr>' % (bestTotalPrice, bestTotalPoints))
        self.displayUpdate('</table>')

        self.f.close()
        print "<p><a href=\"ploutput.html\">ploutput.html</a> successfully generated.</p>"
        return 0

    def extractDataLinesFromHTML(self, html):
        tmpPlayerList = []
        lines = html.split("\n");
        for line in lines:
            if (line[0:3] == "ed["):
                dataStart = re.compile("\[").search(line[4:])
                dataEnd = re.compile("\]").search(line[4+dataStart.start():])
                data = line[dataStart.start()+4+1:dataStart.start()+4+dataEnd.end()-1]
                fields = data.split(",")
                tmpPlayerList.append(Player(fields))
        return tmpPlayerList
        

teampicker = TeamPicker()
