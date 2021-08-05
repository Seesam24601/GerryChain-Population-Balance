#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Created 4 August 2020

Program to determine the percentage deviation from the proportional number of
seats won.

Program by Charlie Murphy
'''

from calc_fracwins_comp import calc_fracwins_comp

# Disproportionality as calculated using Dave's
def prop_dev(partition, composite, electionvol, proportional_seats):

    seats_num = len(partition)
    wins = calc_fracwins_comp(partition, composite, electionvol)

    return abs(proportional_seats - wins) / seats_num

# Disproportionality, but calculated using fractional 
def prop_frac_dev(partition, composite, electionvol, vote_share):

    seats_num = len(partition)
    proportional_seats = vote_share * seats_num

    return prop_dev(partition, composite, electionvol, proportional_seats)