# fll_scheduling
Create schedules for an FLL tournament with Integer Programming

This project creates FLL tournament schedules. It uses "Integer Programming" to meet all
the constraints. It is kind of gross overkill, but it let me play with IP while doing
something useful.

The Python code reads in a config file and produces the problem in the format of
a GMPL (a.k.a. MathProg) problem.

The solver used is CBC from the COIN-OR project.

Note that I am *not* an Operations Researcher. I fully admit this is a hack. If you have
suggestions on improving it, especially solving it faster, I would welcome the advise.