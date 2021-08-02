#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Created 29 July 2020
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

# Max Splits
max_splits = total_splits(initial_partition)

# Stage is used to keep track of how many things are being changed. Stage 0 
# means that the population has not been balanced. Stage 1 means the population 
# has been balanced but there are still fracks. Stage 2 means the population
# has been balanced and there are no fracks.
stage = 0
count = 0

while True:

    # End if chain finished
    if stage == 3:
        break

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

    # Look through Markov Chain
    for part in chain.with_progress_bar():
        count += 1

        # Return files of valid plans
        if part.counter != 1:
            if part.good == 1:
                filename = 'redist_data/example_districts/' + state + '_' + \
                    my_apportionment + '_pop_' + str(round(part.new_popdev, 4)) + \
                    '_frack_' + str(part.new_fracks) + \
                    '_smooth_' + str(len(part.state['cut_edges'])) + \
                    '_splits_' + str(part.splits) + \
                    '_' + str(count) + '.txt'
                dl.part_dump(part.state, filename)

                # If the partition is ready for the next stage
                if ((stage == 1 and part.new_fracks == 0) or 
                    (stage == 0 and part.new_popdev <= max_pop_deviation)):
                    stage += 1
                    initial_partition = GeographicPartition(graph, 
                        assignment = part.state.assignment, updaters = my_updaters)
                    max_splits = total_splits(initial_partition)
                    break

            # If you have finished the Markov Chain
            if count > markovchainlength:
                stage = 3
                break