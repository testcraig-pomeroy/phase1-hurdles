# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Scalable Signal Fm
# Generated: Mon Oct 31 20:43:11 2016
##################################################

import os
import sys

from gnuradio import analog
from gnuradio import blocks
from gnuradio import filter
from gnuradio import gr
from gnuradio.filter import firdes
from scalable_fm import scalable_fm

class signal_fm(gr.hier_block2):

    def __init__(self, channel_shift_hz=0, occupied_bw=100e3, random_source_seed=0, 
                 sample_rate=3e6, tx_len_s=1.0, fm_file_path="hurdle2/deps/hurdle2/beethoven_symphony_no5.wav",
                 fm_file_start_s=27.75):
        gr.hier_block2.__init__(
            self, "Scalable Signal Fm",
            gr.io_signature(0, 0, 0),
            gr.io_signature(1, 1, gr.sizeof_gr_complex*1),
        )

        ##################################################
        # Parameters
        ##################################################
        self.channel_shift_hz = channel_shift_hz
        self.occupied_bw = occupied_bw
        self.random_source_seed = random_source_seed
        self.sample_rate = sample_rate
        self.tx_len_s = tx_len_s
        self.fm_file_start_s = fm_file_start_s

        ##################################################
        # Variables
        ##################################################
        self.fm_scale_factor = fm_scale_factor = 1.0/0.728
        self.audio_rate = audio_rate = 44100
        self.samp_rate = samp_rate = sample_rate
        self.quad_rate = quad_rate = audio_rate*20
        self.num_bins = num_bins = 2
        self.max_deviation = max_deviation = occupied_bw*fm_scale_factor

        ##################################################
        # Blocks
        ##################################################
        self.wavfile_source = blocks.wavfile_source(fm_file_path, True)
        self.skiphead = blocks.skiphead(gr.sizeof_float*1, int(fm_file_start_s*audio_rate))
        self.scalable_fm = scalable_fm(
            audio_rate=audio_rate,
            max_dev=max_deviation,
            quad_rate=quad_rate,
        )
        self.rational_resampler_0 = filter.rational_resampler_ccc(
                interpolation=15,
                decimation=4,
                taps=None,
                fractional_bw=None,
        )
        self.rational_resampler = filter.rational_resampler_ccc(
                interpolation=400,
                decimation=441,
                taps=None,
                fractional_bw=None,
        )
        self.null_sink = blocks.null_sink(gr.sizeof_float*1)
        self.mult = blocks.multiply_vcc(1)
        self.low_pass_filter_0 = filter.interp_fir_filter_ccf(1, firdes.low_pass(
        	1, samp_rate, occupied_bw*1.5, samp_rate/100.0, firdes.WIN_BLACKMAN, 6.76))
        self.head = blocks.head(gr.sizeof_gr_complex*1, int(tx_len_s*samp_rate))
        self.freq_shift = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, channel_shift_hz, 1, 0)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.freq_shift, 0), (self.mult, 1))    
        self.connect((self.head, 0), (self, 0))    
        self.connect((self.low_pass_filter_0, 0), (self.mult, 0))    
        self.connect((self.mult, 0), (self.head, 0))    
        self.connect((self.rational_resampler, 0), (self.rational_resampler_0, 0))    
        self.connect((self.rational_resampler_0, 0), (self.low_pass_filter_0, 0))    
        self.connect((self.scalable_fm, 0), (self.rational_resampler, 0))    
        self.connect((self.skiphead, 0), (self.scalable_fm, 0))    
        self.connect((self.wavfile_source, 0), (self.null_sink, 0))    
        self.connect((self.wavfile_source, 1), (self.skiphead, 0))    
