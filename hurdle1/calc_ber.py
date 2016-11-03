#!/usr/bin/python
# encoding: utf-8


from argparse import ArgumentDefaultsHelpFormatter
from argparse import ArgumentParser
import binascii
from itertools import izip
import json
import struct
import sys

from collections import Counter
from collections import namedtuple

PacketHeaderTup = namedtuple("PacketHeaderTup", "preamble sync len0 len1 len2 len3 count0 count1 count2 count3 crc")


PACKET_HEADER_FMT = ">II4B4Ii"
PACKET_HEADER_LEN = struct.calcsize(PACKET_HEADER_FMT)
print("packet header is now {} bytes".format(PACKET_HEADER_LEN))


FRAME_HEADER_FMT = ">II"
FRAME_HEADER_LEN = struct.calcsize(FRAME_HEADER_FMT)
print("frame header is now {} bytes".format(FRAME_HEADER_LEN))

NON_SCORED_BYTES=8

def parse_packets(preamble, sync, packet_bytes):
    sync_header = struct.pack(">II", preamble, sync)

    packets = []
    pos = packet_bytes.find(sync_header)

    while pos >= 0:

        next_pos = packet_bytes.find(sync_header, pos + 1)

        if next_pos > 0:
            packets.append(packet_bytes[pos:next_pos])
        else:
            packets.append(packet_bytes[pos:])

        pos = next_pos


    return packets

def validate_len_and_counters(packets):
    # try to clean up packet headers
    
    
    headers = [ p[:PACKET_HEADER_LEN] for p in packets]

    
    packet_dict = {}
    
    for h, p in izip(headers, packets):
        
        t = PacketHeaderTup._make(struct.unpack(PACKET_HEADER_FMT, h))
        
        packet_lens = [t.len0, t.len1, t.len2, t.len3]
        packet_counts = [t.count0, t.count1, t.count2, t.count3]
        packet_crc = t.crc
        
        # try to brute force a matching CRC
        crc_valid = False
        valid_len = -1
        valid_count = -1
        
        for l in packet_lens:
            if crc_valid:
                break
            for c in packet_counts:
                crc_fields = struct.pack(">4B4I", l,l,l,l,c,c,c,c)
                if packet_crc == binascii.crc32(crc_fields):
                    crc_valid=True
                    valid_len = l
                    valid_count = c
                    
                    break
        
        if crc_valid:
            packet_dict[valid_count] = p
        else:
            expected_crc = binascii.crc32(h[8:PACKET_HEADER_LEN])
            print("Could not validate packet header: {}".format(binascii.hexlify(h[:PACKET_HEADER_LEN])))
            print("crc was {}, expected {}".format(hex(packet_crc),hex(expected_crc) ))  
            
            
            # see if voting works
            len_cnt = Counter()
            pkt_cnt = Counter()
            
            for l in packet_lens:
                len_cnt[l]+=1
    
            for c in packet_counts:
                pkt_cnt[c]+=1
            
            common_len, common_len_count = len_cnt.most_common(1)[0]     
            common_pkt, common_pkt_count = pkt_cnt.most_common(1)[0]  
        
            if common_len_count > 1 and common_pkt_count > 1:
                print("voting successful for packet count {}".format(common_pkt))
                packet_dict[common_pkt] = p
            else:
                print("voting failed")    
    return packet_dict

def main(argv=None):

    preamble = 0x99999999
    sync = 0x1ACFFC1D


    try:
        # Setup argument parser
        parser = ArgumentParser(description="Hurdle 1 BER calculator", formatter_class=ArgumentDefaultsHelpFormatter)
        parser.add_argument("--decoded-name", type=str, default="decoded.bin", help="path to find decoded packets")
        parser.add_argument("--truth-name", type=str, default="truth_packets.bin", help="path to find true values of generated packets")
        parser.add_argument("--results-name", type=str, default="results.json", help="path to store results file")
        parser.add_argument("--test-label", type=str, default="test", help="Label for this test")
        parser.add_argument("--ber-threshold", type=float, default=1e-5, help="maximum bit error rate required to pass")

        # Process arguments
        args = parser.parse_args()

        # read in truth packets, whole file
        with open(args.truth_name, 'rb') as f:
            truth_bytes = f.read()

        # read in decoded file, whole file
        with open(args.decoded_name, 'rb') as f:
            decoded_bytes = f.read()

        truth_packets = parse_packets(preamble, sync, truth_bytes)
        
        # ignore last truth packet
        truth_packets.pop()
        
        decoded_packets = parse_packets(preamble, sync, decoded_bytes)

        # storing as a dict to remove duplicate packet counters
        decoded_dict = validate_len_and_counters(decoded_packets)

        # storing as a set to remove duplicate packet counters
        decoded_packet_counters = set([struct.unpack(">4I", p[12:28])[0] for p in decoded_packets])
        decoded_packet_crcs = [struct.unpack(">i", p[28:32])[0] for p in decoded_packets]

        correct_count = 0
        num_good_crcs = 0

        # store truth packets by packet counter
        truth_dict = validate_len_and_counters(truth_packets)
        
        # subtracting 8 bytes per packet to remove the preamble and sync from the computation
        total_bits = 8*sum([len(v)-NON_SCORED_BYTES for k,v in truth_dict.iteritems()])
        error_count = 0
        
        for packet_count in sorted(truth_dict):
            
            if packet_count not in decoded_dict:
                print("packet {} not found".format(packet_count))
                
                # subtracting 8 bytes per packet to remove preamble and sync from the computation
                bit_errors = 8*(len(truth_dict[packet_count])-NON_SCORED_BYTES)
        
            else:

                tp = bytearray(truth_dict[packet_count])
                dp = bytearray(decoded_dict[packet_count])
                
                # stripping off first 8 bytes of preamble and sync
                tp = tp[NON_SCORED_BYTES:]
                dp = dp[NON_SCORED_BYTES:]

                bit_errors = sum([bin(a ^ b).count("1") for a, b in izip(tp, dp)])
            
            error_count += bit_errors
         
         
        truth_packet_nums = set(truth_dict.keys())
        decoded_packet_nums = set(decoded_dict.keys())
        
        print("missing packet nums {}".format(truth_packet_nums-decoded_packet_nums))

        ber = (error_count) / float(total_bits)
        print("Bit error rate was {}, error bits: {} total bits {}".format(ber, error_count, total_bits))

        
        hurdle_pass = args.ber_threshold >= ber

        print("Hurdle 1 Pass? {}".format(hurdle_pass))

        result = {'test_label':args.test_label,
                  'num_truth_packets':len(truth_packets),
                  'num_decoded_packets':len(decoded_packets),
                  'ber':ber,
                  'hurdle_pass':hurdle_pass}


        with open(args.results_name, 'w') as f:
            f.write(json.dumps(result))

    except KeyboardInterrupt:
        print("process interrupted by keyboard")

if __name__ == "__main__":

    sys.exit(main())
