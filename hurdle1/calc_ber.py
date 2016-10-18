#!/usr/bin/python
# encoding: utf-8


from argparse import ArgumentDefaultsHelpFormatter
from argparse import ArgumentParser
import binascii
from itertools import izip
import json
import struct
import sys



PACKET_HEADER_FMT = ">II4B4Ii"
PACKET_HEADER_LEN = struct.calcsize(PACKET_HEADER_FMT)
print("packet header is now {} bytes".format(PACKET_HEADER_LEN))


FRAME_HEADER_FMT = ">II"
FRAME_HEADER_LEN = struct.calcsize(FRAME_HEADER_FMT)
print("frame header is now {} bytes".format(FRAME_HEADER_LEN))

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


def main(argv=None):

    preamble = 0x99999999
    sync = 0x1ACFFC1D


    try:
        # Setup argument parser
        parser = ArgumentParser(description="Hurdle 1 BER calculator", formatter_class=ArgumentDefaultsHelpFormatter)
        parser.add_argument("--decoded-name", type=str, default="decoded.bin", help="path to find decoded packets")
        parser.add_argument("--truth-name", type=str, default="truth_packets.bin", help="path to find true values of generated packets")
        parser.add_argument("--results-name", type=str, default="results.json", help="path to store results file")
        parser.add_argument("--team-name", type=str, default="team-name", help="Name of the team that submitted solution")
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
        decoded_packets = parse_packets(preamble, sync, decoded_bytes)

        truth_packet_counters = [struct.unpack(">I", p[12:16])[0] for p in truth_packets]

        # storing as a set to remove duplicate packet counters
        decoded_packet_counters = set([struct.unpack(">4I", p[12:28])[0] for p in decoded_packets])
        decoded_packet_crcs = [struct.unpack(">i", p[28:32])[0] for p in decoded_packets]

        correct_count = 0
        num_good_crcs = 0

        # this ber calculator is not the final version that will be used for scoring
        for i, c in enumerate(decoded_packet_counters):
            # try to match each decoded packet counter c against a truth packet counter t
            matched_ind = next((i for i, t in enumerate(truth_packet_counters) if t == c), -1)

            # print(matched_ind)
            if matched_ind >= 0:

                d_crc = decoded_packet_crcs[i]
                crc_check = binascii.crc32(decoded_packets[i][:PACKET_HEADER_LEN - 4])
                # check that CRCs match

                if crc_check == d_crc:

                    num_good_crcs += 1

                    tp = bytearray(truth_packets[matched_ind])
                    dp = bytearray(decoded_packets[i])

                    tp = tp[:-8]
                    dp = dp[:-8]

                    bit_errors = sum([bin(a ^ b).count("1") for a, b in izip(tp, dp)])
                    bits_correct = 8 * len(tp) - bit_errors

                    if bit_errors > 0:
                        print("Packet found with {} bit errors. Bits correct was {}".format(bit_errors, bits_correct))
                        print("truth:  ", binascii.hexlify(tp))
                        print("decoded:", binascii.hexlify(dp))
                    else:
                        print("packet correct")
                else:
                    print("crc fail")

            else:
                bit_errors = 8 * len(decoded_packets[i])
                bits_correct = 0
                print("No packet found, adding {} bit errors".format(bit_errors))

            correct_count += bits_correct

        bit_count = 8 * sum(len(t) for t in truth_packets)
        print("found {} packets out of total {}".format(len(decoded_packets), len(truth_packets)))

        ber = (bit_count - correct_count) / float(bit_count)
        print("Bit error rate was {}, correct bits: {} total bits {}".format(ber, correct_count, bit_count))

        hurdle_pass = args.ber_threshold >= ber

        print("Hurdle 1 Pass? {}".format(hurdle_pass))

        result = {'team_name':args.team_name,
                  'num_truth_packets':len(truth_packets),
                  'num_decoded_packets':len(decoded_packets),
                  'num_unique_packet_counters':len(decoded_packet_counters),
                  'num_passing_crcs':num_good_crcs,
                  'num_truth_bits':bit_count,
                  'num_correct_bits':correct_count,
                  'ber':ber,
                  'hurdle_pass':hurdle_pass}


        with open(args.results_name, 'w') as f:
            f.write(json.dumps(result))

    except KeyboardInterrupt:
        print("process interrupted by keyboard")

if __name__ == "__main__":

    sys.exit(main())
