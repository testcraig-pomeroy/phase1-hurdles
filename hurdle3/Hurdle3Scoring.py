#!/usr/bin/python
# encoding: utf-8

from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter
import json
from matplotlib import pyplot as pp
import os
import sys
import time

from thrift import Thrift
from thrift.protocol import TBinaryProtocol
from thrift.transport import TSocket
from thrift.transport import TTransport

from hurdle3.ProbabilisticStateMachine import ProbabilisticStateMachine as PSM
from hurdle3_rpc import Hurdle3Execution
import matplotlib as mpl
import numpy as np
import random

def compute_score(action, state_prediction, state_actual,
                  no_collision_reward=1,
                  collision_penalty=-12,
                  prediction_success_reward=3):
    score = 0

    if action == state_actual:
        score += collision_penalty
    else:
        score += no_collision_reward

    if state_prediction == state_actual:
        score += prediction_success_reward

    return score

def expected_random_score(num_states,
                          no_collision_reward=1,
                          collision_penalty=-12,
                          prediction_success_reward=3):

    collision_rate = 1.0 / num_states


    expected_value = collision_rate * (collision_penalty + prediction_success_reward) + (1 - collision_rate) * no_collision_reward

    return expected_value



def execute_hurdle(make_plot=False, result_file="results.json", host='127.0.0.1', port=9090, seed=None, initial_state=None,
                   num_trials=10, num_rounds=30000, scoring_rounds=1000, test_label="team"):
    num_states = 10

    
    avg_score_threshold = 2.0
    trial_pass_threshold = 6

    expected = expected_random_score(num_states)
    print("expected score of random guesser is {}".format(expected * num_rounds))
    print("score required to pass a trial is {}".format(avg_score_threshold * num_rounds))
    print("Number of trials passed to pass Hurdle 3 is  {} out of {}".format(trial_pass_threshold, num_trials))


    # Make socket
    transport = TSocket.TSocket(host, port)

    # Buffering is critical. Raw sockets are very slow
    transport = TTransport.TBufferedTransport(transport)

    # Wrap in a protocol
    protocol = TBinaryProtocol.TBinaryProtocol(transport)

    # Create a client to use the protocol encoder
    client = Hurdle3Execution.Client(protocol)

    # Connect!
    transport.open()

    results = {"trials":{}, "test_label":test_label}

    
    # set up a dedicated random number generator
    # for this object to guarantee repeatability
    # of solution evaluation without forcing
    # each trial to use the same seed.
    # This ensures the same set of trial seeds will be used
    # when using the same top level seed
    rng = np.random.RandomState(seed)
      
    
    for t in range(num_trials):

        # generate a unique seed per trial
        trial_seed = rng.randint(0, 0xffffffff)         
        
        
        if initial_state is None:
            trial_initial_state = rng.choice(range(num_states))
        else:
            trial_initial_state = initial_state

        # create a new probabilistic state machine with potentaiily 
        # a new initial state and seed
        # at the start of each trial
        psm = PSM(num_states, trial_initial_state, trial_seed)

        
        print("starting trial {} of {} with trial seed {}".format(t,num_trials, trial_seed))

        # run the trial and store the trial results
        trial_results = run_trial(t, num_rounds, scoring_rounds, avg_score_threshold, client, psm)
        
        # add seed and initial state to trial_results
        trial_results["seed"] = trial_seed
        trial_results["initial_state"] = trial_initial_state

        results["trials"][t]=trial_results
        
    # count the number of trials that passed
    trials_passed = sum([results["trials"][i]["trial_pass"] for i in range(num_trials)])
    
    
    print("Number of trials passed: {} Number of trials passed required to pass Hurdle 3: {}".format(trials_passed, trial_pass_threshold))
    hurdle_pass = trials_passed >= trial_pass_threshold
    
    print("Hurdle 3 Passed? {}".format(hurdle_pass))

    results["main_seed"] = seed
    results["num_trials"]=num_trials
    results["num_states"]=num_states
    results["trials_passed"]=trials_passed
    results["trial_pass_threshold"]=trial_pass_threshold
    results["hurdle_pass"]=hurdle_pass
    
    

    with open(result_file, 'w') as f:

        f.write(json.dumps(results))
    
    print("Writing results to file: {}".format(result_file))
    #print("Results file: {}".format(results))

    client.stop()

