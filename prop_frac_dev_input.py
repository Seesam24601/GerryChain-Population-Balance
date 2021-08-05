#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Created 4 August 2020

Program by Charlie Murphy
'''

# File Names
my_electiondatafile = r'C:\Users\charl\Box\Internships\Gerry Chain\States\Texas\Combined Level 1\TX_2020_censusvtds.shp'
ex_dist_name = 'TX_smoothed.csv'

# State Attributes
state = 'TX'
popkey = 'POP19'
geotag = 'GEOID10'
my_apportionment = 'assignment'

# Chain Attributes
markovchainlength = 100000
poptol = .005
electionvol = 0.06
max_pop_deviation = 0.0075
vote_share = 0.4627

# Pool Attributes
poolsize = 6
time_interval = 30
