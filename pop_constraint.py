#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Population constraint that uses the same population deviation calculation used
in Dave's Redistricting App

Program by Charlie Murphy
'''

from gerrychain.constraints import deviation_from_ideal

# Population Deviation
def pop_deviation(partition):
    deviation = deviation_from_ideal(partition)
    key_max = max(deviation.keys(), key = (lambda k: deviation[k]))
    key_min = min(deviation.keys(), key = (lambda k: deviation[k]))
    popdev = abs(deviation[key_max] + abs(deviation[key_min]))
    return popdev

# Population Constraint
def pop_constraint(max_pop_deviation):
    return lambda p: pop_deviation(p) <= max_pop_deviation