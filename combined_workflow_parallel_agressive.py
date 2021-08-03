#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Created 3 August 2020

Program to balance population, eliminate fracks, and reduce cut_edges to improve
compactness all in a single step.

Program by Charlie Murphy
'''

from gerrychain import (GeographicPartition, Partition, Graph,
    MarkovChain_xtended_combined_workflow, proposals, updaters, constraints, accept,
    Election)
from gerrychain.proposals import recom_frack, recom_merge, recom
from functools import partial
import pandas
import geopandas
from get_electioninfo import get_elections
import district_list as dl
from fracking import fracking
from pop_constraint import pop_constraint, pop_deviation
from total_splits import total_splits
from multiprocessing import freeze_support, get_context, Value, Manager
import time
import random
import os

# Multichian Run
def multi_chain(i1, graph, state, popkey, poptol, markovchainlength, win_margin,
    electionvol, cutoff, margin, my_apportionment, best_pop, best_stage, 
    best_frack, best_smooth, geotag, ns, time_interval, max_pop_deviation):

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

            # Max Splits
            max_splits = total_splits(initial_partition)

            first_time = False
            stage = 0

        # Constraints
        contiguous_parts = lambda p: constraints.contiguous(p)
        my_constraints = [contiguous_parts]
        if stage >= 1:
            my_constraints.append(pop_constraint(max_pop_deviation))
        if stage == 2:
            fracking_constraint = lambda p: fracking(p) == 0
            my_constraints.append(fracking_constraint)

        # Create a Proposal
        if stage == 0:
            proposal = partial(recom_merge, pop_col = popkey, epsilon = poptol,  
                node_repeats = 2)
        elif stage == 1:
            proposal = partial(recom_frack, pop_col = popkey, epsilon = poptol,  
                node_repeats = 2)
        else:
            ideal_population = sum(list(initial_partition["population"].values())) / len(initial_partition)
            proposal = partial(recom, pop_col=popkey, pop_target=ideal_population,
                epsilon=poptol, node_repeats=2)

        # Run Markov Chain
        chain = MarkovChain_xtended_combined_workflow(proposal = proposal,
            constraints = my_constraints, accept = accept.always_accept,
            initial_state = initial_partition, total_steps = markovchainlength,
            election_composite = composite, win_margin = win_margin,
            win_volatility = electionvol, cutoff = cutoff, margin = margin,
            stage = stage, max_splits = max_splits)

        # Set initial values
        best_pop_i1 = pop_deviation(initial_partition)
        best_frack_i1 = fracking(initial_partition)
        best_smooth_i1 = len(initial_partition['cut_edges'])

        # Set the next time that the processor will check other's progress.
        # time_interval is in seconds
        check_time = time.time() + time_interval

        # Loop through markovchain
        for part in chain:
            count += 1

            if part.counter != 1:

                # Create a file of the plan if the plan reduces population deviation
                if (part.good == 1 and best_stage.value == stage and 
                    ((stage == 0 and best_pop.value > part.new_popdev) or
                    (stage == 1 and best_frack.value > part.new_fracks) or
                    (stage == 2 and best_smooth.value > len(part.state['cut_edges'])))):

                    filename = 'redist_data/example_districts/' + state + '_' + \
                        my_apportionment + '_pop_' + str(round(part.new_popdev, 4)) + \
                        '_frack_' + str(part.new_fracks) + \
                        '_smooth_' + str(len(part.state['cut_edges'])) + \
                        '_splits_' + str(part.splits) + \
                        '_' + str(i1) + '_' + str(count) + '.txt'
                    dl.part_dump(part.state, filename)

                    # Set the values to reflect the changes
                    best_pop.value = best_pop_i1 = part.new_popdev
                    best_frack.value = best_fracks_i1 = part.new_fracks
                    best_smooth.value = best_smooth_i1 = len(part.state['cut_edges'])
                    
                    # Update assignment
                    ns.assignment = part.state.assignment

                    # If the partition is ready for the next stage
                    if ((stage == 1 and part.new_fracks == 0) or 
                        (stage == 0 and part.new_popdev <= max_pop_deviation)):
                        stage += 1
                        best_stage.value = stage
                        initial_partition = GeographicPartition(graph, 
                            assignment = part.state.assignment, updaters = my_updaters)
                        max_splits = total_splits(initial_partition)
                        break

                # At each time interval, check if another processor has a better
                # plan. If so, restart the markovchain
                if time.time() > check_time:
                    if (best_stage.value > stage or 
                        (stage == 0 and best_pop.value < best_pop_i1) or
                        (stage == 1 and best_frack.value < best_frack_i1) or
                        (stage == 2 and best_smooth.value < best_smooth_i1)):
                        initial_partition = GeographicPartition(graph, 
                            assignment = ns.assignment, updaters = my_updaters)
                        stage = best_stage.value
                        break            
                    check_time = time.time() + time_interval       

                # If you have finished the Markov Chain
                if count > markovchainlength:
                    stage = 3
                    break

    return i1

# Setup
if __name__ == '__main__':
    freeze_support()

    # Load files and combine into a single dataframe
    exec(open("./input_templates/combined_input.py").read())
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
    manager = Manager()
    best_pop = manager.Value('d', pop_deviation(initial_partition))
    best_stage = manager.Value('d', 0)
    best_frack = manager.Value('d', fracking(initial_partition))
    best_smooth = manager.Value('d', len(initial_partition['cut_edges']))

    ns = manager.Namespace()
    ns.assignment = initial_partition.assignment

    # Run in parallel
    ctx = get_context("spawn")
    p = ctx.Pool(poolsize)

    updated_vals = p.starmap(multi_chain, [(i1, graph, state, popkey, poptol, 
        markovchainlength, win_margin, electionvol, cutoff, margin,
        my_apportionment, best_pop, best_stage, best_frack, best_smooth, geotag, 
        ns, time_interval, max_pop_deviation) for i1 in range(poolsize)])