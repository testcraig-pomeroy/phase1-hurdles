#!/usr/bin/env python

# This file generates a band plan for the Hurdle 2 transmitter.
#
# The output is a configuration file that will be read by the
# transmit flowgraph and used to instantiate the transmitters.
#
# All configuration of the generator is done here, inline.



#------------------------
# Problem Statement
#------------------------

# The problem statement from the hurdle document is:
# Develop a classifier that can identify the occupied
# range and type of six simultaneous non-overlapping
# signals within a 3 MHz bandwidth channel. Each signal
# will be continuous in time and fixed in frequency for
# the duration of the test vector. The signals that may
# be present are: analog FM, QPSK, and GMSK.
# Multiple or no instances of a particular signal type
# may be present. Each signal is present at the same
# total power as each of the others. AWGN is present
# in the 3 MHz channel. The SNR seen by any individual
# signal type will be greater than or equal to 15 dB.

#------------------------
# Caveats
#------------------------
#
# Based on our understanding, "SNR" is defined as the
# height above the noise floor, in dB, of a given signal
# whithin the 100kHz band.  This is not the traditional
# definition of SNR, but will be how it is used here
#
# The generator does not guarantee at least one type of
# each modulator, it is uniformly selected so you may end
# up with instances without some types

#------------------------
# System Configuration
#------------------------

# Total bandwidth of the channel
channel_bandwidth = 3e6

# The number of bins to divide the channel into
n_bins = 30

# The number of signals to generate
n_signals = 6

# Minimum SNR in dB
min_snr_db = 15

# Valid signal types
signal_types = ('FM','QPSK','GMSK')

# Random generator seed.  Set to "None" for random selection
instance_seed = None

#Maximum width of a signal in bins
max_signal_bins= 4

#Maximum number of attempts before aborting
max_tries = 100

#------------------------
# Main Process
#
# Don't change anything below this line
#------------------------

import random
import sets
import json
#------------------------
# Parameter Calculation
#------------------------

bin_bandwidth = channel_bandwidth/n_bins

#------------------------
# Signal Generation
#------------------------

random.seed(instance_seed)

signals = list() #Store the signals we generate
tries = 0

while (len(signals) < n_signals) and (tries < max_tries):
    tries+=1
    signal = dict()

    #Randomly generate a bandwidth
    signal['n_bins'] = random.randint(1, max_signal_bins)
    half_bins = int(signal['n_bins']/2)

    #Randomly generate a center bin
    # Note: Subtracting 1 from randint upper bound since randint upper bound is inclusive of the endpoint 
    signal['center_bin'] = random.randint( 1+half_bins,n_bins - half_bins -1 )

    signal['occupied_bins'] = sets.Set( \
            signal['center_bin'] - half_bins + x \
            for x in range(0,signal['n_bins']) )

    #Verify that we aren't stepping on an existing signal
    overlaps = False
    for existing in signals:
        if( len( \
        signal['occupied_bins'].intersection(existing['occupied_bins'])\
                  )>0):
            #print "[%d tries] This signal overlaps an existing one, retrying..." % tries
            overlaps=True
            break
    if( overlaps == True): continue

    #Randomly generate a signal type
    signal['modulation_type'] = random.choice(signal_types)

    #Add this signal to the primary list
    signals.append(signal)

# Get rid of the sets, since they're python specific
for signal in signals:
    signal['occupied_bins'] = list(signal['occupied_bins'])

# Print out the bands
if(False):
    print("\n\nGenerated the following %d signals" % len(signals))
    for signal in signals:
        print(signal)

# Write out the plan
band_plan = dict()

band_plan['freq_span'] = channel_bandwidth
band_plan['n_bins']    = n_bins
band_plan['n_signals'] = len(signals)
band_plan['signals'] = signals


# Writing JSON data
with open('band_data.json', 'w') as f:
     json.dump(band_plan, f)
