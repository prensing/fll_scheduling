#!/bin/bash

#/home/scratch/builds/glpk-4.60/examples/glpsol --math --model ../fllschedule.mod --data fllschedule.dat --output result.txt

# did not finish in many hours
#export LD_LIBRARY_PATH=/usr/local/bin/lp_solve
#/usr/local/bin/lp_solve/lp_solve -time -v6 -stat -rxli xli_MathProg ../fllschedule.mod -rxlidata fllschedule.dat 2>&1 | tee result.txt

#/scratch/build/Cbc/Cbc/src/cbc fllschedule.mod% -randoms $(($RANDOM * 10000 + $RANDOM)) -threads 6 -solve -stat -solution result.txt

datestamp=$(date +%Y%m%d_%H%M)
stdbuf -o 0 /scratch/build/Cbc/Cbc/src/cbc -threads 6 -slog 2 -import ${1}% -solve -stat -solution result.txt | tee solve_${datestamp}.log
