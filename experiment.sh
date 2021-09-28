#!/bin/bash
export COLLECT_DATA="false"

echo "RUNNING WITH GC"
echo
echo

export GC_ACTIVE="true"
for i in $(seq 10000 10000 100000)
do
  export SIM_DURATION=$i
  echo "BEGIN $i with GC"
  time python3 main.py > /dev/null
  echo "END $i with GC"
  echo "=============="
  echo
done

echo 
echo
echo "RUNNING WITHOUT GC"
echo
echo

export GC_ACTIVE="false"
for i in $(seq 10000 10000 100000)
do
  export SIM_DURATION=$i
  echo "BEGIN $i without GC"
  time python3 main.py > /dev/null
  echo "END $i without GC"
  echo "=============="
  echo
done