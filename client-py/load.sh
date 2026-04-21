#!/bin/sh
#
# Create 4 processes that take 100% CPU each.

startall() {
    for i in `seq 4`; do
	(while true; do true; done) &
	(while true; do true; done) &
	sleep 1
    done
}


ctrl_c() {
    pkill -P $$
    exit
}

trap ctrl_c INT

while true; do
    startall
    sleep 1
    pkill -P $$

    sleep 2
done
