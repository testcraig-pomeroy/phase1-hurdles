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
import pmt
import struct

import numpy


class traffic_parser(gr.basic_block):
    """
    This handles traffic blocks that begin with 2 fields: 
        uint32 zero_pad: number of zero samples to add before packet
        uint32 frame_len: length of frame including these 2 header fields
        
        All header fields are expected to be little endian
        
        The number of zeros to add field is converted to a stream tag
    """
    def __init__(self, len_tag_name, zero_pad_tag_name):
        gr.basic_block.__init__(self,
            name="traffic_parser",
            in_sig=[numpy.uint8],
            out_sig=[numpy.uint8])

        # storing tag name as stream tag so we don't need to convert
        # in work function
        self.len_tag_name = pmt.to_pmt(len_tag_name)

        # storing tag name as stream tag so we don't need to convert
        # in work function
        self.zero_pad_tag_name = pmt.to_pmt(zero_pad_tag_name)

        # header format is two unsigned ints, little endian
        self.hdr_fmt = ">II"
        self.hdr_len = struct.calcsize(self.hdr_fmt)

        # variable to store number of payload items remaining to output
        # before looking for packet header again
        self.nitems_remaining = 0


    def forecast(self, noutput_items, ninput_items_required):
        # setup size of input_items[i] for work call
        for i in range(len(ninput_items_required)):

            # do min of items remaining and output items to handle chunk of remaining items correctly
            if self.nitems_remaining != 0:

                ninput_items_required[i] = min(noutput_items, self.nitems_remaining)

            # otherwise this block is 1:1
            else:
                ninput_items_required[i] = noutput_items

    def general_work(self, input_items, output_items):

        # this block only works with single input port, so make a convenience var for ch0
        inp = input_items[0]


        # check if we need to look for a header
        if self.nitems_remaining <= 0:

            # make sure there's a whole header plus first payload byte available
            if len(inp) >= self.hdr_len + 1:
                pad_len, frame_len = struct.unpack(self.hdr_fmt, inp[:self.hdr_len])

                packet_len = frame_len - self.hdr_len
                self.nitems_remaining = packet_len - 1


                # add stream tags for payload len and zero pad len
                offset = self.nitems_written(0)

                self.add_item_tag(0, offset,
                                  self.zero_pad_tag_name,
                                  pmt.to_pmt(pad_len))

                self.add_item_tag(0, offset,
                                  self.len_tag_name,
                                  pmt.to_pmt(packet_len))

                # keep track of where we are in the input chain
                self.consume_each(self.hdr_len + 1)
                output_items[0][0] = inp[self.hdr_len]
                return 1
            # if a full header isn't available in inp, return and hope for better
            # luck next iteration
            else:
                return 0

        # this should always be true at this point
        if self.nitems_remaining > 0:

            # figure out how many items we can output
            noutput_items = min(len(inp), len(output_items[0]), self.nitems_remaining)

            output_items[0][:noutput_items] = inp[:noutput_items]

            # consume header and all items we just passed to output and return
            self.consume_each(noutput_items)

            self.nitems_remaining -= noutput_items
            return noutput_items

        else:
            # we should not be able to get here...
            print("Warning, traffic parser is hitting an unexpected state")
            return 0

        # we shouldn't be able to get here either
        print("Warning, traffic parser is hitting another unexpected state")
        return 0
