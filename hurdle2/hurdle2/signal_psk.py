#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#
# Heir block for the PSK transmitter
#
#

from gnuradio import analog
from gnuradio import blocks
from gnuradio import digital
from gnuradio import filter
from gnuradio import gr
from gnuradio.filter import firdes

class psk_tx(gr.hier_block2):

    def __init__(self, channel_shift_hz=0, random_source_seed=0, sample_rate=0, occupied_bw=0, tx_len_s=1.0):
        gr.hier_block2.__init__(
            self, "Hurdle2 Psk",
            gr.io_signature(0, 0, 0),
            gr.io_signature(1, 1, gr.sizeof_gr_complex * 1),
        )


        symbol_rate = occupied_bw / 0.7 / 2.0  # spectral efficiency
        #print("sample rate: {}".format(sample_rate))
        #print("symbol rate: {}".format(symbol_rate))

        ##################################################
        # Parameters
        ##################################################       
        self.channel_shift_hz = channel_shift_hz
        self.random_source_seed = random_source_seed
        self.sample_rate = sample_rate
        self.symbol_rate = symbol_rate
        self.samples_per_symbol = int(sample_rate / symbol_rate)
        #print("qpsk samp rate: {} sym rate: {} samples per symbol:{}".format(sample_rate, symbol_rate, self.samples_per_symbol))
        
        self.num_samples = int(sample_rate * tx_len_s)
        
        self.qpsk = qpsk = digital.constellation_rect(([-1-1j, -1+1j, 1+1j, 1-1j]), ([0, 1, 3, 2]), 4, 2, 2, 1, 1).base()

        ##################################################
        # Blocks
        ##################################################
        self.low_pass_filter_0_0 = filter.fir_filter_ccf(1, firdes.low_pass(
        	1, sample_rate, symbol_rate * 5, symbol_rate, firdes.WIN_HAMMING, 6.76))
        	
        self.qpsk_mod = digital.generic_mod(
          constellation=qpsk,
          differential=True,
          samples_per_symbol=self.samples_per_symbol,
          pre_diff_code=True,
          excess_bw=0.7,
          verbose=False,
          log=False,
          )
        self.blocks_multiply_xx_0 = blocks.multiply_vcc(1)
        self.analog_sig_source_x_0 = analog.sig_source_c(sample_rate, analog.GR_COS_WAVE, channel_shift_hz, 1, 0)
        self.analog_random_uniform_source_x_0 = analog.random_uniform_source_b(0, 256, random_source_seed)
        
        # this is in response to the QPSK block refusing to shut down for certain numbers of samples
        self.modulo_map = {60:29, 30:29, 20:9, 15:7, 12:5, 10:9}
        extra_samples = self.modulo_map[self.samples_per_symbol]-self.num_samples%self.samples_per_symbol+self.samples_per_symbol
        # ask for a known good number of samples such that QPSK will shut down, then limit to the number of 
        # samples we actually want with a downstream head block
        self.head_hack = blocks.head(gr.sizeof_gr_complex * 1, int(self.num_samples + extra_samples))
        
        # this limits output to the requested number of samples
        self.head = blocks.head(gr.sizeof_gr_complex * 1, int(self.num_samples))

        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_random_uniform_source_x_0, 0), (self.qpsk_mod, 0))
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_multiply_xx_0, 1))
        self.connect((self.qpsk_mod, 0), self.head_hack, (self.low_pass_filter_0_0, 0))
        self.connect((self.low_pass_filter_0_0, 0), (self.blocks_multiply_xx_0, 0))
        
        # limit output
        self.connect(self.blocks_multiply_xx_0, self.head, self)
