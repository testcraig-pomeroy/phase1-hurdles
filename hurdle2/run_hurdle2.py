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
from generate_band_plan import generate_band_plan

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
        
        # store guard bins for scoring
        for bin_ind in s["guard_bins"]:
            answer[bin_ind] = "GUARD"
            
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

        parser.add_argument("--host",              type=str,   default="0.0.0.0",       help="IP address that this script will listen on for incoming connections") 
        parser.add_argument("--tx-port",           type=int,   default=9091,            help="Port that sample transmitting TCP Server will listen to for incoming connections") 
        parser.add_argument("--rpc-port",          type=int,   default=9090,            help="Port for RPC connections") 
        parser.add_argument("--bandplan",          type=str,   default="bandplan.json", help="IP address that this script will listen on for incoming connections")         
        parser.add_argument("--sample-duration",   type=float, default=3.0,             help="Set the duration of the test transmission in seconds")
        parser.add_argument("--fm-file-start",     type=float, default=27.75,           help="Set the starting point at which to pull samples from the fm transmit file")
        parser.add_argument("--sample-file",       type=str,   default="samples.dat",   help="path to store transmit sample recording to")

        parser.add_argument("--channel-bandwidth", type=float, default=3e6,             help="Total channel bandwidth, Hz")
        parser.add_argument("--n-bins",            type=int,   default=30,              help="Number of frequency bins") 
        parser.add_argument("--n-signals",         type=int,   default=6,               help="Number of signals to generate") 
        parser.add_argument("--min-snr-db",        type=float, default=15,              help="Minimum SNR per signal") 
        parser.add_argument("--max-snr-db",        type=float, default=20,              help="Maximum SNR per signal") 
        parser.add_argument("--instance-seed",     type=int,   default=None,            help="Random generator seed")
        parser.add_argument("--max-signal-bins",   type=int,   default=4,               help="Maximum signal width in bins") 
        parser.add_argument("--max-tries",         type=int,   default=100,             help="Maximum number of iterations to run random signal generator before giving up") 
        parser.add_argument("--test-label",        type=str,   default="test",          help="label to attach inside json results file")
        
        # Process arguments
        args = parser.parse_args()

        print(args)

        # Total bandwidth of the channel
        channel_bandwidth = args.channel_bandwidth

        # The number of bins to divide the channel into
        n_bins = args.n_bins

        # The number of signals to generate
        n_signals = args.n_signals

        # Minimum SNR in dB
        min_snr_db = args.min_snr_db
        max_snr_db = args.max_snr_db
        
        # Valid signal types
        signal_types = ('FM','QPSK','GMSK')

        # Random generator seed.  Set to "None" for random selection
        instance_seed = args.instance_seed

        #Maximum width of a signal in bins
        max_signal_bins= args.max_signal_bins

        #Maximum number of attempts before aborting
        max_tries = args.max_tries
        
        band_plan = generate_band_plan(channel_bandwidth, n_bins, n_signals, min_snr_db, 
                                       max_snr_db, signal_types, instance_seed, max_signal_bins,
                                       max_tries )

        with open(args.bandplan, 'w') as f:
            json.dump(band_plan, f)
        
        with open(args.bandplan, 'r') as f:
            band_plan = yaml.safe_load(f)
        
        answer = bandplan_to_answer(band_plan)

        print("correct answer is {}".format(answer))

        p1 = multiprocessing.Process(target=runScoringServer, args=(args.host, args.rpc_port, answer, args.test_label))

        tx = Transmitter(band_plan=band_plan, 
                         file_len_s=args.sample_duration,
                         fm_file_start_s=args.fm_file_start,
                         sample_file_name=args.sample_file)
        

        p2 = multiprocessing.Process(target=tx.go, args=(True, args.host, args.tx_port))

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
