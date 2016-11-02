#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2016 <+YOU OR YOUR COMPANY+>.
# 
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
# 
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
# 

import binascii
import numpy as np  
import struct
from itertools import izip
from collections import deque

import pmt
from gnuradio import gr


PACKET_HEADER_FMT = ">II4B4Ii"
PACKET_HEADER_LEN = struct.calcsize(PACKET_HEADER_FMT)
print("packet header is now {} bytes".format(PACKET_HEADER_LEN))

FRAME_HEADER_FMT = ">II"
FRAME_HEADER_LEN = struct.calcsize(FRAME_HEADER_FMT)
print("frame header is now {} bytes".format(FRAME_HEADER_LEN))

def make_random_packet(preamble, sync, payload_len, counter, rng):
    '''
    preamble and sync are expected to be bytearray or bytes objects
    
    payload len should not exceed 255
    '''

    if rng is None:
        rng = np.random.RandomState()

    if (payload_len > 255 - PACKET_HEADER_LEN) or (payload_len < 0):
        # payload len is an 8 bit field so cannot be larger than 255
        raise ValueError("Payload len must be >=0 and < {}".format(256 - PACKET_HEADER_LEN))

    # counter takes up 2 bytes
    payload = rng.bytes(payload_len - 2)

    packet_len = len(payload) + PACKET_HEADER_LEN

    # assemble fields to compute CRC32
    packed_fields = struct.pack(PACKET_HEADER_FMT, preamble,
                                                   sync,
                                                   packet_len, packet_len,
                                                   packet_len, packet_len,
                                                   counter, counter,
                                                   counter, counter,
                                                   0)
    

    # only compute CRC for packet_len and counter fields up to the crc itself
    #crc = binascii.crc32(packed_fields[12:-4])
    crc = binascii.crc32(packed_fields[8:-4])

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
    add fields to support zero padding
    '''

    frame_len = len(packet) + FRAME_HEADER_LEN

    frame_header = struct.pack(FRAME_HEADER_FMT,
                               pre_spacing,
                               frame_len)


    return frame_header + packet


def make_random_data_file(preamble, sync, min_spacing, max_spacing, num_bits, truth_name, seed):

    # setup constants
    syms_per_byte = 4
    samps_per_sym = 4

    samps_per_byte = samps_per_sym * syms_per_byte
    generated_bits = 0
    packet_sizes = []
    
    rng = np.random.RandomState(seed)
    
    while generated_bits < num_bits:
        packet_size = rng.randint(low=2, high=256 - 30 - PACKET_HEADER_LEN, size=1)[0]
        packet_sizes.append(packet_size)
        generated_bits += packet_size * 8

    num_packets = len(packet_sizes)
    #print("generating {} bits in {} packets".format(sum(packet_sizes) * 8, num_packets))

    pre_spacing = rng.randint(low=min_spacing, high=max_spacing, size=(num_packets,))
    #pre_spacing = pre_spacing/4
    #pre_spacing = pre_spacing*4
    
    # make all the packets
    packets = [ make_random_packet(preamble, sync, packet_sizes[i], i, rng) for i in range(num_packets)]


    # write out the packets as ground truth
    with open(truth_name, 'wb') as f:
        for p in packets:
            f.write(p)
    
    # encapsulate packets in frames
    frames = [make_frame(pre, packet) for pre, packet in izip(pre_spacing, packets)]

    #print("Returning {} frames".format(len(frames)))
    return frames


class random_packet_source(gr.sync_block):
    """
    Generate at least num_bits of random bits
    """
    def __init__(self, preamble, sync, num_bits, min_padding, max_padding, truth_name, seed=None):
        gr.sync_block.__init__(self,
            name="random_packet_source",
            in_sig=None,
            out_sig=[np.uint8])
        
        self.preamble = preamble
        self.sync = sync
        self.num_bits = num_bits
        self.min_padding = min_padding
        self.max_padding = max_padding
        self.truth_name = truth_name
        
        frames = make_random_data_file(preamble, 
                                        sync,
                                        min_padding,
                                        max_padding,
                                        num_bits,
                                        truth_name, 
                                        seed)
        
        self.byte_list = deque([ord(c) for frame in frames for c in frame ])
        #print("length of byte list: {}".format(len(self.byte_list)*8))


    def work(self, input_items, output_items):
        #print("Work called")
        
        if len(self.byte_list) == 0:
            print("random packet generator done")
            return -1
        
        out = output_items[0]
        

        
        #print("len of byte list {}".format(len(self.byte_list)))
        #print("len of output items {}".format(len(out)))
        
        
        nitems_to_output = min(len(self.byte_list), len(out))
        #print("outputting {} items".format(nitems_to_output))
        out[:nitems_to_output] = [self.byte_list.popleft() for i in range(nitems_to_output)]
        return nitems_to_output

