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

import numpy


# use this to map between item size and numpy dtype
itemsize2dtype = {gr.sizeof_gr_complex:numpy.complex64,
                  gr.sizeof_float:numpy.float32,
                  gr.sizeof_int:numpy.int32,
                  gr.sizeof_short:numpy.uint16,
                  gr.sizeof_char:numpy.uint8}

def tag_to_dict(t):
    d = {"offset":t.offset,
         "key":pmt.to_python(t.key),
         "value":pmt.to_python(t.value),
         "srcid":pmt.to_python(t.srcid)}

    return d
