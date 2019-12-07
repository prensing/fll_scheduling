#!/usr/bin/env python

startTime = '9:00'
travelTime = 19


# judged events
# columns are: name, rooms, time, breakTime, extraSessions
judgeEvents = (
    {'name': 'Judging',
     'sessionLen': 50,
     'sessionBreak': 10,
     'rooms': range(9),  # just need to indicate how many rooms total
     'breakTimes': (('12:00', '12:30'), ),
     # extend the final session (into lunch) so that the last teams get a later match after lunch
     # 'extendLastSession': 30,
     'subEvents': {
         'sessionLen': 10,
         'sessionBreak': 10,
         'events': (
             {'name': 'Technical',
              'rooms': ('Rm 102', 'Rm 110', 'Rm X1'), },
             {'name': 'CoreValues',
              'rooms': ('Rm 205', 'Rm 209', 'Rm X2'), },
             {'name': 'Project',
              'rooms': ('Rm 210', 'Rm 214', 'Rm X3'), },
         ), },
     },
)

matchInfo = {
    'matchLen': 5,
    'matchBreak': 0,
    'gamesPerTeam': 5,
    'tableNames': (('Blue', 'Green'), ('Red', 'Purple')),
    'extraMatches': 0,
    'maxTeamMatchesPerFields': 3,
    # 'resetAfterBreak': ('13:30', ),
    # 'oneFieldOnly': ('12:12', '12:24'),
    'extendSessions': (
        ('09:35', '09:45', 10),
        ('10:35', '10:45', 10),
    ),
    'breakTimes': (
        ('09:45', '10:00'),
        ('10:45', '11:00'),
        ('11:45', '12:30'),
    )
}

# Schedule blocks.
# Scheduling will require each team to have >=1 match or do judging in each group
# ### Cannot fully contrain it so leave one block "free"
scheduleBlocks = (
    ('9:00', '10:00', ('Judging',)),
    ('10:00', '11:00', ('Judging',)),
    ('11:00', '12:00', ('Judging',)),
    # ('12:00', '13:00'),
    ('13:15', '14:00', ()),
)

# Team Numbers
teams = (
    (1, 'Team 1'),
    (2, 'Team 2'),
    (3, 'Team 3'),
    (4, 'Team 4'),
    (5, 'Team 5'),
    (6, 'Team 6'),
    (7, 'Team 7'),
    (8, 'Team 8'),
    (9, 'Team 9'),
    (10, 'Team 10'),
    (11, 'Team 11'),
    (12, 'Team 12'),
    (13, 'Team 13'),
    (14, 'Team 14'),
    (15, 'Team 15'),
    (16, 'Team 16'),
    (17, 'Team 17'),
    (18, 'Team 18'),
    (19, 'Team 19'),
    (20, 'Team 20'),
    (21, 'Team 21'),
    (22, 'Team 22'),
    (23, 'Team 23'),
    (24, 'Team 24'),
    (25, 'Team 25'),
    (26, 'Team 26'),
    (27, 'Team 27'),
    (28, 'Team 28'),
    (29, 'Team 29'),
    (30, 'Team 30'),
    (31, 'Team 31'),
    (32, 'Team 32'),
    (33, 'Team 33'),
    (34, 'Team 34'),
    (35, 'Team 35'),
    (36, 'Team 36'),
)
