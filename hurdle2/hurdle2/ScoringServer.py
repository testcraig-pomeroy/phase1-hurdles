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

from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
from thrift.transport import TSocket
from thrift.transport import TTransport

from hurdle2_rpc import Hurdle2Scoring
from hurdle2_rpc.ttypes import BinContents


class ScoringHandler:
    def __init__(self, correct_answer=None, result_file="results.json"):
        self.lgo = {}

        self.correct_answer = correct_answer
        self.results_file = result_file

    def submitAnswer(self, answer):
        print('Received Answer: {}'.format(answer))

        if answer is not None:
            result = self.score_answer(answer)

            with open(self.results_file, 'w') as f:
                f.write(json.dumps(result))
        sys.exit()
        return True


    def score_answer(self, answer):

        score_threshold = 0.68

        # convert from enums to strings in solution
        for k, v in answer.iteritems():
            answer[k] = BinContents._VALUES_TO_NAMES[v]

        print('Converted Answer to: {}'.format(answer))


        num_bins = len(answer)

        # get characteristics of the solution for computing probabilities later
        num_occupied_bins = sum([ 1 for k, v in self.correct_answer.iteritems() if v != "NOISE"])
        num_unoccupied_bins = num_bins - num_occupied_bins

        num_detections = 0
        num_false_alarms = 0
        num_wrong_type_reports = 0



        for bin_num, bin_truth in self.correct_answer.iteritems():


            if bin_num not in answer.keys():
                # no change to score if the submitted answer didn't include an answer for the current bin
                print("warning: bin number {} not found in submitted answer".format(bin_num))
            else:

                bin_type = answer[bin_num]

                # look for correct detection
                if bin_truth != "NOISE" and bin_type != "NOISE":
                    num_detections += 1

                # look for false alarms
                if bin_truth == "NOISE" and bin_type != bin_truth:
                    num_false_alarms += 1

                # look for incorrect type reports
                if bin_type != "NOISE" and bin_type != bin_truth:
                    num_wrong_type_reports += 1

        # compute probabilities
        Pd = num_detections / float(num_occupied_bins)
        Pfa = num_false_alarms / float(num_unoccupied_bins)
        Pt = (num_detections - num_wrong_type_reports) / float(num_detections)

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


def runScoringServer(host="0.0.0.0", port=9090, correct_answer=None):

    try:
        handler = ScoringHandler(correct_answer=correct_answer)
        processor = Hurdle2Scoring.Processor(handler)
        transport = TSocket.TServerSocket(host=host, port=port)
        tfactory = TTransport.TBufferedTransportFactory()
        pfactory = TBinaryProtocol.TBinaryProtocolFactory()

        server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)

        print('Starting the scoring server on host {}, port {}'.format(host, port))
        server.serve()

    except SystemExit:
        print('Scoring done.')


