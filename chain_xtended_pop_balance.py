#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Created 24 June 2020
Program designed to use gerrychain to improve population balance of a 
redistricting plan.

Program by Charlie Murphy based on code by Dinos Gonatas
'''

from gerrychain.constraints import Validator, deviation_from_ideal
from gerrychain import updaters
from calc_fracwins_comp import calc_fracwins_comp

# Population Deviation
def pop_deviation(partition):
    deviation = deviation_from_ideal(partition)
    key_max = max(deviation.keys(), key = (lambda k: deviation[k]))
    key_min = min(deviation.keys(), key = (lambda k: deviation[k]))
    popdev = abs(deviation[key_max] + abs(deviation[key_min]))
    return popdev

# Return County Field
def get_county_field(partition):

    fieldlist = partition.graph.nodes[0].keys()   #get LIST OF FIELDS
    
    if 'COUNTYFP10' in fieldlist:
        county_field = 'COUNTYFP10'
    elif 'CTYNAME' in fieldlist:
        county_field = 'CTYNAME'
    elif 'COUNTYFIPS' in fieldlist:
        county_field = 'COUNTYFIPS'
    elif 'COUNTYFP' in fieldlist:
        county_field = 'COUNTYFP'
    elif 'cnty_nm' in fieldlist:
        county_field = 'cnty_nm'
    elif 'county_nam' in fieldlist:
        county_field = 'county_nam'
    elif 'FIPS2' in fieldlist:
        county_field = 'FIPS2'
    elif 'County' in fieldlist:
        county_field = 'County'
    elif 'FIPS' in fieldlist:
        county_field = 'FIPS'
    elif 'CNTY_NAME' in fieldlist:
        county_field = 'CNTY_NAME'
    elif 'COUNTY' in fieldlist:
        county_field = 'COUNTY'
    else:
        print("no county ID info in shapefile\n")
        county_field = None
    
    return county_field    
        
class MarkovChain_xtended_pop_balance:

    def __init__(self, proposal, constraints, accept, initial_state, 
        total_steps, election_composite, win_margin, win_volatility,
        boundary_margin):

        if callable(constraints):
            is_valid = constraints
        else:
            is_valid = Validator(constraints)

        if not is_valid(initial_state):
            failed = [
                constraint
                for constraint in is_valid.constraints
                if not constraint(initial_state)
            ]
            message = (
                "The given initial_state is not valid according is_valid. "
                "The failed constraints were: " + ",".join([f.__name__ for f in failed])
            )
            self.good = 0
            raise ValueError(message)

        self.proposal = proposal
        self.is_valid = is_valid
        self.accept = accept
        self.good = 1
        self.total_steps = total_steps
        self.initial_state = initial_state
        self.state = initial_state
        self.old_popdev = pop_deviation(self.state)

        self.election_composite = election_composite
        self.win_margin = win_margin
        self.win_volatility = win_volatility
        self.boundary_margin = boundary_margin

    def __iter__(self):
        self.counter = 0
        self.state = self.initial_state
        self.good=1
        self.fit = 1
        return self

    def plan_criteria(self, proposed_next_state):
        new_wins = calc_fracwins_comp(proposed_next_state, self.election_composite, self.win_volatility)
        old_wins = calc_fracwins_comp(self.state, self.election_composite, self.win_volatility)
        new_le_oldwins = new_wins <= old_wins * (1 + self.win_margin)
        
        new_bdrylength = len(proposed_next_state["cut_edges"])
        old_bdrylength = len(self.state["cut_edges"])
        new_le_oldlength = new_bdrylength <= old_bdrylength * (1 + self.boundary_margin)

        return (self.merged_splits and new_le_oldlength and new_le_oldwins)

    def county_splits(self, proposed_next_state):
        
        edge = max(self.state["cut_edges"], key=lambda x: 
        abs(abs(self.state["population"][self.state.assignment[x[1]]]) - 
        abs(self.state["population"][self.state.assignment[x[0]]])) )

        d1 = self.state.assignment[edge[0]]
        d2 = self.state.assignment[edge[1]]

        county_field = get_county_field(proposed_next_state)
        gg = updaters.county_splits(proposed_next_state, county_field)
        gg_res = gg(proposed_next_state)

        merged_district_count = 0
        split_count = 0
        for x in gg_res:
            split_count += len(gg_res[x].contains) -1
            if d1 in gg_res[x].contains and d2 in gg_res[x].contains:
                merged_district_count += 1

        self.splits = split_count
        self.merged_splits = merged_district_count <= 1


    def __next__(self):

        if self.counter == 0:
            self.counter += 1
            self.good = 1
            return self

        while self.counter < self.total_steps:

            proposed_next_state = self.proposal(self.state)
            self.new_popdev = pop_deviation(proposed_next_state)

            # Erase the parent of the parent, to avoid memory leak
            self.state.parent = None
            self.good = 0

            if self.is_valid(proposed_next_state) and self.accept(proposed_next_state):

                self.county_splits(proposed_next_state)

                if (self.plan_criteria(proposed_next_state) and 
                    self.old_popdev > self.new_popdev):
                    self.old_popdev = self.new_popdev
                    self.state = proposed_next_state
                    self.good = 1
                   
                self.counter += 1
                return self
        raise StopIteration

    def __len__(self):
        return self.total_steps

    def __repr__(self):
        return "<MarkovChain [{} steps]>".format(len(self))

    def with_progress_bar(self):
        from tqdm.auto import tqdm

        return tqdm(self)
