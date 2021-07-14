#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Created 24 June 2020
Program designed to use gerrychain to improve population balance of a 
redistricting plan.

Program by Charlie Murphy
'''

from gerrychain import (GeographicPartition, Partition, Graph,
    MarkovChain_xtended_pop_balance,proposals, updaters, constraints, accept,
    Election)
from gerrychain.proposals import recom_pop
from functools import partial
import pandas
import geopandas
from get_electioninfo import get_elections
import district_list as dl
import random
import os
from multiprocessing import freeze_support, get_context

# Multichian Run
def multi_chain(i1, graph, state, popkey, poptol, markovchainlength, win_margin,
    electionvol, boundary_margin, my_apportionment):

    # Random Seed
    random.seed(os.urandom(10)*i1) 

    # Updaters
    elections, composite = get_elections(state)
    my_updaters = {"population": updaters.Tally(popkey, alias = "population")}
    election_updaters = {election.name: election for election in elections}
    my_updaters.update(election_updaters)

    # Create Initial Partition
    initial_partition = GeographicPartition(graph, assignment = my_apportionment,
        updaters = my_updaters)

    # Compactness and Contiguity Constraints
    compactness_bound = constraints.UpperBound(lambda p: len(p["cut_edges"]),
        2*len(initial_partition["cut_edges"]))
    contiguous_parts = lambda p: constraints.contiguous(p)
    my_constraints = [contiguous_parts, compactness_bound]

    # Create a Proposal
    proposal = partial(recom_pop, pop_col = popkey, epsilon = poptol, 
        node_repeats = 2)

    # Run Markov Chain
    chain = MarkovChain_xtended_pop_balance(proposal = proposal,
    constraints = my_constraints, accept = accept.always_accept,
    initial_state = initial_partition, total_steps = markovchainlength,
    election_composite = composite, win_margin = win_margin,
    win_volatility = electionvol, boundary_margin = boundary_margin)

    # Return files of valid plans
    for part in chain:
        if part.good == 1 and part.counter != 1:
            filename = 'redist_data/example_districts/' + state + '_' + \
                my_apportionment + '_pop_' + str(round((part.new_popdev * 100), 4)) + \
                '_splits_' + str(part.splits) + \
                '_' + str(i1) + '_' + str(part.counter) + '.txt'
            dl.part_dump(part.state, filename)
        
        if part.counter > markovchainlength:
            break

    return i1

# Setup
if __name__ == '__main__':
    freeze_support()

    # Load files and combine into a single dataframe
    exec(open("./input_templates/pop_balance_input.py").read())
    df = geopandas.read_file(my_electiondatafile) 
    exec(open("splice_assignment_fn.py").read())
    graph = graph_PA

    # Run in parallel
    poolsize = 10
    ctx = get_context("spawn")
    p = ctx.Pool(poolsize)

    updated_vals = p.starmap(multi_chain, [(i1, graph, state, popkey, poptol, 
        markovchainlength, win_margin, electionvol, boundary_margin, 
        my_apportionment) for i1 in range(poolsize)])