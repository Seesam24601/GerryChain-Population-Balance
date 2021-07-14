#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Created 24 June 2020

Program by Charlie Murphy
'''

# File Names
my_electiondatafile = r'C:\Users\charl\Box\Internships\Gerry Chain\States\Ohio\OH 2018 & 2020 Elections\OH_2020_censusvtds.shp'
# ex_dist_name = 'OH_CD/OH_CD_SEN16_gt__3.5973_smoothfrac_r_1057.txt'
ex_dist_name = 'OH_District_pop_1.7988_splits_23_590.txt'

# State Attributes
state = 'OH'
popkey = 'POP19'
geotag = 'GEOID20'
my_apportionment = 'District'

# Chain Attributes
markovchainlength = 1000
poptol = .005
win_margin = 0.1
electionvol = 0.06
boundary_margin = 0.1
