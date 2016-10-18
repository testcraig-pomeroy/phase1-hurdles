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


from gnuradio import analog
from gnuradio import blocks
from gnuradio import gr
from grc_gnuradio import blks2 as grc_blks2
import json

# Transmitter candidates
from signal_fm import fm_tx
from signal_gmsk import gmsk_tx
from signal_psk import psk_tx


class Transmitter(gr.top_block):


    def __init__(self, band_plan, file_len_s=5, sample_file_name="samples.dat"):
        gr.top_block.__init__(self, "Hurdle 2 CLI")

        self.samp_rate = band_plan['freq_span']
        self.bin_width = band_plan['freq_span'] / band_plan['n_bins']
        # self.symb_rate = band_plan['freq_span']/band_plan['n_bins']*0.7


        print "total bandwidth is %d" % self.samp_rate
        print "bin width is %d" % self.bin_width

        ##################################################
        # Blocks
        ##################################################
        self.noise_floor = analog.noise_source_c(analog.GR_GAUSSIAN, 0.01, 0)
        self.noise_head = blocks.head(gr.sizeof_gr_complex * 1, int(self.samp_rate * file_len_s))
        self.signal_sum = blocks.add_vcc(1)
        self.file_sink = blocks.file_sink(gr.sizeof_gr_complex * 1, sample_file_name, False)
        self.file_sink.set_unbuffered(True)

        # Add in the generated signals
        self.signal_sources = []
        self.head_blocks = []
        for x in band_plan['signals']:

            # TODO: fix the case where there is an odd number of bins
            shift = self.bin_width * x['center_bin'] - self.samp_rate / 2
            if(x['n_bins'] & 1):  # X is odd
                shift = shift - self.bin_width * 0.5

            occupied_bw = x['n_bins'] * self.bin_width * 0.7

            print "Adding a signal: %s" % x
            print "Center freq is %d" % shift
            print "occupied bw is %d" % occupied_bw

            if(x['modulation_type'] == "QPSK"):

                symb_rate = occupied_bw / 2  # spectral efficiency

                sig = psk_tx(
                    channel_shift_hz=shift,
                    random_source_seed=0,
                    sample_rate=self.samp_rate,
                    symbol_rate=symb_rate,
                )
            elif(x['modulation_type'] == "GMSK"):
                symb_rate = occupied_bw / 1  # spectral efficiency
                sig = gmsk_tx(
                    channel_shift_hz=shift,
                    random_source_seed=0,
                    sample_rate=self.samp_rate,
                    symbol_rate=symb_rate,
                )
            elif(x['modulation_type'] == "FM"):
                symb_rate = occupied_bw / 1  # spectral efficiency
                sig = fm_tx(
                    channel_shift_hz=shift,
                    random_source_seed=0,
                    sample_rate=self.samp_rate,
                    symbol_rate=symb_rate,
                )
            else:
                raise NotImplementedError


            self.signal_sources.append (sig)
            self.head_blocks.append(blocks.head(gr.sizeof_gr_complex * 1, int(self.samp_rate * file_len_s)))


        ##################################################
        # Connections
        ##################################################

        # add in noise floor
        self.connect(self.noise_floor, self.noise_head, (self.signal_sum, 0))

        # connect all of the signal sources to the head blocks and remaining
        # adder blocks
        for i, sig in enumerate(self.signal_sources):
            self.connect(sig, self.head_blocks[i])
            self.connect(self.head_blocks[i], (self.signal_sum, i + 1))



        # also save samples to disk
        self.connect(self.signal_sum, self.file_sink)

    def go(self, host, port):

        self.tcp_server_sink = blocks.tcp_server_sink(gr.sizeof_gr_complex * 1, host, port, True)

        print("IQ port connected")
        # send samples out via a TCP server
        self.connect(self.signal_sum, self.tcp_server_sink)

        self.start()
        print("flowgraph running")

        self.wait()
        print("flowgraph complete")

