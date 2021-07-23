#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Default input file for fracking_reduction

Program by Charlie Murphy
'''

# File Names
my_electiondatafile = r'C:\Users\charl\Box\Internships\Gerry Chain\States\Ohio\OH 2018 & 2020 Elections\OH_2020_censusvtds.shp'
ex_dist_name = 'OH_assignment_pop_4.918.txt'

# State Attributes
state = 'OH'
popkey = 'POP19'
geotag = 'GEOID10'
my_apportionment = 'assignment'

# Chain Attributes
markovchainlength = 1000
poptol = .005
win_margin = 0.5
electionvol = 0.06
boundary_margin = 0.5

# Pool Attributes
# poolsize = 10
# time_interval = 30
