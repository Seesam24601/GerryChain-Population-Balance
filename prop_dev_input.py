#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Created 4 August 2020

Program by Charlie Murphy
'''

# File Names
my_electiondatafile = r'C:\Users\charl\Box\Internships\Gerry Chain\States\Texas\Combined Level 1\TX_2020_censusvtds.shp'
ex_dist_name = 'TX_start.csv'

# State Attributes
state = 'TX'
popkey = 'POP19'
geotag = 'GEOID10'
my_apportionment = 'assignment'

# Chain Attributes
markovchainlength = 1000
poptol = .005
electionvol = 0.06
maxsplits = 37
max_pop_deviation = 0.0075
proportional_seats = 18

# Pool Attributes
poolsize = 6
time_interval = 30
