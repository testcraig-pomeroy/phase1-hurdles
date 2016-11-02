# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Scalable Fm
# Generated: Mon Oct 31 14:51:05 2016
##################################################

from gnuradio import analog
from gnuradio import filter
from gnuradio import gr
from gnuradio.filter import firdes
import math


class scalable_fm(gr.hier_block2):

    def __init__(self, audio_rate=44100, max_dev=75e3, quad_rate=220.5e3):
        gr.hier_block2.__init__(
            self, "Scalable Fm",
            gr.io_signature(1, 1, gr.sizeof_float*1),
            gr.io_signature(1, 1, gr.sizeof_gr_complex*1),
        )

        ##################################################
        # Parameters
        ##################################################
        self.audio_rate = audio_rate
        self.max_dev = max_dev
        self.quad_rate = quad_rate

        ##################################################
        # Variables
        ##################################################
        self.k = k = 2*math.pi*max_dev/quad_rate
        self.interp_factor = interp_factor = int(quad_rate/audio_rate)

        ##################################################
        # Blocks
        ##################################################
        self.rational_resampler_xxx_0 = filter.rational_resampler_fff(
                interpolation=interp_factor,
                decimation=1,
                taps=None,
                fractional_bw=None,
        )
        self.analog_frequency_modulator_fc_0 = analog.frequency_modulator_fc(k)
        self.analog_fm_preemph_0 = analog.fm_preemph(fs=quad_rate, tau=75e-6, fh=-1.0)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_fm_preemph_0, 0), (self.analog_frequency_modulator_fc_0, 0))    
        self.connect((self.analog_frequency_modulator_fc_0, 0), (self, 0))    
        self.connect((self, 0), (self.rational_resampler_xxx_0, 0))    
        self.connect((self.rational_resampler_xxx_0, 0), (self.analog_fm_preemph_0, 0))    
