#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Created 4 August 2020

Program by Charlie Murphy
'''

# File Names
my_electiondatafile = r'C:\Users\charl\Box\Internships\Gerry Chain\States\Ohio\OH 2018 & 2020 Elections\OH_2020_censusvtds.shp'
ex_dist_name = 'OH_assignment_pop_0.0977_frack_7_smooth_1907_splits_35_5_43.txt'

# State Attributes
state = 'OH'
popkey = 'POP19'
geotag = 'GEOID10'
my_apportionment = 'assignment'

# Chain Attributes
markovchainlength = 5000
poptol = .06
max_pop_deviation = 0.1

# Pool Attributes
poolsize = 6
time_interval = 30
