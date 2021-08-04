#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Default input file for combined_workflow

Program by Charlie Murphy
'''

# File Names
my_electiondatafile = r'C:\Users\charl\Box\Internships\Gerry Chain\States\Texas\Combined Level 1\TX_2020_censusvtds.shp'
ex_dist_name = 'TX_start.csv'

# State Attributes
state = 'TX'
popkey = 'POP19'
geotag = 'GEOID20'
my_apportionment = 'assignment'

# Chain Attributes
markovchainlength = 1000
poptol = 0.06
electionvol = 0.06
max_pop_deviation = 0.0075

# This is the percentage change in the fractional seat share that will be
# allowed at each step of the Markov Chain. Decreasing this value will decrease
# the change in partisan outcomes, but will also make the program run slower and
# possibly reduce the amount of smoothing allowed.
win_margin = 0.1

# Smoothing
cutoff = 100
margin = 0.001

# Pool Attributes
poolsize = 6
time_interval = 20