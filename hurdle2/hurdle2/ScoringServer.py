#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2016 DARPA.
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

import json
import sys
import threading
import time

from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
from thrift.transport import TSocket
from thrift.transport import TTransport

from hurdle2_rpc import Hurdle2Scoring
from hurdle2_rpc.ttypes import BinContents


class ScoringHandler:
    def __init__(self, correct_answer=None, result_file="results.json", test_label="test", exit_flag=None):

        self.correct_answer = correct_answer
        self.results_file = result_file
        self.test_label = test_label
        self.exit_flag = exit_flag
        
    def submitAnswer(self, answer):
        print('Received Answer: {}'.format(answer))

        answer_valid = False
        
        if answer is not None:
            answer_valid = self.validate_answer(answer)
        
        if answer_valid:
            print("Answer passed validation check, now scoring")
            result = self.score_answer(answer)
        else:
            print("Answer did not pass validation check, will not be scored")
            print("Hurdle 2 Failed")
            result = {'hurdle_pass':False}
            
        
        result["test-label"]=self.test_label
        result["answer-valid"]=answer_valid
        
        with open(self.results_file, 'w') as f:
            f.write(json.dumps(result))

        # announce that the server can be shut down now
        self.exit_flag.set()
        return answer_valid

    def validate_answer(self, answer):
        '''
        Check that the answer submitted is scorable
        '''
        
        answer_valid = True
        
        # check for missing bins
        for k in self.correct_answer.keys():
            if k not in answer:
                answer_valid = False

        return answer_valid

    def score_answer(self, answer):

        score_threshold = 0.68

        # convert from enums to strings in solution
        for k, v in answer.iteritems():
            answer[k] = BinContents._VALUES_TO_NAMES[v]

        print('Converted Answer to: {}'.format(answer))


        num_bins = len(answer)

        # get characteristics of the solution for computing probabilities later
        num_occupied_bins = sum([ 1 for k, v in self.correct_answer.iteritems() if (v != "NOISE") and (v!="GUARD")])
        num_unoccupied_bins = num_bins - num_occupied_bins

        num_detections = 0
        num_false_alarms = 0
        num_wrong_type_reports = 0



        for bin_num, bin_truth in self.correct_answer.iteritems():


            if bin_num not in answer.keys():
                # no change to score if the submitted answer didn't include an answer for the current bin
                print("warning: bin number {} not found in submitted answer".format(bin_num))
            elif bin_truth == "GUARD":
                print("Not scoring guard bin in bin number {}".format(bin_num))
            else:

                bin_type = answer[bin_num]

                # look for detection of any signal in a bin not containing noise
                if bin_truth != "NOISE" and bin_type != "NOISE":
                    num_detections += 1

                # look for false alarms
                if bin_truth == "NOISE" and bin_type != bin_truth:
                    num_false_alarms += 1

                # look for incorrect type reports
                if bin_type != "NOISE" and bin_type != bin_truth:
                    num_wrong_type_reports += 1
                    
        # compute probabilities
        if num_occupied_bins > 0:
            Pd = num_detections / float(num_occupied_bins)
        else:
            # doesn't make for an interesting test, but I guess you shouldn't be 
            # penalized if there's nothing to detect....
            Pd = 1.0
        
        if num_unoccupied_bins > 0:
            Pfa = num_false_alarms / float(num_unoccupied_bins)
        else:
            # this shouldn't be possible given the use of guard bins but let's be thorough
            Pfa = 0.0
            
        if num_detections > 0:    
            Pt = (num_detections - num_wrong_type_reports) / float(num_detections)
        else:
            # If you have no detections, you have no correct type reports
            Pt = 0.0

        score = Pd * (1 - Pfa) * Pt

        print("Minimum score needed: {} Score received: {}".format(score_threshold, score))

        if score_threshold > score:
            print("Hurdle 2 Failed")
            hurdle_pass = False
        else:
            print("Hurdle 2 Passed")
            hurdle_pass = True

        result = {'num_bins':num_bins,
                  'num_occupied_bins':num_occupied_bins,
                  'num_detections':num_detections,
                  'num_false_alarms':num_false_alarms,
                  'num_wrong_type_reports':num_wrong_type_reports,
                  'Pd':Pd,
                  'Pfa':Pfa,
                  'Pt':Pt,
                  'score':score,
                  'hurdle_pass':hurdle_pass, }

        print("Detailed Results: {}".format(result))
        return result


def runScoringServer(host="0.0.0.0", port=9090, correct_answer=None, test_label="test"):

    try:
        exit_flag = threading.Event()
        wait_time = 1.0
        
        handler = ScoringHandler(correct_answer=correct_answer, test_label=test_label, exit_flag=exit_flag)
        processor = Hurdle2Scoring.Processor(handler)
        transport = TSocket.TServerSocket(host=host, port=port)
        tfactory = TTransport.TBufferedTransportFactory()
        pfactory = TBinaryProtocol.TBinaryProtocolFactory()

        server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)

        print('Starting the scoring server on host {}, port {}'.format(host, port))
        
        server_thread = threading.Thread(name='thrift-server', 
                                         target=server.serve,
                                         )
        server_thread.start()
        
        # wait for Scoring Handler to signal that it is done
        ready_to_exit = exit_flag.wait()
        print('Shutting Thrift server down in {} seconds'.format(wait_time))
        time.sleep(wait_time)
        
        transport.close()
        
    except SystemExit:
        print('Scoring done.')


