#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Created 24 July 2020
Program designed to use gerrychain to improve population balance of a 
redistricting plan.

Program by Charlie Murphy
'''

from gerrychain import (GeographicPartition, Partition, Graph,
    MarkovChain_xtended_pop_balance,proposals, updaters, constraints, accept,
    Election)
from gerrychain.proposals import recom_merge
from gerrychain.constraints import deviation_from_ideal
from functools import partial
import pandas
import geopandas
from get_electioninfo import get_elections
import district_list as dl
import random
import os
from multiprocessing import freeze_support, get_context, Value, Manager
import time
from pop_constraint import pop_deviation

# Multichian Run
def multi_chain(i1, graph, state, popkey, poptol, markovchainlength, win_margin,
    electionvol, boundary_margin, my_apportionment, best_pop, geotag, ns,
    time_interval):

    # Limit the total number of plans to markovchainlength
    count = 0
    first_time = True
    while count < markovchainlength:

        # Set everything up if this is the first time this processor has run
        if first_time:

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
            my_constraints = [compactness_bound, contiguous_parts]

            # Create a Proposal
            proposal = partial(recom_merge, pop_col = popkey, epsilon = poptol, 
                node_repeats = 2)

            first_time = False

        # Run Markov Chain
        chain = MarkovChain_xtended_pop_balance(proposal = proposal,
            constraints = my_constraints, accept = accept.always_accept,
            initial_state = initial_partition, total_steps = markovchainlength,
            election_composite = composite, win_margin = win_margin,
            win_volatility = electionvol, boundary_margin = boundary_margin)

        # Set the best population deviation to the initial value
        best_pop_i1 = pop_deviation(initial_partition)

        # Set the next time that the processor will check other's progress.
        # time_interval is in seconds
        check_time = time.time() + time_interval

        # Loop through markovchain
        for part in chain:
            count += 1

            if part.counter != 1:

                # Create a file of the plan if the plan reduces population deviation
                if part.good == 1 and best_pop.value > part.new_popdev:
                    filename = 'redist_data/example_districts/' + state + '_' + \
                        my_apportionment + '_pop_' + \
                        str(round((part.new_popdev * 100), 4)) + \
                        '_splits_' + str(part.splits) + \
                        '_' + str(i1) + '_' + str(count) + '.txt'
                    dl.part_dump(part.state, filename)

                    # Set the values to reflect the new lowest population deviation
                    best_pop.value = best_pop_i1 = part.new_popdev
                    ns.assignment = part.state.assignment

                # At each time interval, check if another processor has a better
                # plan. If so, restart the markovchain
                if time.time() > check_time:
                    if best_pop.value < best_pop_i1:
                        initial_partition = GeographicPartition(graph, 
                            assignment = ns.assignment, updaters = my_updaters)
                        break            
                    check_time = time.time() + time_interval       

                # End chain after the correct number of iterations
                if count > markovchainlength:
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

    # Updaters
    elections, composite = get_elections(state)
    my_updaters = {"population": updaters.Tally(popkey, alias = "population")}
    election_updaters = {election.name: election for election in elections}
    my_updaters.update(election_updaters)

    # Create Initial Partition
    initial_partition = GeographicPartition(graph, assignment = my_apportionment,
        updaters = my_updaters)

    # Value in shared memory
    start_pop = pop_deviation(initial_partition)
    manager = Manager()
    best_pop = manager.Value('d', start_pop)

    ns = manager.Namespace()
    ns.assignment = initial_partition.assignment

    # Run in parallel
    ctx = get_context("spawn")
    p = ctx.Pool(poolsize)

    updated_vals = p.starmap(multi_chain, [(i1, graph, state, popkey, poptol, 
        markovchainlength, win_margin, electionvol, boundary_margin, 
        my_apportionment, best_pop, geotag, ns, time_interval) 
        for i1 in range(poolsize)])