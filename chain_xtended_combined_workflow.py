#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Created 29 June 2020
Modifications to the existing gerrychain Markov Chain designed to balance
population, eliminate fracks, and reduce cut_edges to improve compactness all
in a single step.

Program by Charlie Murphy
'''

from gerrychain.constraints import Validator, deviation_from_ideal
from gerrychain import updaters
from calc_fracwins_comp import calc_fracwins_comp
from fracking import fracking, get_fracked_subgraph, fracking_total_splits, fracking_merge
from pop_constraint import pop_deviation, get_districts
        
class MarkovChain_xtended_combined_workflow:

    def __init__(self, proposal, constraints, accept, initial_state, 
        total_steps, election_composite, win_margin, win_volatility,
        cutoff, margin, stage, max_splits):

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

        self.election_composite = election_composite
        self.win_margin = win_margin
        self.win_volatility = win_volatility

        self.old_popdev = pop_deviation(self.state)
        self.old_fracks = fracking(self.state)
        self.old_cut_edges = len(self.state["cut_edges"])
        self.old_wins = calc_fracwins_comp(self.state, self.election_composite, self.win_volatility)

        self.stage = stage

        self.max_splits = max_splits

        self.cutoff = cutoff
        self.margin = margin
        self.tries = 0

    def __iter__(self):
        self.counter = 0
        self.state = self.initial_state
        self.good=1
        self.fit = 1
        return self

    # Return whether or not the number of cut edges is sufficiently low. This 
    # starts as less than or equal to the existing number of cut edges. However,
    # for ever time it takes longer than the cutoff number of tries this bound
    # is relaxed by the margin percent.
    def smoothing(self):
        if self.new_cut_edges <= self.old_cut_edges * (1 + (self.tries // self.cutoff) * self.margin):
            return True

    # Returns whether or not the plan meets the partisan criteria, as calculated
    # by fractional wins. At any step the plan will not allow change large than
    # that of the of the win margin
    def plan_criteria(self):
        return self.new_wins <= self.old_wins * (1 + self.win_margin)

    def __next__(self):

        # Keep the initial state
        if self.counter == 0:
            self.counter += 1
            self.good = 1
            return self

        while self.counter < self.total_steps:
            self.tries += 1

            # If population is not yet balanced, choose the districts to merge
            # that have the greatest population deviation
            if self.stage == 0:
                districts = get_districts(self.state)
                proposed_next_state = self.proposal(self.state, districts)

            # Otherwise, if there are still fracks, choose districts to merge 
            # that share fracks
            elif self.stage == 1:
                districts, subgraph, population = get_fracked_subgraph(self.state)
                proposed_next_state = self.proposal(self.state, subgraph, districts,
                    population)

            # Otherwise, choose districts to merge randomly
            else:
                proposed_next_state = self.proposal(self.state)

            # Find the number of fracks and county splits in the new proposed
            # plan
            if self.stage == 0:
                self.new_fracks, merged_splits, self.splits = fracking_merge(proposed_next_state,
                    districts[0], districts[1])
            else:
                self.new_fracks, self.splits = fracking_total_splits(proposed_next_state)

            # Find population deviation
            self.new_popdev = pop_deviation(proposed_next_state)

            # Find number of cut edges
            self.new_cut_edges = len(proposed_next_state["cut_edges"])

            # Find the fractional seat share
            self.new_wins = calc_fracwins_comp(proposed_next_state, 
                self.election_composite, self.win_volatility)

            # Erase the parent of the parent, to avoid memory leak
            self.state.parent = None
            self.good = 0

            # If the plan meets the constraints
            if (self.is_valid(proposed_next_state) 
                and self.accept(proposed_next_state)):
                if self.plan_criteria():

                    # If population is not yet balanced, keep if the plan 
                    # improves the population balance and reduces cut edges
                    if (self.stage == 0 and self.old_popdev > self.new_popdev 
                        and merged_splits <= 1 and self.smoothing()):
                        self.old_popdev = self.new_popdev
                        self.old_cut_edges = self.new_cut_edges
                        self.old_wins = self.new_wins
                        self.state = proposed_next_state
                        self.good = 1
                        self.tries = 0

                    # If there are fracks, keep if the plan reduces fracks and 
                    # cut edges
                    elif (self.stage == 1 and self.new_fracks < self.old_fracks 
                        and self.smoothing()):
                        self.good = 1
                        self.old_fracks = self.new_fracks
                        self.old_cut_edges = self.new_cut_edges
                        self.old_wins = self.new_wins
                        self.state = proposed_next_state
                        self.tries = 0

                    # Otherwise, only keep plans based on smoothing
                    elif (self.stage == 2 and self.splits <= self.max_splits and 
                        self.smoothing()):
                        self.state = proposed_next_state
                        self.tries = 0
                        self.old_wins = self.new_wins

                        # Only make a file of the plan if the number of new cut
                        # edges is strictly less
                        if self.new_cut_edges < self.old_cut_edges:
                            self.good = 1
                            self.old_cut_edges = self.new_cut_edges
                   
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
