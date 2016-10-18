#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Hurdle 1
# Generated: Thu Oct 13 03:42:49 2016
##################################################

from gnuradio import analog
from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import hurdle1


class hurdle_1(gr.top_block):

    def __init__(self, host='127.0.0.1', iq_port=9094, tx_packet_filename='out_packets.bin'):
        gr.top_block.__init__(self, "Hurdle 1")

        ##################################################
        # Parameters
        ##################################################
        self.host = host
        self.iq_port = iq_port
        self.tx_packet_filename = tx_packet_filename

        ##################################################
        # Variables
        ##################################################
        self.symbol_rate = symbol_rate = 1000000
        self.samp_rate = samp_rate = 4000000
        
        self.rrc_taps = rrc_taps = firdes.root_raised_cosine(1.0, samp_rate, symbol_rate, 0.35, 11*4)
          
        
        self.constellation_1 = constellation_1 = digital.constellation_calcdist(([-1-1j, -1+1j, 1+1j, 1-1j]), ([0, 1, 3, 2]), 4, 1).base()
        

        ##################################################
        # Blocks
        ##################################################
        self.hurdle1_zero_pad_0 = hurdle1.zero_pad(gr.sizeof_gr_complex, 'zero_pad')
        self.hurdle1_traffic_parser_0 = hurdle1.traffic_parser('pkt_len', 'zero_pad')
        self.digital_constellation_modulator_0 = digital.generic_mod(
          constellation=constellation_1,
          differential=False,
          samples_per_symbol=samp_rate/symbol_rate,
          pre_diff_code=True,
          excess_bw=0.35,
          verbose=False,
          log=False,
          )
        self.blocks_tcp_server_sink_0 = blocks.tcp_server_sink(gr.sizeof_gr_complex*1, host, iq_port, False)
        self.blocks_multiply_xx_0 = blocks.multiply_vcc(1)
        self.blocks_file_source_0 = blocks.file_source(gr.sizeof_char*1, tx_packet_filename, False)
        self.blocks_add_xx_0 = blocks.add_vcc(1)
        self.analog_sig_source_x_0 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, 74500, 1, 0)
        self.analog_noise_source_x_0 = analog.noise_source_c(analog.GR_GAUSSIAN, 0, 0)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_noise_source_x_0, 0), (self.blocks_add_xx_0, 1))    
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_multiply_xx_0, 1))    
        self.connect((self.blocks_add_xx_0, 0), (self.blocks_tcp_server_sink_0, 0))    
        self.connect((self.blocks_file_source_0, 0), (self.hurdle1_traffic_parser_0, 0))    
        self.connect((self.blocks_multiply_xx_0, 0), (self.blocks_add_xx_0, 0))    
        self.connect((self.digital_constellation_modulator_0, 0), (self.hurdle1_zero_pad_0, 0))    
        self.connect((self.hurdle1_traffic_parser_0, 0), (self.digital_constellation_modulator_0, 0))    
        self.connect((self.hurdle1_zero_pad_0, 0), (self.blocks_multiply_xx_0, 0))    

    def get_host(self):
        return self.host

    def set_host(self, host):
        self.host = host

    def get_iq_port(self):
        return self.iq_port

    def set_iq_port(self, iq_port):
        self.iq_port = iq_port

    def get_tx_packet_filename(self):
        return self.tx_packet_filename

    def set_tx_packet_filename(self, tx_packet_filename):
        self.tx_packet_filename = tx_packet_filename
        self.blocks_file_source_0.open(self.tx_packet_filename, False)

    def get_symbol_rate(self):
        return self.symbol_rate

    def set_symbol_rate(self, symbol_rate):
        self.symbol_rate = symbol_rate

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.analog_sig_source_x_0.set_sampling_freq(self.samp_rate)

    def get_rrc_taps(self):
        return self.rrc_taps

    def set_rrc_taps(self, rrc_taps):
        self.rrc_taps = rrc_taps

    def get_constellation_1(self):
        return self.constellation_1

    def set_constellation_1(self, constellation_1):
        self.constellation_1 = constellation_1


def argument_parser():
    parser = OptionParser(usage="%prog: [options]", option_class=eng_option)
    parser.add_option(
        "", "--host", dest="host", type="string", default='127.0.0.1',
        help="Set host [default=%default]")
    parser.add_option(
        "", "--iq-port", dest="iq_port", type="intx", default=9094,
        help="Set iq_port [default=%default]")
    parser.add_option(
        "", "--tx-packet-filename", dest="tx_packet_filename", type="string", default='out_packets.bin',
        help="Set tx_packet_filename [default=%default]")
    return parser


def main(top_block_cls=hurdle_1, options=None):
    if options is None:
        options, _ = argument_parser().parse_args()

    tb = top_block_cls(host=options.host, iq_port=options.iq_port, tx_packet_filename=options.tx_packet_filename)
    tb.start()
    tb.wait()


if __name__ == '__main__':
    main()
