#!/usr/bin/python
# encoding: utf-8
'''
run_hurdle2 -- shortdesc

run_hurdle2 is a description

'''

from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter
import json
import yaml
import multiprocessing
import os
import random
import sys

from hurdle2.ScoringServer import runScoringServer
from hurdle2.Transmitter import Transmitter

def bandplan_to_answer(bandplan):
    
    n_bins = bandplan["n_bins"]
    
    # initialize answer assuming all bins are noise
    answer = {}
    for i in range(n_bins):
        answer[i]="NOISE"
    
    # now search through band plan and add in the modulations we detect
    for s in bandplan["signals"]:
        for bin_ind in s["occupied_bins"]:
            # cross check that there are no overlaps
            if answer[bin_ind] == "NOISE":
                # store modulation type to bin. Force to uppercase
                answer[bin_ind] = s["modulation_type"].upper()
            else:
                print("overlap in bin {}, trying to set to {} when already set to {}".format(
                    bin_ind, s["modulation_type"].upper(), answer[bin_ind]))
    
    return answer


def main(argv=None): 
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)


    try:
        # Setup argument parser
        parser = ArgumentParser(description="Hurdle 2 Test Driver", formatter_class=ArgumentDefaultsHelpFormatter)

        parser.add_argument("--host",            type=str,   default="0.0.0.0",       help="IP address that this script will listen on for incoming connections") 
        parser.add_argument("--tx-port",         type=int,   default=9091,            help="Port that sample transmitting TCP Server will listen to for incoming connections") 
        parser.add_argument("--rpc-port",        type=int,   default=9090,            help="Port for RPC connections") 
        parser.add_argument("--bandplan",        type=str,   default="bandplan.json", help="IP address that this script will listen on for incoming connections")         
        parser.add_argument("--sample-duration", type=float, default=5.0,             help="Set the duration of the test transmission in seconds")
        parser.add_argument("--sample-file",     type=str,   default="samples.dat",   help="path to store transmit sample recording to")

        # Process arguments
        args = parser.parse_args()

        print(args)

        with open(args.bandplan, 'r') as f:
            bandplan = yaml.safe_load(f)
        
        answer = bandplan_to_answer(bandplan)

        print("correct answer is {}".format(answer))

        p1 = multiprocessing.Process(target=runScoringServer, args=(args.host, args.rpc_port, answer))
        
        tx = Transmitter(bandplan, file_len_s=args.sample_duration, sample_file_name=args.sample_file)

        p2 = multiprocessing.Process(target=tx.go, args=(args.host, args.tx_port))

        p1.start()
        p2.start()


        p1.join()
        print('Scoring process join complete.')

        p2.join()
        print('Gnuradio process join complete.')

    except KeyboardInterrupt:
        try:
            print("killing scoring server")
            p1.terminate()
            p1.join()

        except AssertionError:
            print("scoring server already shut down")

        try:
            print("killing gnuradio process")
            p2.terminate()
            p2.join()

        except AssertionError:
            print("gnuradio already shut down")

        ### handle keyboard interrupt ###
        return 0


if __name__ == "__main__":

    sys.exit(main())
