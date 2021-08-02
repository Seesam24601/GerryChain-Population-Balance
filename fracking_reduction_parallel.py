#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Created 24 July 2020
Program designed to use gerrychain to reduce the number of fracked counties.

Program by Charlie Murphy
'''

from gerrychain import (GeographicPartition, Partition, Graph,
    MarkovChain_xtended_fracking, proposals, updaters, constraints, accept,
    Election)
from gerrychain.proposals import recom_frack
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
from pop_constraint import pop_constraint
from fracking import fracking

# Multichian Run
def multi_chain(i1, graph, state, popkey, poptol, markovchainlength, win_margin,
    electionvol, boundary_margin, my_apportionment, best, geotag, ns,
    time_interval, max_pop_deviation):

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

            # Constraints
            compactness_bound = constraints.UpperBound(lambda p: len(p["cut_edges"]),
                2*len(initial_partition["cut_edges"]))
            contiguous_parts = lambda p: constraints.contiguous(p)
            my_constraints = [contiguous_parts, compactness_bound,
                pop_constraint(max_pop_deviation)]

            # Create a Proposal
            proposal = partial(recom_frack, pop_col = popkey, epsilon = poptol, 
                node_repeats = 2)

            first_time = False

        # Run Markov Chain
        chain = MarkovChain_xtended_fracking(proposal = proposal,
            constraints = my_constraints, accept = accept.always_accept,
            initial_state = initial_partition, total_steps = markovchainlength,
            election_composite = composite, win_margin = win_margin,
            win_volatility = electionvol, boundary_margin = boundary_margin)

        # Set the best population deviation to the initial value
        best_i1 = fracking(initial_partition)

        # Set the next time that the processor will check other's progress.
        # time_interval is in seconds
        check_time = time.time() + time_interval

        # Loop through markovchain
        for part in chain:
            count += 1

            if part.counter != 1:

                # Create a file of the plan if the plan reduces population deviation
                if part.good == 1 and best.value > part.new_fracks:
                    filename = 'redist_data/example_districts/' + state + '_' + \
                        my_apportionment + '_frack_' + str(part.new_fracks) + \
                        '_worker_' + str(i1) +'_run_' + str(part.counter) + '.txt'
                    dl.part_dump(part.state, filename)

                    # Set the values to reflect the new lowest population deviation
                    best_i1 = part.new_fracks
                    best.value = best_i1
                    ns.assignment = part.state.assignment
                    
                    if best.value == 0:
                        return i1 

                # At each time interval, check if another processor has a better
                # plan. If so, restart the markovchain
                if time.time() > check_time:
                    if best.value < best_i1:
                        if best.value == 0:
                            return i1  
                        initial_partition = GeographicPartition(graph, 
                            assignment = ns.assignment, updaters = my_updaters)
                        break            
                    check_time = time.time() + time_interval  

    return i1

# Setup
if __name__ == '__main__':
    freeze_support()

    # Load files and combine into a single dataframe
    exec(open("./input_templates/fracking_input.py").read())
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
    start = fracking(initial_partition)
    manager = Manager()
    best = manager.Value('d', start)

    ns = manager.Namespace()
    ns.assignment = initial_partition.assignment

    # Run in parallel
    ctx = get_context("spawn")
    p = ctx.Pool(poolsize)

    updated_vals = p.starmap(multi_chain, [(i1, graph, state, popkey, poptol, 
        markovchainlength, win_margin, electionvol, boundary_margin, 
        my_apportionment, best, geotag, ns, time_interval, max_pop_deviation) 
        for i1 in range(poolsize)])