from enum import Enum
from fake import *
from collections import Counter
import random

class GameStates(Enum):
    roleSet = 0
    partySelection = 1
    partyBuilt = 2
    partyVote = 3
    partyVoteTally = 4
    missionVote = 5
    missionTally = 6
    missionGood = 7
    missionEvil = 8
    merlinVote = 9
    merlinVoteTally = 10
    gameWinGood = 11
    gameWinEvil = 12

class Avalon:
    playerCount = 10  # 5-10
    leaderIndex = 0  # random index into player array

    # array containing player names
    players = [] # [p1, p2, p3, p4, p5]

    # array of roles, indices correspond with player array
    roles = [None] * playerCount   # ["evil", "merlin", "good", "good", "evil"]
    currentQuest = 1  # 1-5
    questOutcomes = [None] * 5 # array of who won each past quest ["good","evil","good"]
    goodScore = 0  # 0-3
    evilScore = 0  # 0-3

    # contains the indices of people in players array
    party = [] # 2-5 people depending on Q# and playerCount

    # array of how people voted, indices correspond to players array
    partyVotes = [] # ["yes", "no", "yes", "yes", "yes"]

    # number of the currently attempted party 1-5, lose if party 5 doesn't pass
    partyAttempt = 0

    # array of how evil players voted on mission, indices do not match players
    missionVotes = [] # ["succeed", "fail"]

    # assassin picks 1 player to be merlin, value corresponds to value in players
    merlinVote = -1 # 0-9

    state = GameStates.roleSet

    def __init__(self, players):
        if len(players) < 5 or len(players) > 10:
            raise ValueError('There must be 5-10 players.')
        if not(all(isinstance(i, str) for i in players)):
            raise TypeError('Player list must contain strings')
        self.players = players
        self.playerCount = len(self.players)
    
    def pickRoles(self):
        if self.playerCount < 5 or self.playerCount > 10:
            print("invalid player count")
            return        
        goodNum = 0
        if   self.playerCount <= 5:
            goodNum = 3
        elif self.playerCount <= 7:
            goodNum = 4
        elif self.playerCount <= 8:
            goodNum = 5
        elif self.playerCount <= 10:
            goodNum = 6

        # list of random ordered numbers
        randomList = random.sample(range(self.playerCount), self.playerCount)
        roles = [None] * self.playerCount
        
        roles[randomList[0]] = "merlin"
        goodNum -= 1
        for i in range(1, len(randomList)):
            if goodNum > 0:
                goodNum -= 1
                roles[randomList[i]] = "good"
            else:
                roles[randomList[i]] = "evil"
        return roles

    # junk right now
    def getPartyFromLeader(self):
        Q1 = [2,  2,  2,  3,  3,  3]
        Q2 = [3,  3,  3,  4,  4,  4]
        Q3 = [2,  4,  3,  4,  4,  4]
        Q4 = [3,  3,  4,  5,  5,  5]
        Q5 = [3,  4,  4,  5,  5,  5]
        grid = [Q1, Q2, Q3, Q4, Q5]
        qNum = self.currentQuest - 1
        pCount = self.playerCount - 5
        partySize = grid[qNum][pCount]

        # wait for response somehow check it matches length
        # [1, 2, 3] test val
        response = retrieveParty(partySize, self.playerCount)
        return response

    # junk right now
    def getPartyVotes(self):
        # Don't really know how to do right now

        #for now contains "yes" or "no", empty ones will be yes
        votes = ["yes"] * self.playerCount
        #votes = ["no"] * self.playerCount
        return votes
        pass

    # junk right now
    def getMissionVotes(self):
        # Everyone part member submits, but only evil votes switched to 'fail'
        votes = ["succeed"] * len(self.party)
        #votes[0] = 'fail'
        #votes[1] = 'fail'
        return votes
        pass

    def getMerlinVote(self):
        # only Assassin submits a vote, its an integer from [0, playerCount)
        vote = 1
        return vote
    
    def nextLeader(self, leaderIndex, playerCount):
        return (leaderIndex + 1) % playerCount
    
    def advance(self):
        stateToMethodDict = {
            GameStates.roleSet:         self.roleSetAction,
            GameStates.partySelection:  self.partySelectionAction,
            GameStates.partyBuilt:      self.partyBuiltAction,
            GameStates.partyVote:       self.partyVoteAction,
            GameStates.partyVoteTally:  self.partyVoteTallyAction,
            GameStates.missionVote:     self.missionVoteAction,
            GameStates.missionTally:    self.missionTallyAction,
            GameStates.missionGood:     self.missionGoodAction,
            GameStates.missionEvil:     self.missionEvilAction,
            GameStates.merlinVote:      self.merlinVoteAction,
            GameStates.merlinVoteTally: self.merlinVoteTallyAction,
            GameStates.gameWinGood:     self.gameWinGoodAction,
            GameStates.gameWinEvil:     self.gameWinEvilAction
        }

        stateToMethodDict[self.state]()
        
    def roleSetAction(self):
        print('roleSetAction')
        self.leaderIndex = random.randint(0, self.playerCount-1)
        self.roles = self.pickRoles()
        print(self.players)
        print(self.roles)
        print('First leader is {}'.format(self.players[self.leaderIndex]))
        self.state = GameStates.partySelection
        pass

    def partySelectionAction(self):
        print('partySelectionAction')
        self.party = self.getPartyFromLeader()
        print('party list is {}'.format(self.party))
        self.state = GameStates.partyBuilt
        pass

    def partyBuiltAction(self):
        print('partyBuiltAction')
        self.partyAttempt += 1
        print('On party attempt #{}'.format(self.partyAttempt))
        self.state = GameStates.partyVote
        pass

    def partyVoteAction(self):
        # if someone fails to vote their vote is treated as "yes"
        print('partyVoteAction')
        self.partyVotes = self.getPartyVotes()
        print(self.partyVotes)
        self.state = GameStates.partyVoteTally
        pass

    def partyVoteTallyAction(self):
        # approved by majority vote yes
        # evil wins on 5 consecutive failed votes
        
        print('partyVoteTallyAction')
        tally = Counter(self.partyVotes)
        if tally['yes'] > tally['no']:
            print('Party passed; {} voted yes, {} voted no'
                  .format(tally['yes'], tally['no']))
            self.partyAttempt = 0
            self.state = GameStates.missionVote
        elif self.partyAttempt == 5:
            print('Party didn\'t passed; {} voted yes, {} voted no'
                  .format(tally['yes'], tally['no']))
            self.state = GameStates.gameWinEvil
        else:
            print('Party didn\'t passed; {} voted yes, {} voted no'
                  .format(tally['yes'], tally['no']))
            self.leaderIndex = self.nextLeader(self.leaderIndex,
                                               self.playerCount)
            print('new leader is {}'.format(self.players[self.leaderIndex]))
            self.state = GameStates.partySelection
        pass

    def missionVoteAction(self):
        # good players cant actually vote
        # bad players can vote 'succeed' or 'fail'
        
        print('missionVoteAction')

        self.missionVotes = self.getMissionVotes()
        print(self.missionVotes)
        self.state = GameStates.missionTally
        pass

    def missionTallyAction(self):
        # if players >= 7; quest 4 requires 2 fail cards
        # all other cases only 1 fail needed
        
        print('missionTallyAction')
        tally = Counter(self.missionVotes)
        if tally['fail'] == 0:
            print('Mission succeeds with no fail cards')
            self.state = GameStates.missionGood
        elif (tally['fail'] < 2 and self.currentQuest == 4
        and self.playerCount >= 7):
            print('Mission succeeds with 1 fail card')
            self.state = GameStates.missionGood
        else:
            print('Mission failed with {} fail card(s)'.format(tally['fail']))
            self.state = GameStates.missionEvil   
        pass

    def missionGoodAction(self):
        print('missionGoodAction')
        # increase good wins by 1, set list val to goodwin
        self.goodScore += 1
        self.questOutcomes[self.currentQuest-1] = 'good'
        print('Good side has won {} missions'.format(self.goodScore))
        print('Quest outcomes so far: {}'.format(self.questOutcomes))
        if self.goodScore == 3:
            self.state = GameStates.merlinVote
        else:
            self.currentQuest += 1
            self.leaderIndex = self.nextLeader(self.leaderIndex,
                                               self.playerCount)
            self.partyAttempt = 0
            self.state = GameStates.partySelection
        pass

    def missionEvilAction(self):
        print('missionEvilAction')
        self.evilScore += 1
        self.questOutcomes[self.currentQuest-1] = 'evil'
        print('Evil side has won {} missions'.format(self.evilScore))
        print('Quest outcomes so far: {}'.format(self.questOutcomes))
        if self.evilScore == 3:
            self.state = GameStates.gameWinEvil
        else:
            self.currentQuest += 1
            self.leaderIndex = self.nextLeader(self.leaderIndex,
                                               self.playerCount)
            self.partyAttempt = 0
            self.state = GameStates.partySelection
        pass

    def merlinVoteAction(self):
        print('merlinVoteAction')
        # assassin picks who they think merlin is
        self.merlinVote = self.getMerlinVote()
        print('Assassin picked {}'.format(self.players[self.merlinVote]))
        self.state = GameStates.merlinVoteTally
        pass

    def merlinVoteTallyAction(self):
        print('merlinVoteTallyAction')
        # if assassin picked real merlin evil wins

        j = 0
        for i in range(0, self.playerCount):
            if self.roles[i] == 'merlin':
                j = i
                break

        print('{} was Merlin'.format(self.players[j]))
        if self.roles[self.merlinVote] == 'merlin':
            self.state = GameStates.gameWinEvil            
        else:
            self.state = GameStates.gameWinGood
        pass

    def gameWinGoodAction(self):
        print('gameWinGoodAction')
        pass

    def gameWinEvilAction(self):
        print('gameWinEvilAction')
        pass
