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

from gnuradio import blocks
from gnuradio import gr, gr_unittest
import pmt
import struct

import numpy as np
from traffic_parser import traffic_parser


def tag_to_dict(t):
    d = {"offset":t.offset,
         "key":pmt.to_python(t.key),
         "value":pmt.to_python(t.value)}
    return d


class qa_traffic_parser (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()
        self.header_fmt = "<II"
    def tearDown (self):
        self.tb = None

    def test_single_packet_output (self):

        # set up source data
        len_tag_name = "packet_len"
        pad_tag_name = "num_zeros"

        num_zero_pad = 7
        packet_len = 10
        packet_payload = np.array(range(packet_len), dtype=np.uint8)

        header = struct.pack(self.header_fmt, num_zero_pad, packet_len)
        header = np.fromstring(header, dtype=np.uint8)

        # combine header and payload
        frame = np.concatenate((header, packet_payload))

        # declare blocks
        src = blocks.vector_source_b(frame.tolist())
        op = traffic_parser(len_tag_name, pad_tag_name)
        dst = blocks.vector_sink_b()

        # connect flowgraph and run
        self.tb.connect(src, op, dst)
        self.tb.run ()

        # retrieve data
        result_data = np.array(dst.data(), dtype=np.uint8)
        result_tags = dst.tags()
        result_tags = sorted([tag_to_dict(t) for t in result_tags])


        self.assertTrue(np.all(packet_payload == result_data))

        # check tags
        expected_tags = [{"offset":0,
                          "key":len_tag_name,
                          "value":packet_len},
                         {"offset":0,
                          "key":pad_tag_name,
                          "value":num_zero_pad}]

        expected_tags = sorted(expected_tags)


        self.assertListEqual(expected_tags, result_tags)


    def test_multi_packet_output (self):
        expected_tags = []

        # set up source data
        len_tag_name = "packet_len"
        pad_tag_name = "num_zeros"

        # set up first packet
        num_zero_pad = 7
        packet_len = 10
        packet_payload = np.array(range(packet_len), dtype=np.uint8)

        expected_data = packet_payload

        header = struct.pack(self.header_fmt, num_zero_pad, packet_len)
        header = np.fromstring(header, dtype=np.uint8)

        expected_tags.append({"offset":0,
                               "key":len_tag_name,
                               "value":packet_len})

        expected_tags.append({"offset":0,
                               "key":pad_tag_name,
                               "value":num_zero_pad})

        # combine header and payload
        frame0 = np.concatenate((header, packet_payload)).tolist()



        # set up second packet
        num_zero_pad = 99
        packet_len = 50
        packet_payload = np.array(range(packet_len), dtype=np.uint8)

        expected_data = np.concatenate((expected_data, packet_payload))

        header = struct.pack(self.header_fmt, num_zero_pad, packet_len)
        header = np.fromstring(header, dtype=np.uint8)

        expected_tags.append({"offset":10,
                               "key":len_tag_name,
                               "value":packet_len})

        expected_tags.append({"offset":10,
                               "key":pad_tag_name,
                               "value":num_zero_pad})

        # combine header and payload
        frame1 = np.concatenate((header, packet_payload)).tolist()


        frame = frame0 + frame1

        # declare blocks
        src = blocks.vector_source_b(frame)
        op = traffic_parser(len_tag_name, pad_tag_name)
        dst = blocks.vector_sink_b()

        # connect flowgraph and run
        self.tb.connect(src, op, dst)
        self.tb.run ()

        # retrieve data
        result_data = np.array(dst.data(), dtype=np.uint8)
        result_tags = dst.tags()
        result_tags = sorted([tag_to_dict(t) for t in result_tags])


        self.assertTrue(np.all(expected_data == result_data))


        expected_tags = sorted(expected_tags)


        self.assertListEqual(expected_tags, result_tags)


if __name__ == '__main__':
    gr_unittest.run(qa_traffic_parser)
