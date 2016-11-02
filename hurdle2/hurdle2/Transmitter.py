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

import numpy as np

# Transmitter candidates
from signal_fm import signal_fm as fm_tx
from signal_gmsk import gmsk_tx
from signal_psk import psk_tx

from math import ceil

import hurdle1

class Transmitter(gr.top_block):


    def __init__(self, band_plan, file_len_s=5,
                 fm_file_start_s=27.75,
                 sample_file_name="samples.dat"):
        gr.top_block.__init__(self, "Hurdle 2 CLI")

        self.samp_rate = band_plan['freq_span']
        self.bin_width = band_plan['freq_span'] / band_plan['n_bins']
        # self.symb_rate = band_plan['freq_span']/band_plan['n_bins']*0.7

        

        #print "total bandwidth is %d" % self.samp_rate
        #print "bin width is %d" % self.bin_width

        ##################################################
        # Blocks
        ##################################################
        self.noise_floor = analog.noise_source_c(analog.GR_GAUSSIAN, 1.0, 0)
        self.end_head = blocks.head(gr.sizeof_gr_complex * 1, int(self.samp_rate * file_len_s))
        self.signal_sum = blocks.add_vcc(1)
        self.file_sink = blocks.file_sink(gr.sizeof_gr_complex * 1, sample_file_name, False)
        self.file_sink.set_unbuffered(True)

        # Add in the generated signals
        self.signal_sources = []
        self.snr_scalars = []
        for x in band_plan['signals']:

            shift = x['center_freq']
            
            snr_dB = x['snr']
            snr_lin = 10**(snr_dB/10.0)

            if(x['modulation_type'] == "QPSK"):
                
                occupied_bw = x['n_bins'] * self.bin_width*0.7
                scale_factor = np.sqrt(occupied_bw/self.samp_rate*snr_lin)
                
                sig = psk_tx(
                    channel_shift_hz=shift,
                    random_source_seed=0,
                    sample_rate=self.samp_rate,
                    occupied_bw=occupied_bw,
                    tx_len_s=file_len_s
                )
            elif(x['modulation_type'] == "GMSK"):
                
                occupied_bw = x['n_bins'] * self.bin_width*0.7
                scale_factor = np.sqrt(occupied_bw/self.samp_rate*snr_lin)
                
                sig = gmsk_tx(
                    channel_shift_hz=shift,
                    random_source_seed=0,
                    sample_rate=self.samp_rate,
                    occupied_bw=occupied_bw,
                    tx_len_s=file_len_s
                )
            elif(x['modulation_type'] == "FM"):
                
                occupied_bw = x['n_bins'] * self.bin_width
                scale_factor = np.sqrt(occupied_bw/self.samp_rate*snr_lin)
                
                sig = fm_tx(
                    channel_shift_hz=shift,
                    random_source_seed=0,
                    sample_rate=self.samp_rate,
                    occupied_bw=occupied_bw,
                    tx_len_s=file_len_s,
                    fm_file_start_s=fm_file_start_s
                )
            else:
                raise NotImplementedError

            #print "Adding a signal: %s" % x
            #print "Center freq is %d" % shift
            #print "occupied bw is %d" % occupied_bw
            #print "scale factor is %f" % scale_factor

            self.signal_sources.append (sig)
            self.snr_scalars.append(blocks.multiply_const_cc(scale_factor))


        ##################################################
        # Connections
        ##################################################

        # add in noise floor
        self.connect(self.noise_floor, (self.signal_sum, 0))

        # connect all of the signal sources to the head blocks, snr scalars and remaining
        # adder blocks
        for i, sig in enumerate(self.signal_sources):
            self.connect(sig, self.snr_scalars[i], (self.signal_sum, i + 1))

        self.connect(self.signal_sum, self.end_head)

        # also save samples to disk
        self.connect(self.end_head, self.file_sink)

    def go(self, do_tcp=True, host='127.0.0.1', port=0):

        if do_tcp:
            self.tcp_server_sink = hurdle1.tcp_server_sink(gr.sizeof_gr_complex * 1, host, port)

            print("IQ port connected to server")
            # send samples out via a TCP server
            self.connect(self.end_head, self.tcp_server_sink)
        else:
            print("skipping tcp output")

        self.run()
        print("flowgraph running")

        #self.wait()
        print("flowgraph complete")

