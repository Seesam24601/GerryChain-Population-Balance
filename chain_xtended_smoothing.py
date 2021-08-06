#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Created 4 August 2020

Program designed to use gerrychain to smooth a plan regardless of partisan 
intent.

Program by Charlie Murphy
'''

from gerrychain.constraints import Validator, deviation_from_ideal
from gerrychain import updaters
from fracking import fracking_merge
import random
        
class MarkovChain_xtended_smoothing:

    def __init__(self, proposal, constraints, accept, initial_state, 
        total_steps):

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

        self.old_smooth = len(self.state["cut_edges"])

    def __iter__(self):
        self.counter = 0
        self.state = self.initial_state
        self.good=1
        self.fit = 1
        return self

    def __next__(self):

        if self.counter == 0:
            self.counter += 1
            self.good = 1
            return self

        while self.counter < self.total_steps:

            edge = random.choice(tuple(self.state["cut_edges"]))

            self.d1 = self.state.assignment[edge[0]]
            self.d2 = self.state.assignment[edge[1]]

            proposed_next_state = self.proposal(self.state, (self.d1, self.d2))

            self.new_smooth = len(proposed_next_state["cut_edges"])

            # Erase the parent of the parent, to avoid memory leak
            self.state.parent = None
            self.good = 0

            if self.is_valid(proposed_next_state) and self.accept(proposed_next_state):

                self.fracks, self.merged_splits, self.splits = fracking_merge(proposed_next_state,
                    self.d1, self.d2)

                if (self.merged_splits <= 1 and 
                    self.new_smooth < self.old_smooth and
                    self.fracks == 0):
                    self.old_smooth = self.new_smooth
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
