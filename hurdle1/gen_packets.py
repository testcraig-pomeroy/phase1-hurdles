#!/usr/bin/python
# encoding: utf-8


from argparse import ArgumentDefaultsHelpFormatter
from argparse import ArgumentParser
import binascii
from itertools import izip
import os
import random
import struct
import sys

import numpy as np


PACKET_HEADER_FMT = ">II4B4Ii"
PACKET_HEADER_LEN = struct.calcsize(PACKET_HEADER_FMT)
print("packet header is now {} bytes".format(PACKET_HEADER_LEN))


FRAME_HEADER_FMT = ">II"
FRAME_HEADER_LEN = struct.calcsize(FRAME_HEADER_FMT)
print("frame header is now {} bytes".format(FRAME_HEADER_LEN))



def make_random_packet(preamble, sync, payload_len, counter):
    '''
    preamble and sync are expected to be bytearray or bytes objects
    
    payload len should not exceed 255
    '''

    if (payload_len > 255 - PACKET_HEADER_LEN) or (payload_len < 0):
        # payload len is an 8 bit field so cannot be larger than 255
        raise ValueError("Payload len must be >=0 and < {}".format(256 - PACKET_HEADER_LEN))

    # counter takes up 2 bytes
    payload = os.urandom(payload_len - 2)

    packet_len = len(payload) + PACKET_HEADER_LEN

    # assemble fields to compute CRC32
    packed_fields = struct.pack(PACKET_HEADER_FMT, preamble,
                                                   sync,
                                                   packet_len, packet_len,
                                                   packet_len, packet_len,
                                                   counter, counter,
                                                   counter, counter,
                                                   0)

    # only compute CRC for fields up to the crc itself
    crc = binascii.crc32(packed_fields[:-4])

    # now insert CRC
    packed_fields = struct.pack(PACKET_HEADER_FMT, preamble,
                                                   sync,
                                                   packet_len, packet_len,
                                                   packet_len, packet_len,
                                                   counter, counter,
                                                   counter, counter,
                                                   crc)


    return packed_fields + payload


def make_frame(pre_spacing, packet):
    '''
    rework this to remove need for frame_count, num bursts, bytes_per_sym
    '''

    frame_len = len(packet) + FRAME_HEADER_LEN

    frame_header = struct.pack(FRAME_HEADER_FMT,
                               pre_spacing,
                               frame_len)


    return frame_header + packet


def make_random_data_file(preamble, sync, max_spacing, num_bits, truth_name, out_name):

    # setup constants
    syms_per_byte = 4
    samps_per_sym = 4

    samps_per_byte = samps_per_sym * syms_per_byte
    generated_bits = 0
    packet_sizes = []
    while generated_bits < num_bits:
        packet_size = np.random.randint(low=2, high=256 - PACKET_HEADER_LEN, size=1)[0]
        packet_sizes.append(packet_size)
        generated_bits += packet_size * 8

    num_packets = len(packet_sizes)
    print("generating {} bits in {} packets".format(sum(packet_sizes) * 8, num_packets))

    pre_spacing = np.random.randint(low=samps_per_byte * 160, high=max_spacing, size=(num_packets,))

    # make all the packets
    packets = [ make_random_packet(preamble, sync, packet_sizes[i], i) for i in range(num_packets)]



    # write out the packets as ground truth
    with open(truth_name, 'wb') as f:
        for p in packets:
            f.write(p)


    # encapsulate packets in frames and write to disk
    with open(out_name, 'wb') as f:
        for pre, packet in izip(pre_spacing, packets):
            frame = make_frame(pre, packet)
            f.write(frame)

def main(argv=None):

    preamble = 0x99999999
    # sync = 0x1DFCCF1A
    sync = 0x1ACFFC1D

    try:
        # Setup argument parser
        parser = ArgumentParser(description="Hurdle 1 Packet Generator", formatter_class=ArgumentDefaultsHelpFormatter)
        parser.add_argument("--num-bits", type=float, default=1e6, help="minimum number of scorable bits to generate")
        parser.add_argument("--max-padding", type=float, default=256 * 8 * 2, help="maximum spacing to randomly generate between packets, in complex samples")
        parser.add_argument("--out-name", type=str, default="out_packets.bin", help="path to store generated packets including frame headers")
        parser.add_argument("--truth-name", type=str, default="truth_packets.bin", help="path to store true values of generated packets")

        # Process arguments
        args = parser.parse_args()

        # generate random packets and store to file
        make_random_data_file(preamble, sync, args.max_padding, args.num_bits, args.truth_name, args.out_name)
    except KeyboardInterrupt:
        print("process interrupted by keyboard")

if __name__ == "__main__":

    sys.exit(main())
