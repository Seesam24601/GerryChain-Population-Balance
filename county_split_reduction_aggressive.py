#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Created 4 August 2020

Program to reduce the number of county splits in a redistricting plan using
gerrychain

Program by Charlie Murphy
'''

from gerrychain import (GeographicPartition, Partition, Graph,
    MarkovChain_xtended, proposals, updaters, constraints, accept,
    Election)
from gerrychain.proposals import recom
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
from total_splits import total_splits

# Multichian Run
def multi_chain(i1, graph, state, popkey, poptol, markovchainlength, maxsplits,
    my_apportionment, best_splits, geotag, ns, time_interval, max_pop_deviation):

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

            # Create a Proposal
            ideal_population = sum(list(initial_partition["population"].values())) / len(initial_partition)
            proposal = partial(recom, pop_col = popkey, pop_target = ideal_population,
                epsilon = poptol, node_repeats = 2)

            # Constraints
            compactness_bound = constraints.UpperBound(lambda p: len(p["cut_edges"]),
                2*len(initial_partition["cut_edges"]))
            contiguous_parts = lambda p: constraints.contiguous(p)
            my_constraints = [compactness_bound, contiguous_parts,
                pop_constraint(max_pop_deviation)]

            first_time = False

        # Run Markov Chain
        chain = MarkovChain_xtended(proposal = proposal,
            constraints = my_constraints, accept = accept.always_accept,
            initial_state = initial_partition, total_steps = markovchainlength,
            maxsplits = maxsplits)

        # Set the best population deviation to the initial value
        best_splits_i1 = total_splits(initial_partition)

        # Set the next time that the processor will check other's progress.
        # time_interval is in seconds
        check_time = time.time() + time_interval

        # Loop through markovchain
        for part in chain:
            count += 1

            if part.counter != 1:

                # Create a file of the plan if the plan reduces population deviation
                if part.good == 1:
                    current_splits = total_splits(part.state)

                    if best_splits.value > current_splits:
                        filename = 'redist_data/example_districts/' + state + '_' + \
                            my_apportionment + '_splits_' + str(current_splits) + \
                            '_' + str(i1) + '_' + str(count) + '.txt'
                        dl.part_dump(part.state, filename)

                        # Set the values to reflect the new lowest population deviation
                        best_splits.value = best_splits_i1 = current_splits
                        ns.assignment = part.state.assignment

                # At each time interval, check if another processor has a better
                # plan. If so, restart the markovchain
                if time.time() > check_time:
                    if best_splits.value < best_splits_i1:
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
    exec(open("./input_templates/county_splits_input.py").read())
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
    maxsplits = total_splits(initial_partition)
    manager = Manager()
    best_splits = manager.Value('d', maxsplits)

    ns = manager.Namespace()
    ns.assignment = initial_partition.assignment

    # Run in parallel
    ctx = get_context("spawn")
    p = ctx.Pool(poolsize)

    updated_vals = p.starmap(multi_chain, [(i1, graph, state, popkey, poptol, 
        markovchainlength, maxsplits, my_apportionment, best_splits, geotag, ns, 
        time_interval, max_pop_deviation) for i1 in range(poolsize)])