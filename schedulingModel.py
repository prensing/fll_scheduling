#!/usr/bin/python3

import sys
import datetime
import math
import re
import csv
import copy
import functools
from dateutil.parser import parse as dateparse
from random import shuffle, seed
# from pprint import pprint


@functools.total_ordering
class EventTime(object):
    # share startT across all instances
    eventStartTime = None
    eventEndTime = None   # integer

    def __init__(self, tm):
        if isinstance(tm, str):
            dt = dateparse(tm)
            self._minutes = int((dt - self.eventStartTime).total_seconds() // 60)
        else:
            self._minutes = tm
        if self.eventEndTime is not None:
            self._minutes = min(self.eventEndTime, self._minutes)
        return

    def __int__(self):
        return self._minutes

    def __hash__(self):
        return hash(self._minutes)

    def __incr__(self, min_incr):
        if type(min) != int:
            raise TypeError

        val = self._minutes + min_incr
        if self.eventEndTime is not None:
            val = min(self.eventEndTime, val)
        self._minutes = val
        return self

    def __add__(self, min_incr):
        if type(min_incr) != int:
            raise TypeError

        val = self._minutes + min_incr
        if self.eventEndTime is not None:
            val = min(self.eventEndTime, val)
        return EventTime(val)

    def __sub__(self, other):
        if type(other) != type(self):
            raise TypeError

        return self._minutes - other._minutes

    def __eq__(self, other):
        if type(other) != type(self):
            raise TypeError("Unsupported type %s" % type(other))

        return self._minutes == other._minutes

    def __lt__(self, other):
        if type(other) != type(self):
            raise TypeError

        return self._minutes < other._minutes

    def __str__(self):
        return (self.eventStartTime + datetime.timedelta(minutes=self._minutes)).strftime('%H:%M')

    def __repr__(self):
        return "EventTime('%s')" % str(self)


class Team(object):
    def __init__(self, index, teamNumber, name):
        self.index = index
        self.teamNumber = teamNumber
        self.name = name
        self.schedule = []
        return

    def designation(self):
        if self.teamNumber > 0:
            return self.teamNumber
        return self.name

    def addEvent(self, evt, slot):
        self.schedule.append((evt, slot))
        return

    def __lt__(self, other):
        if type(other) != type(self):
            raise TypeError

        return self.teamNumber < other.teamNumber

    def travelTime(self):
        minTravel = 10000
        prevET = None
        for evt, slot in sorted(self.schedule, key=lambda e: e[0].startTime()):
            if prevET is not None:
                dt = evt.startTime() - prevET
                minTravel = min(minTravel, dt)
            prevET = evt.endTime()
        return minTravel

    def outputSchedule(self, outCSV):
        outCSV.writerow((self.teamNumber, self.name))
        outCSV.writerow(('Event', 'Room/Table', 'StartTime', 'EndTime'))
        for evt, slot in sorted(self.schedule):
            evt.outputTeamSchedule(slot, outCSV)
        return


@functools.total_ordering
class TimeSlot(object):
    travelTime = 0
    timeBlockBoundaries = {}

    def __init__(self, index, startT, endT):
        self.index = index
        self._startT = copy.copy(startT)
        self._endT = copy.copy(endT)
        self.extendEnd = 0
        return

    @classmethod
    def setTimeBlocks(cls, alltimes):
        cls.timeBlockBoundaries = {t: i for i, t in enumerate(sorted(alltimes))}
        return

    @classmethod
    def numTimeBlocks(cls):
        # 1 less because we are counting regions. timeBlockBoundaries holds the edges
        return len(cls.timeBlockBoundaries) - 1

    def startTime(self):
        return self._startT

    def endTime(self, padded=False):
        if padded:
            return self._endT + (self.travelTime + self.extendEnd)
        return self._endT

    def timeBlockRange(self, padded=False):
        return range(self.timeBlockBoundaries[self._startT], self.timeBlockBoundaries[self.endTime(padded)])

    def __eq__(self, other):
        if not isinstance(other, TimeSlot):
            raise TypeError("Unsupported type %s" % type(other))

        return self._startT == other._startT

    def __lt__(self, other):
        if not isinstance(other, TimeSlot):
            raise TypeError

        return self._startT < other._startT


class JudgeEvent(object):
    def __init__(self, index, name):
        self.index = index
        self.name = name
        self.rooms = []
        self.sessions = []
        self.subSchedule = None  # for block scheduling
        self.blockEvents = {}
        return

    def findSession(self, sessIndex):
        s = self.sessions[sessIndex - 1]
        assert(s.index == sessIndex)
        return s

    def buildBlockSubschedule(self, config):
        nSessions = len(config['events'])
        sessLen = config['sessionLen']
        deltaT = sessLen + config['sessionBreak']

        times = []
        sT = 0
        evtRoom = []
        for se in config['events']:
            eT = sT + sessLen
            times.append((sT, eT))

            self.blockEvents[se['name']] = se['rooms']
            nRooms1 = len(se['rooms'])
            for r in se['rooms']:
                evtRoom.append((se['name'], r))

            sT += deltaT

        step = 0
        results = {}

        for rmIndex, rm in enumerate(self.rooms):
            reslist = []

            used = set()
            seRmIndex = rmIndex % nRooms1

            for seLoop in range(nSessions):
                trials = 0
                while step > 0 and seRmIndex in used:
                    seRmIndex = (seRmIndex + 1) % nRooms1
                    trials += 1
                    if trials >= nRooms1:
                        print("Error: no available room")
                        sys.exit(10)

                seIndex = (seLoop + step) % nSessions
                reslist.append({'session': seLoop,
                                'event': config['events'][seIndex]['name'],
                                'room': config['events'][seIndex]['rooms'][seRmIndex],
                                'startTM': times[seLoop][0],
                                'endTM': times[seLoop][1]})

                used.add(seRmIndex)
                seRmIndex = (seRmIndex + step) % nRooms1

            # results[rm] = sorted(reslist, key=lambda x: x['session'])
            results[rm] = reslist
            if (rmIndex + 1) % nRooms1 == 0:
                step += 1

        self.subSchedule = results
        return

    def outputSchedule(self, outstrm):
        allSessions = {}
        for sess in self.sessions:
            sess.judgeScheduleEntries(allSessions)

        for evtName, sessions in sorted(allSessions.items()):
            outstrm.write(evtName + '\r\n')  # CSV files use DOS eol
            fields = ['Session', 'StartTime', 'EndTime', ]
            if self.subSchedule is None:
                fields.extend(self.rooms)
            else:
                fields.extend(self.blockEvents[evtName])
            outCSV = csv.DictWriter(outstrm, fieldnames=fields)
            outCSV.writeheader()

            index = 1
            for sess in sorted(sessions.values(), key=lambda r: r['StartTime']):
                sess['Session'] = index
                outCSV.writerow(sess)
                index += 1
            outstrm.write('\r\n')
        return


class JudgeSession(TimeSlot):
    def __init__(self, event, index, startT, endT, penalty=0):
        TimeSlot.__init__(self, index, startT, endT)
        self.event = event
        self.penalty = penalty
        self.teams = len(self.event.rooms) * [None, ]
        return

    def assignTeam(self, team):
        # No need for shuffling, and that way, empty room is always latest possible
        for i in range(len(self.event.rooms)):
            if self.teams[i] is None:
                self.teams[i] = team
                team.addEvent(self, i)
                return
        raise Exception("Too many teams for judge rooms")

    def __str__(self):
        args = [self.index, self.startTime(), self.endTime(), self.event.name]
        args.extend(self.teams)
        return ' '.join([str(x) for x in args])

    def outputTeamSchedule(self, slot, outCSV):
        if self.event.subSchedule is not None:
            for subE in self.event.subSchedule[self.event.rooms[slot]]:
                outCSV.writerow((subE['event'], subE['room'], self.startTime() + subE['startTM'], self.startTime() + subE['endTM']))
        else:
            outCSV.writerow((self.event.name, self.event.rooms[slot], self.startTime(), self.endTime()))
        return

    def judgeScheduleEntries(self, entries):
        if self.event.subSchedule is not None:
            for i in range(len(self.event.rooms)):
                t = self.teams[i]
                for subE in self.event.subSchedule[self.event.rooms[i]]:
                    r1 = entries.get(subE['event'], None)
                    if r1 is None:
                        r1 = {}
                        entries[subE['event']] = r1

                    st = self.startTime() + subE['startTM']
                    r2 = r1.get(st, None)
                    if r2 is None:
                        r2 = {'StartTime': st, 'EndTime': self.startTime() + subE['endTM']}
                        r1[st] = r2
                    r2[subE['room']] = t.teamNumber if t is not None else ''
        else:
            if self.event.name not in entries:
                entries[self.event.name] = {}
            row = {'StartTime': self.startTime(), 'EndTime': self.endTime()}
            for i in range(len(self.teams)):
                if self.teams[i] is not None:
                    row[self.event.rooms[i]] = self.teams[i].teamNumber
            entries[self.event.name][self.startT] = row
        return


class MatchList(object):
    def __init__(self):
        self.matches = []
        self.nGamesPerTeam = 0
        self.dummyTeam = False
        self.breakTime = 0
        self.maxTeamMatchesPerFields = None
        return

    def outputSchedule(self, outstrm):
        fields = ['Match', 'StartTime', 'EndTime']
        for tl in self.tableNames:
            for t in tl:
                for i in range(2):
                    tn = '{} {}'.format(t, i+1)
                    fields.append(tn)
        outCSV = csv.DictWriter(outstrm, fieldnames=fields)
        outCSV.writeheader()

        row = {'Match': -1}
        prevEndTime = None
        for m in self.matches:
            if row['Match'] != m.matchNum:
                if row['Match'] > 0:
                    outCSV.writerow(row)
                    # be nice and flag breaks
                    if prevEndTime is not None and m.startTime() - prevEndTime > self.breakTime:
                        outCSV.writerow({'Match': '', 'StartTime': prevEndTime, 'EndTime': m.startTime(), fields[3]: 'Break'})
                row = {'Match': m.matchNum,
                       'StartTime': m.startTime(),
                       'EndTime': m.endTime()}
                prevEndTime = m.endTime()
            for i in range(len(m.teams)):
                if m.teams[i] is not None:
                    row[m.tableName(i)] = m.teams[i].designation()

        outCSV.writerow(row)
        return


class Match(TimeSlot):
    def __init__(self, index, startT, endT, matchNum, table):
        TimeSlot.__init__(self, index, startT, endT)
        self.matchNum = matchNum
        self.table = table
        # self.penalty = penalty
        self.teams = [None, None]
        return

    def assignTeam(self, team):
        slots = [0, 1]
        shuffle(slots)
        for i in slots:
            if self.teams[i] is None:
                self.teams[i] = team
                team.addEvent(self, i)
                return
        raise Exception("Too many teams for match slots")

    def __str__(self):
        args = [self.index, self.startT, self.endT, self.table]
        args.extend(self.teams)
        return ' '.join([str(x) for x in args])

    def tableName(self, slot):
        return '{} {}'.format(self.table, slot+1)

    def outputTeamSchedule(self, slot, outCSV):
        outCSV.writerow(('Match {}'.format(self.matchNum), self.tableName(slot), self.startTime(), self.endTime()))
        return


class ScheduleModel(object):
    # GLPK solver
    # lineExpr = r'^\s*[0-9]+ matchAssign\[(?P<m>[^,]+),(?P<t1>[^,]+),(?P<t2>[^,]+)\]\s+\*\s+(?P<val>[0-9]+)'

    # CBC solver (seems to be faster)
    modelLineExpr = r'^\s*[0-9]+ (?P<type>match|judge)Assign\[(?P<i1>[^,]+),(?P<i2>[^,]+),(?P<i3>[^,]+)\]\s+(?P<val>[0-9]+)'

    def __init__(self, config):
        EventTime.eventStartTime = dateparse(config['startTime'])

        self.eventDuration = 0
        TimeSlot.travelTime = config['travelTime']

        self.teams = ScheduleModel._readTeams(config['teams'])

        self._createMatches(config['matchInfo'])

        self.hasJudgePenalty = False
        self._createJudgeSessions(config['judgeEvents'])
        EventTime.eventEndTime = self.eventDuration

        self.scheduleBlocks = config.get('scheduleBlocks', None)

        # now that the schedule is defined, find all the time periods
        self.setTimeBlocks()

        return

    def findTeam(self, index):
        # quick method, but double check
        if index == len(self.teams) + 1:
            return Team(index, -1, 'DUMMY')

        t = self.teams[index - 1]
        assert(t.index == index)
        return t

    def findMatch(self, index):
        m = self.matchList.matches[index - 1]
        assert(m.index == index)
        return m

    def findJudgeEvent(self, index):
        for e in self.judgeEvents.values():
            if e.index == index:
                return e
        return None

    def setTimeBlocks(self):
        alltimes = set()
        for e in self.judgeEvents.values():
            for s in e.sessions:
                alltimes.add(s.startTime())
                alltimes.add(s.endTime(padded=True))

        for e in self.matchList.matches:
            alltimes.add(e.startTime())
            alltimes.add(e.endTime(padded=True))

        TimeSlot.setTimeBlocks(alltimes)
        return

    # ----------------------------------------------------------------------------------------------------
    # Config methods

    @staticmethod
    def _readTeams(tList):
        result = []
        index = 1
        for num, name in tList:
            result.append(Team(index, num, name))
            index += 1
        return result

    def _readBreaks(self, times):
        breaks = []
        for brkSt, brkEt in times:
            st = EventTime(brkSt)
            et = EventTime(brkEt)
            breaks.append((st, et))
        return breaks

    def _createMatches(self, config):
        self.matchList = MatchList()
        self.matchList.nGamesPerTeam = config['gamesPerTeam']
        self.matchList.tableNames = config['tableNames']
        self.matchList.breakTime = config['matchBreak']
        self.matchList.maxTeamMatchesPerFields = config.get('maxTeamMatchesPerFields', None)

        resetAfterBreak = config.get('resetAfterBreak', False)

        nTeams = len(self.teams)
        nMatchesFloat = float(nTeams) * self.matchList.nGamesPerTeam / 2 + config.get('extraMatches', 0)
        nMatches = int(math.ceil(nMatchesFloat))

        self.matchList.dummyTeam = 1 if int(nMatchesFloat) != nMatches else 0

        breakTimes = self._readBreaks(config['breakTimes'])

        if 'resetAfterBreak' in config:
            resetAfterBreak = [EventTime(t) for t in config['resetAfterBreak']]
        else:
            resetAfterBreak = ()

        if 'oneFieldOnly' in config:
            oneFieldOnly = [EventTime(t) for t in config['oneFieldOnly']]
        else:
            oneFieldOnly = {}

        # ------------------------------
        # compute matches times, names

        startT = EventTime(0)
        mLen = config['matchLen']
        dt = mLen + self.matchList.breakTime

        nTableSets = len(self.matchList.tableNames)
        tblSet = 0

        matchSession = 1
        matchIndex = 0
        while matchIndex < nMatches:
            endT = startT + mLen

            oneField = startT in oneFieldOnly

            for tbl in config['tableNames'][tblSet]:
                matchIndex += 1
                self.matchList.matches.append(Match(matchIndex, startT, endT, matchSession, tbl))
                if matchIndex >= nMatches:
                    break
                if oneField:
                    break

            matchSession += 1
            startT += dt

            for brkST, brkET in breakTimes:
                if startT >= brkST and startT < brkET:
                    startT = brkET
                    break

            if startT in resetAfterBreak:
                tblSet = 0
            else:
                tblSet = (tblSet + 1) % nTableSets

        print('Matches end at {}'.format(startT), file=sys.stderr)
        self.eventDuration = max(self.eventDuration, int(startT))

        if 'extendSessions' in config:
            # extend over breaks so teams have decent amount of time
            # can help if breaks don't happen because of overruns
            for st, et, delT in config['extendSessions']:
                startT1 = EventTime(st)
                endT1 = EventTime(et)

                for m in self.matchList.matches:
                    if m.startTime() >= startT1 and m.startTime() < endT1:
                        m.extendEnd = delT

        return

    def _createJudgeSessions(self, config):
        self.judgeEvents = {}

        eventIndex = 1
        for judgeInfo in config:
            event = JudgeEvent(eventIndex, judgeInfo['name'])
            self.judgeEvents[judgeInfo['name']] = event
            event.rooms = judgeInfo['rooms']

            breakTimes = self._readBreaks(judgeInfo['breakTimes'])
            startT = EventTime(0)
            sLen = judgeInfo['sessionLen']
            dt = sLen + judgeInfo['sessionBreak']

            nSessFull = len(self.teams) / len(judgeInfo['rooms'])
            nSess = int(math.ceil(len(self.teams) / len(judgeInfo['rooms'])))

            for sessIndex in range(1, nSess+1):
                pen = 0
                if sessIndex > nSessFull:
                    pen = 10
                    self.hasJudgePenalty = True
                endT = startT + sLen
                session = JudgeSession(event, sessIndex, startT, endT, pen)
                event.sessions.append(session)

                startT += dt

                for brkST, brkET in breakTimes:
                    if startT >= brkST and startT < brkET:
                        startT = brkET
                        break

            if 'extendSessions' in judgeInfo:
                # extend over lunch so teams have decent amount of time
                st = EventTime(judgeInfo['extendSessions'][0])
                et = EventTime(judgeInfo['extendSessions'][1])
                delT = judgeInfo['extendSessions'][2]

                for jS in event.sessions:
                    if jS.startT >= st and jS.startT < et:
                        jS.extendEnd = delT

            if 'subEvents' in judgeInfo:
                event.buildBlockSubschedule(judgeInfo['subEvents'])

            eventIndex += 1
            print('Judge {} ends at {}'.format(judgeInfo['name'], startT), file=sys.stderr)
            self.eventDuration = max(self.eventDuration, int(startT))

        return

    # ----------------------------------------------------------------------------------------------------
    # Output model file

    def writeModel(self):
        self._writeParams()
        self._writeObjective()
        self._handleScheduleBlocks()
        self._handleFieldDistribution()
        self._writeData()
        return

    def _writeParams(self):
        maxTeams = len(self.teams)
        if self.matchList.dummyTeam:
            maxTeams += 1

        print('# Model created', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        print()
        print('set teams := 1 .. %d;' % len(self.teams))
        print('set matches := 1 .. %d;' % len(self.matchList.matches))

        print('set judgeEvents := 1 .. %d;' % len(self.judgeEvents))
        print('param nJudgeSessions{en in judgeEvents};')
        print('set judgeSessions{en in judgeEvents} := 1 .. nJudgeSessions[en];')

        print('set times := 0 .. %d;' % (TimeSlot.numTimeBlocks() - 1))

        print()
        print('var matchAssign{m in matches, t1 in teams, t2 in t1+1 .. %d}, binary;' % maxTeams)
        # if self.hasMatchPenalty:
        #     print('param matchPenalties{m in matches}, default 0, >= 0;')

        print('var judgeAssign{en in judgeEvents, j in judgeSessions[en], t in teams}, binary;')
        if self.hasJudgePenalty:
            print('param judgePenalties{en in judgeEvents,j in judgeSessions[en]}, default 0, >= 0;')

        print()
        print('param judgeEventTimes{en in judgeEvents,judgeSessions[en], tm in times}, binary, default 0;')
        print('param matchTimes{m in matches, tm in times}, binary, default 0;')

        return

    def _writeObjective(self):
        maxTeams = len(self.teams)
        if self.matchList.dummyTeam:
            maxTeams += 1

        print()
        print('minimize f:')
        done = False
        # if self.hasMatchPenalty:
        #    print('    sum{m in matches,t in teams,t2 in t+1 ..', nTeams+1, '} matchPenalties[m] * matchAssign[m,t,t2] +'.format_map(params))
        #    print('    sum{m in matches,t in 1 ..', nTeams, ',t2 in 1 .. t-1} matchPenalties[m] * matchAssign[m,t2,t]', end='')
        #    done = True
        if self.hasJudgePenalty:
            if done:
                print(' +')
            print('    sum{en in judgeEvents,j in judgeSessions[en],t in teams} judgePenalties[en,j] * judgeAssign[en,j,t]', end='')
            done = True
        if not done:
            print('    1', end='')
        print(';')

        print()
        print('# number of matches for each team')
        print('s.t. teamMatches{t in teams}:')
        print('     (sum{m in matches, t2 in 1 .. t-1} matchAssign[m,t2,t]) +')
        print('     (sum{m in matches, t2 in t+1 .. %d} matchAssign[m,t,t2]) = %d;' % (maxTeams, self.matchList.nGamesPerTeam))
        if self.matchList.dummyTeam:
            print('s.t. dummyMatch:')
            print('     (sum{{t in teams}} matchAssign[{},t,{}]) = 1;'.format(len(self.matchList.matches), maxTeams))
            print('s.t. dummyNonMatch{{t in teams,m in 1 .. {}}}:'.format(len(self.matchList.matches)-1))
            print('     matchAssign[m,t,{}] = 0;'.format(maxTeams))

        print('# only one pair per match')
        print('s.t. teamsPerMatch{m in matches}:')
        print('     sum{t1 in teams, t2 in t1+1 .. %d} matchAssign[m,t1,t2] <= 1;' % maxTeams)

        print('# no re-matches')
        print('s.t. rematches{t1 in teams, t2 in t1+1 .. %d}:' % maxTeams)
        print('     sum{m in matches} matchAssign[m,t1,t2] <= 1;')

        print()
        print('# number of teams per judge slot')
        for jName, event in self.judgeEvents.items():
            print('s.t. {}Slots{{j in judgeSessions[{}]}}:'.format(jName, event.index))
            print('     sum{t in teams} judgeAssign[%d,j,t] <= %d;' % (event.index, len(event.rooms)))

        print('# teams get judged exactly once per event type')
        print('s.t. teamJudgings{en in judgeEvents,t in teams}:')
        print('     sum{j in judgeSessions[en]} judgeAssign[en,j,t] = 1;')

        print()
        print('# team can only be in once place at a time')
        print('s.t. teamLocation{t in teams,tm in times}:')
        print('     (sum{je in judgeEvents, j in judgeSessions[je]} judgeAssign[je,j,t] * judgeEventTimes[je,j,tm]) +')
        print('     (sum{t2 in 1 .. t-1, m in matches} matchAssign[m,t2,t] * matchTimes[m,tm]) +')
        print('     (sum{t2 in t+1 .. %d, m in matches} matchAssign[m,t,t2] * matchTimes[m,tm]) <= 1;' % maxTeams)

        return

    def _handleScheduleBlocks(self):
        if self.scheduleBlocks is None:
            return

        maxTeams = len(self.teams)
        if self.matchList.dummyTeam:
            maxTeams += 1

        print()
        index = 0
        for st, et, judgeEvts in self.scheduleBlocks:
            startT = EventTime(st)
            endT = EventTime(et)

            startMatch = None
            endMatch = None
            for m in self.matchList.matches:
                if startMatch is None and m.startTime() >= startT:
                    startMatch = m.index
                if m.endTime() <= endT:
                    endMatch = m.index
            if startMatch is not None and endMatch is None:
                endMatch = self.matches.matchList[-1].index

            print('s.t. scheduleBlock{}{{t in teams}}:'.format(index))
            print('    (sum{{m in {0} .. {1}, t2 in t+1 .. {2}}} matchAssign[m,t,t2])'.format(startMatch, endMatch, maxTeams))
            print('    + (sum{{m in {0} .. {1}, t2 in 1 .. t-1}} matchAssign[m,t2,t])'.format(startMatch, endMatch))

            for m in judgeEvts:
                startSess = None
                endSess = None
                evtIndex = self.judgeEvents[m].index
                for s in self.judgeEvents[m].sessions:
                    if startSess is None and s.startTime() >= startT:
                        startSess = s.index
                    if s.endTime() <= endT:
                        endSess = s.index
                if startSess is not None:
                    if startSess == endSess:
                        print('    + judgeAssign[{0},{1},t]'.format(evtIndex, startSess))
                    else:
                        print('    + (sum{{j in {1} .. {2}}} judgeAssign[{0},j,t])'.format(evtIndex, startSess, endSess))

            print('    >= 1;')
            index += 1

        return

    def _handleFieldDistribution(self):
        maxMatch = self.matchList.maxTeamMatchesPerFields
        if maxMatch is None:
            return

        nMatches = len(self.matchList.matches)
        nFields = sum([len(x) for x in self.matchList.tableNames])

        print()
        print('# Add constraints to spread the teams across the different fields')
        print('#  Not required, and may slow down the model solving!!')
        print('s.t. maxPerField{t in teams, sm in 1 .. %d}:' % nFields)
        print('    (sum{{m in sm .. {} by {}, t2 in t+1 .. {}}} matchAssign[m,t,t2])'.format(nMatches, nFields, len(self.teams)))
        print('    + (sum{{m in sm .. {} by {}, t2 in 1 .. t-1}} matchAssign[m,t2,t]) <= {};'.format(nMatches, nFields, maxMatch))

        return

    def _writeData(self):
        print()
        print('data;')

        print('param nJudgeSessions :=')
        first = True
        for name, event in self.judgeEvents.items():
            if not first:
                print(',')
            print('     {} {}'.format(event.index, len(event.sessions)), end='')
            first = False
        print(';')

        if self.hasJudgePenalty:
            print('param judgePenalties :=')
            first = True
            for name, event in self.judgeEvents.items():
                for s in event.sessions:
                    if s.penalty > 0:
                        if not first:
                            print(',')
                        print('      [{},{}] {}'.format(event.index, s.index, s.penalty), end='')
                        first = False
            print(';')

        # if self.hasMatchPenalty:
        #     print('# applied only to non-dummy groups')
        #     print('param matchPenalties :=')
        #     # first = True
        #     # for match, mName, st, et, p in matchList:
        #     #     if p > 0:
        #     #         if not first: print ','
        #     #         print "      '%s' %d" % (mName, p),
        #     #         first = False
        #     print(';')

        print('param judgeEventTimes :=')
        first = True
        for name, event in self.judgeEvents.items():
            for s in event.sessions:
                for t in s.timeBlockRange(padded=True):
                    if not first:
                        print(',')
                    print("      [%d,%d,%d] 1" % (event.index, s.index, t), end='')
                    first = False
        print(';')

        print('param matchTimes :=')
        first = True
        for match in self.matchList.matches:
            for t in match.timeBlockRange(padded=True):
                if not first:
                    print(',')
                print("      [%d,%d] 1" % (match.index, t), end='')
                first = False
        print(';')

        print('end;')

    # ----------------------------------------------------------------------------------------------------

    def outputMatches(self):
        self.matchList.outputSchedule(sys.stdout)
        return

    def outputJudging(self):
        for jN, judgeEvt in sorted(self.judgeEvents.items()):
            judgeEvt.outputSchedule(sys.stdout)
        return

    def formatOutput(self, outputBase, results):
        with open(results) as infile:
            self.readResults(infile)

        fname = '{}_matches.csv'.format(outputBase)
        with open(fname, 'w') as outfile:
            self.matchList.outputSchedule(outfile)

        fname = '{}_judging.csv'.format(outputBase)
        with open(fname, 'w') as outfile:
            for jN, judgeEvt in sorted(self.judgeEvents.items()):
                judgeEvt.outputSchedule(outfile)

        fname = '{}_teams.csv'.format(outputBase)
        with open(fname, 'w') as outfile:
            outCSV = csv.writer(outfile)

            for team in sorted(self.teams):
                print('Team {} min travel = {}'.format(team.teamNumber, team.travelTime()))
                team.outputSchedule(outCSV)
                outCSV.writerow(())

        return

    def readResults(self, infile):
        while 1:
            line = infile.readline()
            if not line:
                break

            if re.match(r'^\s*[0-9]+ (matchAssign|judgeAssign)\[.*\]\s*$', line):
                # line must be continued
                line2 = infile.readline()
                line += line2

            #   14914 matchAssign[50,7,17]                1                       0
            m = re.search(ScheduleModel.modelLineExpr, line)
            if m:
                if m.group('type') == 'match':
                    # match assignment
                    val = int(m.group('val'))
                    if val:
                        match = self.findMatch(int(m.group('i1')))
                        match.assignTeam(self.findTeam(int(m.group('i2'))))
                        match.assignTeam(self.findTeam(int(m.group('i3'))))
                else:
                    # judge assignment
                    val = int(m.group('val'))
                    if val:
                        evtInd = int(m.group('i1'))
                        sessInd = int(m.group('i2'))
                        session = self.findJudgeEvent(evtInd).findSession(sessInd)
                        session.assignTeam(self.findTeam(int(m.group('i3'))))

        return

    def assignFakeSchedule(self):
        it = 0
        nt = len(self.teams)
        for m in self.matchList.matches:
            for ii in range(2):
                m.assignTeam(self.teams[it])
                it = (it + 1) % nt

        it = 0
        for evt in self.judgeEvents.values():
            for s in evt.sessions:
                for r in s.event.rooms:
                    if it < len(self.teams):
                        s.assignTeam(self.teams[it])
                        it += 1
        return

# ====================================================================================================


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='FLL Schedule creater')
    parser.add_argument('-b', '--build', action='store_true', help='Build model file')
    parser.add_argument('-o', '--output', help='Formatted output base name')
    parser.add_argument('-m', '--matches', action='store_true', help='Output (empty) match schedule')
    parser.add_argument('-j', '--judging', action='store_true', help='Output (empty) judge schedule')
    parser.add_argument('configfile', help='Config file (python)')
    parser.add_argument('resultfile', nargs='?', help='Model result file')

    args = parser.parse_args()

    # Load the configuration file
    config = {}
    with open(args.configfile, 'rb') as file:
        exec(file.read(), None, config)

    # seed the random generator
    seed()

    model = ScheduleModel(config)

    # for e in model.judgeEvents['Judging'].subSchedule.items():
    #     print(e)
    # sys.exit(1)

    if args.build:
        model.writeModel()

    elif args.matches:
        model.assignFakeSchedule()
        model.outputMatches()

    elif args.judging:
        model.assignFakeSchedule()
        model.outputJudging()

    elif args.output:
        model.formatOutput(args.output, args.resultfile)

    else:
        parser.print_help()
