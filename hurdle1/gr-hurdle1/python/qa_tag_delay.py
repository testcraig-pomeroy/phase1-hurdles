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

from gnuradio import gr, gr_unittest
from gnuradio import blocks
from tag_delay import tag_delay
import pmt
import numpy as np

def make_tag(key, value, offset, srcid=None):
    tag = gr.tag_t()
    tag.key = pmt.string_to_symbol(key)
    tag.value = pmt.to_pmt(value)
    tag.offset = offset
    if srcid is not None:
        tag.srcid = pmt.to_pmt(srcid)
    return tag


class qa_tag_delay (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()

    def tearDown (self):
        self.tb = None

    def test_no_delay (self):
        
        tag_name = "my-tag"
        delay = 0

        data = [complex(a, b) for a, b in zip(range(10), range(20, 30))]
        
        expected = tuple([complex(a, b) for a, b in zip(range(10), range(20, 30))])

        t = make_tag(key=tag_name, value=10, offset=5, srcid="source")

        src = blocks.vector_source_c(data, False, tags=[t])
        op = tag_delay(delay)
        dst = blocks.vector_sink_c()

        # make connections
        self.tb.connect(src, op, dst)

        # set up fg
        self.tb.run ()
        # check data

        result = dst.data()
        result_tags = dst.tags()
        self.assertEqual(expected, result)
        self.assertEqual(t.offset, result_tags[0].offset)

    def test_with_delay (self):
        
        tag_name = "my-tag"
        delay = 3

        data = [complex(a, b) for a, b in zip(range(10), range(20, 30))]
        
        expected = tuple([complex(a, b) for a, b in zip(range(10), range(20, 30))])

        t = make_tag(key=tag_name, value=10, offset=5, srcid="source")

        src = blocks.vector_source_c(data, False, tags=[t])
        op = tag_delay(delay)
        dst = blocks.vector_sink_c()

        # make connections
        self.tb.connect(src, op, dst)

        # set up fg
        self.tb.run ()
        # check data

        result = dst.data()
        result_tags = dst.tags()
        self.assertEqual(expected, result)
        self.assertEqual(t.offset, result_tags[0].offset-delay)
        
if __name__ == '__main__':
    gr_unittest.run(qa_tag_delay, "qa_tag_delay.xml")
