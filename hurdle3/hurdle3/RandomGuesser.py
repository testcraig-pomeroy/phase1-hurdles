#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2016 DARPA.
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

import numpy as np

class RandomGuesser(object):
    '''
    Class for purely random guesser to check out mechanics
    '''
    def __init__(self, num_states, seed=None):
        # set up a dedicated random number generator
        # for this object to guarantee repeatability
        # if a seed is specified

        self._seed = seed

        self._num_states = num_states

    def start(self):
        '''
        Run first iteration as a special case.
        Note that start() should initialize the solution for
        the beginning of a test, even if called in the middle of a 
        test, in order to support running multiple consecutive trials.
        '''
        self._rng = np.random.RandomState(self._seed)

        predicted_output = self._rng.randint(self._num_states)
        my_next_output = self._rng.randint(self._num_states)

        return predicted_output, my_next_output

    def step(self, reward, observation):
        '''
        Given the observation, generate the next probabilistic action
        '''

        predicted_output = self._rng.randint(self._num_states)
        my_next_output = self._rng.randint(self._num_states)

        return predicted_output, my_next_output

