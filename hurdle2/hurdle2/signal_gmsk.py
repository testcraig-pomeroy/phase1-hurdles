#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# For the gmsk transmitter
from gnuradio import analog
from gnuradio import blocks
from gnuradio import digital
from gnuradio import filter
from gnuradio import gr
from gnuradio.filter import firdes


#
# Heir block for the GMSK transmitter
#
#
class gmsk_tx(gr.hier_block2):

    def __init__(self, channel_shift_hz=0, random_source_seed=0, sample_rate=0, occupied_bw=0, tx_len_s=1.0):
        gr.hier_block2.__init__(
            self, "Hurdle2 Gmsk",
            gr.io_signature(0, 0, 0),
            gr.io_signature(1, 1, gr.sizeof_gr_complex * 1),
        )

        symbol_rate = occupied_bw / 1.0  # spectral efficiency

        self.num_samples = int(sample_rate * tx_len_s)

        #print("sample rate: {}".format(sample_rate))
        #print("symbol rate: {}".format(symbol_rate))

        ##################################################
        # Parameters
        ##################################################
        self.channel_shift_hz = channel_shift_hz
        self.random_source_seed = random_source_seed
        self.sample_rate = sample_rate
        self.symbol_rate = symbol_rate

        ##################################################
        # Blocks
        ##################################################
        self.low_pass_filter_0 = filter.fir_filter_ccf(1, firdes.low_pass(
        	1.0, sample_rate, symbol_rate * 5, symbol_rate, firdes.WIN_HAMMING, 6.76))
        self.digital_gmsk_mod_0 = digital.gmsk_mod(
        	samples_per_symbol=sample_rate / symbol_rate,
        	bt=0.35,
        	verbose=False,
        	log=False,
        )
        self.blocks_multiply_xx_0_0_0 = blocks.multiply_vcc(1)
        self.analog_sig_source_x_0_0 = analog.sig_source_c(sample_rate, analog.GR_COS_WAVE, channel_shift_hz, 1, 0)
        self.analog_random_uniform_source_x_0 = analog.random_uniform_source_b(0, 256, random_source_seed)
        
        # this limits output to the requested number of samples
        self.head = blocks.head(gr.sizeof_gr_complex * 1, int(self.num_samples))

        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_random_uniform_source_x_0, 0), (self.digital_gmsk_mod_0, 0))
        self.connect((self.analog_sig_source_x_0_0, 0), (self.blocks_multiply_xx_0_0_0, 1))
        self.connect((self.digital_gmsk_mod_0, 0), (self.low_pass_filter_0, 0))
        self.connect((self.low_pass_filter_0, 0), (self.blocks_multiply_xx_0_0_0, 0))
        
        # limit output
        self.connect(self.blocks_multiply_xx_0_0_0, self.head, self)
