#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Hurdle 1 Solution Stub
# Generated: Thu Oct 13 03:45:01 2016
##################################################

from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import numpy


class hurdle_1_solution_stub(gr.top_block):

    def __init__(self, host='127.0.0.1', iq_port='9094', packet_port='9095', sample_filename='sample_filename.dat'):
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
        self.blocks_tagged_stream_to_pdu_0 = blocks.tagged_stream_to_pdu(blocks.byte_t, 'packet_len')
        self.blocks_stream_to_tagged_stream_0 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, 1000, 'packet_len')
        self.blocks_socket_pdu_0_0 = blocks.socket_pdu("TCP_CLIENT", host, packet_port, 10000, False)
        self.blocks_socket_pdu_0 = blocks.socket_pdu("TCP_CLIENT", host, iq_port, 10000, False)
        self.blocks_pdu_to_tagged_stream_0 = blocks.pdu_to_tagged_stream(blocks.complex_t, 'packet_len')
        self.blocks_head_0 = blocks.head(gr.sizeof_char*1, num_garbage)
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_gr_complex*1, sample_filename, False)
        self.blocks_file_sink_0.set_unbuffered(False)
        self.analog_random_source_x_0 = blocks.vector_source_b(map(int, numpy.random.randint(0, 255, 1000)), True)

        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.blocks_socket_pdu_0, 'pdus'), (self.blocks_pdu_to_tagged_stream_0, 'pdus'))    
        self.msg_connect((self.blocks_tagged_stream_to_pdu_0, 'pdus'), (self.blocks_socket_pdu_0_0, 'pdus'))    
        self.connect((self.analog_random_source_x_0, 0), (self.blocks_throttle_1, 0))    
        self.connect((self.blocks_head_0, 0), (self.blocks_stream_to_tagged_stream_0, 0))    
        self.connect((self.blocks_pdu_to_tagged_stream_0, 0), (self.blocks_file_sink_0, 0))    
        self.connect((self.blocks_stream_to_tagged_stream_0, 0), (self.blocks_tagged_stream_to_pdu_0, 0))    
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
        "", "--iq-port", dest="iq_port", type="string", default='9094',
        help="Set iq_port [default=%default]")
    parser.add_option(
        "", "--packet-port", dest="packet_port", type="string", default='9095',
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
