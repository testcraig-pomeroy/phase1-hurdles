# this module will be imported in the into your flowgraph

import random

from thrift import Thrift
from thrift.protocol import TBinaryProtocol
from thrift.transport import TSocket
from thrift.transport import TTransport

from hurdle2_rpc import Hurdle2Scoring
from hurdle2_rpc.ttypes import BinContents as BC


def submit_my_answer(answer, host, port):

    success = False
    try:

        # Make socket
        transport = TSocket.TSocket(host, port)

        # Buffering is critical. Raw sockets are very slow
        transport = TTransport.TBufferedTransport(transport)

        # Wrap in a protocol
        protocol = TBinaryProtocol.TBinaryProtocol(transport)

        # Create a client to use the protocol encoder
        # client = Calculator.Client(protocol)
        client = Hurdle2Scoring.Client(protocol)

        # Connect!
        transport.open()

        # send answer to the scoring server
        success = client.submitAnswer(answer)

        # Close!
        transport.close()

    except Thrift.TException as tx:
        print('%s' % tx.message)

    return success

def make_random_guess(num_bins):

    choices = [BC.NOISE, BC.FM, BC.GMSK, BC.QPSK]
    answer = {}

    for i in range(num_bins):
        answer[i] = random.choice(choices)

    return answer

