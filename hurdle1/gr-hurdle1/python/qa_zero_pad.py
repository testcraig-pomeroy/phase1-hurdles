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
import numpy as np


from zero_pad import zero_pad


def make_tag(key, value, offset, srcid=None):
    tag = gr.tag_t()
    tag.key = pmt.string_to_symbol(key)
    tag.value = pmt.to_pmt(value)
    tag.offset = offset
    if srcid is not None:
        tag.srcid = pmt.to_pmt(srcid)
    return tag



class qa_zero_pad (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()
        self.maxDiff = None
    def tearDown (self):
        self.tb = None

    def test_001_t (self):
        tag_name = "zero_pad"

        data = [complex(a, b) for a, b in zip(range(10), range(20, 30))]
        # data = tuple(np.array(range(1000), dtype=np.complex64))
        expected = [complex(a, b) for a, b in zip(range(5), range(20, 25))]
        expected.extend([complex(0, 0), ] * 10)
        expected.extend([complex(a, b) for a, b in zip(range(5, 10), range(25, 30))])
        expected = tuple(expected)

        t = make_tag(tag_name, 10, 5, "source")



        src = blocks.vector_source_c(data, False, tags=[t])
        op = zero_pad(gr.sizeof_gr_complex, tag_name)
        dst = blocks.vector_sink_c()

        # make connections
        self.tb.connect(src, op, dst)

        # set up fg
        self.tb.run ()
        # check data

        result = dst.data()

        self.assertEqual(expected, result)

    def test_001_2 (self):
        tag_name = "zero_pad"

        data = [complex(a, b) for a, b in zip(range(20), range(20, 40))]
        # data = tuple(np.array(range(1000), dtype=np.complex64))
        expected = [complex(a, b) for a, b in zip(range(5), range(20, 25))]
        expected.extend([complex(0, 0), ] * 10)
        expected.extend([complex(a, b) for a, b in zip(range(5, 15), range(25, 35))])
        expected.extend([complex(0, 0), ] * 10)
        expected.extend([complex(a, b) for a, b in zip(range(15, 20), range(35, 40))])
        expected = tuple(expected)

        tags = [make_tag(tag_name, 10, 5, "source"),
                make_tag(tag_name, 10, 15, "source")]




        src = blocks.vector_source_c(data, False, tags=tags)
        op = zero_pad(gr.sizeof_gr_complex, tag_name)
        dst = blocks.vector_sink_c()

        # make connections
        self.tb.connect(src, op, dst)

        # set up fg
        self.tb.run ()
        # check data

        result = dst.data()

        self.assertEqual(expected, result)

if __name__ == '__main__':
    gr_unittest.run(qa_zero_pad, "qa_zero_pad.xml")
