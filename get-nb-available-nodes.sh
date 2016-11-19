#!/bin/bash

experiment-cli info -l --site $HOSTNAME | grep m3- -A2 | grep Alive | wc -l
