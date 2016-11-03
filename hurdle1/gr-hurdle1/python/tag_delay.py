#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2016 <+YOU OR YOUR COMPANY+>.
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
from gnuradio import gr

class tag_delay(gr.sync_block):
    """
    docstring for block tag_delay
    """
    def __init__(self, delay):
        gr.sync_block.__init__(self,
            name="tag_delay",
            in_sig=[np.complex64],
            out_sig=[np.complex64])

        # don't violate causality. 
        self.tag_delay = np.abs(delay)
        self.tags = []
        
        self.set_tag_propagation_policy(gr.TPP_DONT)

    

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        
        # get the absolute offset of the start of this window
        start_offset = self.nitems_read(0)
        
        print("start offset: {}".format(start_offset))
        
        # get the absolute offset of the end of this window
        end_offset = start_offset + len(in0)-1
        
        print("end offset: {}".format(end_offset))
        
        # get all the tags in the current window
        tags = self.get_tags_in_range(0, start_offset, end_offset)

        # delay the tag offsets
        tags = self.delay_tags(tags, self.tag_delay)
        
        self.tags.extend(tags)

        # output tags as necessary and remove them from the tag history
        self.output_tags(start_offset, end_offset)

        out[:] = in0
        return len(output_items[0])

    def output_tags(self, start_offset, end_offset):
        
        # filter out the tags we need to output now
        tags_to_output = [t for t in self.tags if ( t.offset >= start_offset and t.offset <= end_offset)]
        
        # hold onto the tags we'll need in the next iteration(s)
        self.tags = [t for t in self.tags if t.offset > end_offset]
        
        # output the tags
        for t in tags_to_output:
            print("outputting tag with offset: {}".format(t.offset))
            self.add_item_tag(0, t)

    @staticmethod
    def delay_tags(tags, delay):
        delayed_tags = []
        
        for t in tags:
            print("current tag offset: {}".format(t.offset))
            t.offset += delay
            print("new tag offset: {}".format(t.offset))
            delayed_tags.append(t)
            
        return delayed_tags
        
        