#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Hurdle 1 Solution Stub
# Generated: Tue Nov  1 13:18:20 2016
##################################################

from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from grc_gnuradio import blks2 as grc_blks2
from optparse import OptionParser
import numpy


class hurdle_1_solution_stub(gr.top_block):

    def __init__(self, host='127.0.0.1', iq_port=9094, packet_port=9095, sample_filename='sample_filename.dat'):
        gr.top_block.__init__(self, "Hurdle 1 Solution Stub")

        ##################################################
        # Parameters
        ##################################################
        self.host = host
        self.iq_port = iq_port
        self.packet_port = packet_port
        self.sample_filename = sample_filename

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 4e6
        self.num_garbage = num_garbage = int(1e6/8)

        ##################################################
        # Blocks
        ##################################################
        self.blocks_throttle_1 = blocks.throttle(gr.sizeof_char*1, samp_rate/8.0,True)
        self.blocks_head_0 = blocks.head(gr.sizeof_char*1, num_garbage)
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_gr_complex*1, sample_filename, False)
        self.blocks_file_sink_0.set_unbuffered(False)
        self.blks2_tcp_source_0 = grc_blks2.tcp_source(
        	itemsize=gr.sizeof_gr_complex*1,
        	addr=host,
        	port=iq_port,
        	server=False,
        )
        self.blks2_tcp_sink_0 = grc_blks2.tcp_sink(
        	itemsize=gr.sizeof_char*1,
        	addr=host,
        	port=packet_port,
        	server=False,
        )
        self.analog_random_source_x_0 = blocks.vector_source_b(map(int, numpy.random.randint(0, 255, 1000)), True)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_random_source_x_0, 0), (self.blocks_throttle_1, 0))    
        self.connect((self.blks2_tcp_source_0, 0), (self.blocks_file_sink_0, 0))    
        self.connect((self.blocks_head_0, 0), (self.blks2_tcp_sink_0, 0))    
        self.connect((self.blocks_throttle_1, 0), (self.blocks_head_0, 0))    

    def get_host(self):
        return self.host

    def set_host(self, host):
        self.host = host

    def get_iq_port(self):
        return self.iq_port

    def set_iq_port(self, iq_port):
        self.iq_port = iq_port

    def get_packet_port(self):
        return self.packet_port

    def set_packet_port(self, packet_port):
        self.packet_port = packet_port

    def get_sample_filename(self):
        return self.sample_filename

    def set_sample_filename(self, sample_filename):
        self.sample_filename = sample_filename
        self.blocks_file_sink_0.open(self.sample_filename)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_throttle_1.set_sample_rate(self.samp_rate/8.0)

    def get_num_garbage(self):
        return self.num_garbage

    def set_num_garbage(self, num_garbage):
        self.num_garbage = num_garbage
        self.blocks_head_0.set_length(self.num_garbage)


def argument_parser():
    parser = OptionParser(usage="%prog: [options]", option_class=eng_option)
    parser.add_option(
        "", "--host", dest="host", type="string", default='127.0.0.1',
        help="Set host [default=%default]")
    parser.add_option(
        "", "--iq-port", dest="iq_port", type="intx", default=9094,
        help="Set iq_port [default=%default]")
    parser.add_option(
        "", "--packet-port", dest="packet_port", type="intx", default=9095,
        help="Set packet_port [default=%default]")
    parser.add_option(
        "", "--sample-filename", dest="sample_filename", type="string", default='sample_filename.dat',
        help="Set sample_filename [default=%default]")
    return parser


def main(top_block_cls=hurdle_1_solution_stub, options=None):
    if options is None:
        options, _ = argument_parser().parse_args()

    tb = top_block_cls(host=options.host, iq_port=options.iq_port, packet_port=options.packet_port, sample_filename=options.sample_filename)
    tb.start()
    tb.wait()


if __name__ == '__main__':
    main()
