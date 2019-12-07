#!/usr/bin/env python

startTime = '9:00'
travelTime = 19


# judged events
# columns are: name, rooms, time, breakTime, extraSessions
judgeEvents = (
    {'name': 'Judging',
     'sessionLen': 50,
     'sessionBreak': 10,
     'rooms': range(12),
     'breakTimes': (('12:00', '12:30'), ),
     # extend the final session (into lunch) so that the last teams get a later match after lunch
     # 'extendLastSession': 30,
     'subEvents': {
         'sessionLen': 10,
         'sessionBreak': 10,
         'events': (
             {'name': 'CoreValues',
              'rooms': ('Rm 201', 'Rm 205', 'Rm 209', 'Rm 213'), },
             {'name': 'Project',
              'rooms': ('Rm 210', 'Rm 214', 'Rm 216', 'Rm 218'), },
             {'name': 'Technical',
              'rooms': ('Rm 102', 'Rm 103', 'Rm 105', 'Rm 110'), },
         ), },
     },
)

matchInfo = {
    'matchLen': 4,
    'matchBreak': 0,
    'gamesPerTeam': 5,
    'extraMatches': 0,
    'tableNames': (('Blue', 'Green',), ('Red', 'Purple',), ),
    'maxTeamMatchesPerFields': 2,
    'extendSessions': (
        ('09:35', '09:48', 10),
        ('10:35', '10:48', 10),
    ),
    'breakTimes': (
        ('09:48', '10:00'),
        ('10:48', '11:00'),
        ('11:48', '12:30'),
        # ('13:18', '13:30'),
    )
}

# Schedule blocks.
# Scheduling will require each team to have >=1 match or do judging in each group
# ### Cannot fully contrain it so leave one block "free"
scheduleBlocks = (
    ('9:00', '10:00', ('Judging',)),
    ('10:00', '11:00', ('Judging',)),
    ('11:00', '12:00', ('Judging',)),
    # ('12:30', '13:30'),
    ('13:18', '14:30', ()),
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
    (37, 'Team 37'),
    (38, 'Team 38'),
    (39, 'Team 39'),
    (40, 'Team 40'),
    (41, 'Team 41'),
    (42, 'Team 42'),
    (43, 'Team 43'),
    (44, 'Team 44'),
    (45, 'Team 45'),
    (46, 'Team 46'),
    (47, 'Team 47'),
    (48, 'Team 48'),
)
