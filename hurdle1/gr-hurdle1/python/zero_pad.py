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

from gnuradio import gr
from operator import itemgetter
import pmt

import numpy

from block_utils import itemsize2dtype
from block_utils import tag_to_dict


class zero_pad(gr.basic_block):
    """
    this block looks for stream tags matching pad_tag_name
    and adds the requested number of zeros at the index
    of the tag. No tags are passed to the output of this block 
    """
    def __init__(self, itemsize, pad_tag_name):
        gr.basic_block.__init__(self,
            name="zero_pad",
            in_sig=[itemsize2dtype[itemsize]],
            out_sig=[itemsize2dtype[itemsize]])

        # storing tag name as stream tag so we don't need to convert
        # in work function
        self.pad_tag_name = pmt.intern(pad_tag_name)



        # variable to store items remaining to output
        self.residue = []


    def forecast(self, noutput_items, ninput_items_required):

        # if in the middle of outputting zeros, this block may not requre any inputs at all
        ninput_items_required[0] = max(noutput_items - len(self.residue), 0)


    def compute_first_zero_pad(self, tags):

        # convert each tag to dict
        tag_list = [tag_to_dict(t) for t in tags]

        # print "given {} tags".format(len(tags))
        # print "found {} matching tags".format(len(tag_list))

        if len(tag_list) > 0:
            # now sort
            tag_list = sorted(tag_list, key=itemgetter('offset'))

            # get the first tag
            first_tag = tag_list[0]

            # print "first tag is", first_tag
            # check for other tags at the same offset
            matching_tags = [t for t in tag_list if t["offset"] == first_tag["offset"]]

            # now sum
            num_zeros = sum([t["value"] for t in matching_tags])
            # print "need to add {} zeros at offset {}".format(num_zeros, first_tag["offset"])

            return first_tag["offset"], num_zeros
        else:
            return None, None

    def general_work(self, input_items, output_items):

        # this block only works with single input port, so make a convenience var for ch0
        inp = input_items[0]
        ninput_items = len(inp)

        nitems_remaining = len(self.residue)

        # if there are items to output, handle that first
        if nitems_remaining > 0:

            # figure out how many items we can output
            n_items_to_output = min(len(output_items[0]), nitems_remaining)

            # output appropriate number of items and clear them from residue
            output_items[0][:n_items_to_output] = self.residue[:n_items_to_output]
            # print("outputting residue:", self.residue[:n_items_to_output])
            self.residue[:n_items_to_output] = []


        # otherwise continue processing inputs
        else:

            # get all the tags
            tags = self.get_tags_in_window(0, 0, ninput_items, self.pad_tag_name)

            offset, num_zeros = self.compute_first_zero_pad(tags)

            if offset is not None:

                # check if there's room to output all items up to the first tag
                n_items_to_output = offset - self.nitems_read(0)

                if len(output_items[0]) >= n_items_to_output:

                    # tell ourselves how many zeros we now need to output
                    self.residue = [0, ] * num_zeros
                    # add the item containing the first tag we found to residue to
                    # prevent infinite loops
                    self.residue.append(inp[n_items_to_output])
                    n_items_consumed = n_items_to_output + 1

                # otherwise there isn't enough room, output as many items as possible
                else:
                    n_items_to_output = min(n_items_to_output, len(output_items[0]))
                    n_items_consumed = n_items_to_output


            else:
                n_items_to_output = min(len(output_items[0]), ninput_items)
                n_items_consumed = n_items_to_output

            output_items[0][:n_items_to_output] = inp[:n_items_to_output]
            # print("outputting:", inp[:n_items_to_output])


            self.consume(0, n_items_consumed)

        return n_items_to_output
