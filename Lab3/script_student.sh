#!/bin/bash

python3 Emulator/emulator.py TestConfig/config1.ini &
sleep 0.5
cd "Student Code/student" || exit
make run-receiver config=../../TestConfig/config1.ini &
sleep 0.25
make run-sender config=../../TestConfig/config1.ini