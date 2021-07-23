#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Created 24 June 2020
Program designed to use gerrychain to reduce the number of fracked counties and
cut edges.

Program by Charlie Murphy
'''

from gerrychain import (GeographicPartition, Partition, Graph,
    MarkovChain_xtended_fracking, proposals, updaters, constraints, accept,
    Election)
from gerrychain.proposals import recom_frack
from functools import partial
import pandas
import geopandas
from get_electioninfo import get_elections
import district_list as dl
from fracking import get_fracks

# Load files and combine into a single dataframe
exec(open("./input_templates/pop_balance_input.py").read())
df = geopandas.read_file(my_electiondatafile) 
exec(open("splice_assignment_fn.py").read())
graph = graph_PA

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
proposal = partial(recom_frack, pop_col = popkey, epsilon = poptol, 
    node_repeats = 2)

# Run Markov Chain
chain = MarkovChain_xtended_fracking(proposal = proposal,
    constraints = my_constraints, accept = accept.always_accept,
    initial_state = initial_partition, total_steps = markovchainlength,
    election_composite = composite, win_margin = win_margin,
    win_volatility = electionvol, boundary_margin = boundary_margin)

# Return files of valid plans
for part in chain.with_progress_bar():
    if part.good == 1 and part.counter != 1:
        filename = 'redist_data/example_districts/' + state + '_' + \
            my_apportionment + '_frack_' + str(part.new_fracks) + \
            '_splits_' + str(part.splits) + \
            '_' + str(part.counter) + '.txt'
        dl.part_dump(part.state, filename)
    
    if part.counter > markovchainlength:
       break