#    if make_plot:
#
#        t = np.array(range(len(score_hist)))
#        expected = expected_random_score(num_states)
#        pp.plot(t, score_hist, t, t * expected, '--', t, t*avg_score_threshold, '--')
#        pp.legend(["trial result", "expected result from guessing", "success threshold"], loc='upper left')
#        pp.grid("on")
#        pp.xlabel("Iteration")
#        pp.ylabel("Score")
#        pp.title("Results Versus Expected Score of Random Guesser")
#
#
#        print("expected random score was {}".format(expected * num_rounds))
#        pp.show()




def run_trial(trial_num, num_rounds, scoring_rounds, avg_score_threshold, client, psm):

    t0 = time.time()
    score = 0

    current_score = None
    p_current_state = None
    d_current_state = None
    score_hist = [0,]*num_rounds

    for i in xrange(num_rounds):
        # print(i)
        # start up participant code without a reward
        if i == 0:
            # print("init")
            result = client.start()
            predicted_state = result.predicted_state
            p_next_state = result.next_state

            d_next_state = psm.start()

        else:
            # print("normal execution")
            result = client.step(reward=current_score, observation=d_current_state)
            predicted_state = result.predicted_state
            p_next_state = result.next_state

            d_next_state = psm.step(p_current_state)

        if i%5000 == 0:
            print("On round {} of {}".format(i,num_rounds))

        # print("p_next_state {} predicted state {} d_next_state {}".format(p_next_state, predicted_state, d_next_state))

        current_score = compute_score(p_next_state, predicted_state, d_next_state)

        p_current_state = p_next_state
        d_current_state = d_next_state

        
        score_hist[i] = current_score


    # compute score over the scoring rounds
    score = sum(score_hist[-scoring_rounds:])
    
    
    t1 = time.time()
    print("Trial Elapsed time: {}".format(t1 - t0))
    print("Trial score was {}".format(score))

    avg_score = score / float(scoring_rounds)
    print("average score required {}, average score received {}".format(avg_score_threshold, avg_score))
    
    if avg_score_threshold > avg_score:
        trial_pass = False
        print("Hurdle 3 Trial {} Failed".format(trial_num))
    else:
        trial_pass = True
        print("Hurdle 3 Trial {} Passed".format(trial_num))
    
    trial_result = {"start_time":t0,
                    "trial_duration":t1 - t0,
                    "num_rounds":num_rounds,
                    "scoring_rounds":scoring_rounds,
                    "final_score":score,
                    "avg_score_threshold":avg_score_threshold,
                    "trial_pass":trial_pass}

    return trial_result

def main(argv=None):  

    try:
        # Setup argument parser
        parser = ArgumentParser(description="Hurdle 3 Test Driver", formatter_class=ArgumentDefaultsHelpFormatter)

        parser.add_argument("--host",          type=str,            default="127.0.0.1",    help="IP address of the Solution container")  
        parser.add_argument("--rpc-port",      type=int,            default=9090,           help="Port for RPC connections") 
        parser.add_argument("--make-plot",     action='store_true', default=False,          help="Controls whether or not a plot of the score is generated")
        parser.add_argument("--result-file",   type=str,            default="results.json", help="where to save the results file")
        parser.add_argument("--seed",          type=int,            default=None,           help="Random number generator seed to use for repeatable tests")
        parser.add_argument("--initial-state", type=int,            default=None,           help="Initial state of state machine to use for repeatable tests")  
        parser.add_argument("--num-trials",    type=int,            default=10,             help="Number of trials to execute")
        parser.add_argument("--num-rounds",    type=int,            default=30000,          help="Number of rounds per trial to execute")
        parser.add_argument("--scoring-rounds",type=int,            default=1000,           help="Number of rounds at the end of the trial that count towards score")
        parser.add_argument("--test-label",    type=str,            default="team",         help="test label to include in results file")
        
        # Process arguments
        args = parser.parse_args()

        # Process arguments
        args = parser.parse_args()

        execute_hurdle(make_plot=args.make_plot, 
                       result_file=args.result_file,
                       host=args.host, 
                       port=args.rpc_port, 
                       seed=args.seed, 
                       initial_state=args.initial_state,
                       num_trials=args.num_trials,
                       num_rounds=args.num_rounds,
                       scoring_rounds=args.scoring_rounds,
                       test_label=args.test_label )

    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0


if __name__ == "__main__":

    sys.exit(main())
