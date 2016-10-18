#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#
#
# Heir block for the FM transmitter
#
#
from gnuradio import analog
from gnuradio import blocks
from gnuradio import digital
from gnuradio import filter
from gnuradio import gr
from gnuradio.filter import firdes

class fm_tx(gr.hier_block2):

    def __init__(self, channel_shift_hz=0, random_source_seed=0, sample_rate=0, symbol_rate=1):
        gr.hier_block2.__init__(
            self, "Hurdle2 Fm",
            gr.io_signature(0, 0, 0),
            gr.io_signature(1, 1, gr.sizeof_gr_complex * 1),
        )

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
        self.low_pass_filter_0_0_0_0 = filter.interp_fir_filter_ccf(5, firdes.low_pass(
        	1, sample_rate, symbol_rate * 5, symbol_rate, firdes.WIN_HAMMING, 6.76))

        self.blocks_multiply_xx_0_0_0 = blocks.multiply_vcc(1)

        self.analog_wfm_tx_0 = analog.wfm_tx(
        	audio_rate=10000,
        	quad_rate=600000,
        	tau=75e-6,
        	max_dev=50e3,
        )
        self.analog_sig_source_x_0_0 = analog.sig_source_c(sample_rate, analog.GR_COS_WAVE, channel_shift_hz, 1, 0)
        self.analog_noise_source_x_1 = analog.noise_source_f(analog.GR_GAUSSIAN, 0.3, random_source_seed)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_noise_source_x_1, 0), (self.analog_wfm_tx_0, 0))
        self.connect((self.analog_sig_source_x_0_0, 0), (self.blocks_multiply_xx_0_0_0, 1))
        self.connect((self.analog_wfm_tx_0, 0), (self.low_pass_filter_0_0_0_0, 0))
        self.connect((self.blocks_multiply_xx_0_0_0, 0), (self, 0))
        self.connect((self.low_pass_filter_0_0_0_0, 0), (self.blocks_multiply_xx_0_0_0, 0))

    def get_channel_shift_hz(self):
        return self.channel_shift_hz

    def set_channel_shift_hz(self, channel_shift_hz):
        self.channel_shift_hz = channel_shift_hz
        self.analog_sig_source_x_0_0.set_frequency(self.channel_shift_hz)

    def get_random_source_seed(self):
        return self.random_source_seed

    def set_random_source_seed(self, random_source_seed):
        self.random_source_seed = random_source_seed

    def get_sample_rate(self):
        return self.sample_rate

    def set_sample_rate(self, sample_rate):
        self.sample_rate = sample_rate
        self.low_pass_filter_0_0_0_0.set_taps(firdes.low_pass(10, self.sample_rate, 100000, 10000, firdes.WIN_HAMMING, 6.76))
        self.analog_sig_source_x_0_0.set_sampling_freq(self.sample_rate)

    def get_symbol_rate(self):
        return self.symbol_rate

    def set_symbol_rate(self, symbol_rate):
        self.symbol_rate = symbol_rate

