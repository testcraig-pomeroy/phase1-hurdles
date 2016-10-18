#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Hurdle 1 Rx
# Generated: Thu Oct 13 03:42:53 2016
##################################################

from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from grc_gnuradio import blks2 as grc_blks2
from optparse import OptionParser


class hurdle_1_rx(gr.top_block):

    def __init__(self, rx_packet_filename='rx_packets.bin', host='127.0.0.1', packet_port=9095):
        gr.top_block.__init__(self, "Hurdle 1 Rx")

        ##################################################
        # Parameters
        ##################################################
        self.rx_packet_filename = rx_packet_filename
        self.host = host
        self.packet_port = packet_port

        ##################################################
        # Blocks
        ##################################################
        self.blocks_file_sink_0_0 = blocks.file_sink(gr.sizeof_char*1, rx_packet_filename, False)
        self.blocks_file_sink_0_0.set_unbuffered(False)
        self.blks2_tcp_source_0 = grc_blks2.tcp_source(
        	itemsize=gr.sizeof_char*1,
        	addr=host,
        	port=packet_port,
        	server=True,
        )

        ##################################################
        # Connections
        ##################################################
        self.connect((self.blks2_tcp_source_0, 0), (self.blocks_file_sink_0_0, 0))    

    def get_rx_packet_filename(self):
        return self.rx_packet_filename

    def set_rx_packet_filename(self, rx_packet_filename):
        self.rx_packet_filename = rx_packet_filename
        self.blocks_file_sink_0_0.open(self.rx_packet_filename)

    def get_host(self):
        return self.host

    def set_host(self, host):
        self.host = host

    def get_packet_port(self):
        return self.packet_port

    def set_packet_port(self, packet_port):
        self.packet_port = packet_port


def argument_parser():
    parser = OptionParser(usage="%prog: [options]", option_class=eng_option)
    parser.add_option(
        "", "--rx-packet-filename", dest="rx_packet_filename", type="string", default='rx_packets.bin',
        help="Set rx_packet_filename [default=%default]")
    parser.add_option(
        "", "--host", dest="host", type="string", default='127.0.0.1',
        help="Set host [default=%default]")
    parser.add_option(
        "", "--packet-port", dest="packet_port", type="intx", default=9095,
        help="Set packet_port [default=%default]")
    return parser


def main(top_block_cls=hurdle_1_rx, options=None):
    if options is None:
        options, _ = argument_parser().parse_args()

    tb = top_block_cls(rx_packet_filename=options.rx_packet_filename, host=options.host, packet_port=options.packet_port)
    tb.start()
    tb.wait()


if __name__ == '__main__':
    main()
