#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Created 24 June 2020
Modifications to the existing gerrychain Markov Chain designed to  reduce the 
number of fracked counties and cut edges.

Program by Charlie Murphy based on code by Dinos Gonatas
'''

from gerrychain.constraints import Validator, deviation_from_ideal
from gerrychain import updaters
from calc_fracwins_comp import calc_fracwins_comp
from fracking import fracking, get_fracked_subgraph   
        
class MarkovChain_xtended_fracking:

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
        self.old_fracks = fracking(self.state)

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

        return (new_le_oldlength and new_le_oldwins)

    def __next__(self):

        if self.counter == 0:
            self.counter += 1
            self.good = 1
            return self

        while self.counter < self.total_steps:

            districts, subgraph, population = get_fracked_subgraph(self.state)

            proposed_next_state = self.proposal(self.state, subgraph, districts,
                population)

            self.new_fracks = fracking(proposed_next_state)

            # Erase the parent of the parent, to avoid memory leak
            self.state.parent = None
            self.good = 0

            if self.is_valid(proposed_next_state) and self.accept(proposed_next_state):

                if (self.new_fracks < self.old_fracks and
                    self.plan_criteria(proposed_next_state)):
                    self.good = 1
                    self.old_fracks = self.new_fracks
                    self.state = proposed_next_state
                   
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
