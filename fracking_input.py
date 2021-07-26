#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Default input file for fracking_reduction

Program by Charlie Murphy
'''

# File Names
my_electiondatafile = r'C:\Users\charl\Box\Internships\Gerry Chain\States\Ohio\OH 2018 & 2020 Elections\OH_2020_censusvtds.shp'
ex_dist_name = 'fracking_test.csv'

# State Attributes
state = 'OH'
popkey = 'POP19'
geotag = 'GEOID20'
my_apportionment = 'District'

# Chain Attributes
markovchainlength = 500
poptol = 0.01
win_margin = 0.5
electionvol = 0.06
boundary_margin = 0.5
max_pop_deviation = 0.0075

# Pool Attributes
poolsize = 6
time_interval = 10
