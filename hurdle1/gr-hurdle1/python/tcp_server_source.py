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
# Boston, MA 02110-1301, USA.TCP_USER_TIMEOUTTCP_USER_TIMEOUT
# 

import select
import socket
import sys
import math
import time

from block_utils import itemsize2dtype
import numpy as np
from gnuradio import gr

# Stealing from /usr/include/netinet/tcp.h
TCP_USER_TIMEOUT = 18

class tcp_server_source(gr.sync_block):
    """
    docstring for block tcp_server_source
    """
    def __init__(self, itemsize, host, port):
        gr.sync_block.__init__(self,
            name="tcp_server_source",
            in_sig=None,
            out_sig=[itemsize2dtype[itemsize]])
        
        self.itemsize = itemsize
        self.host = host
        self.port = port
        
        self.client_socket = None
        self.socket_timeout = 0.1
        
        
        self.itemtype = itemsize2dtype[itemsize]
        
        print "Starting server socket"
        print "listening on host {} port {}".format(host, port)
        try:   
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((host, port))
            self.server_socket.listen(1)
        except KeyError as err: #this is the wrong exception to catch, just a placeholder 
            raise(err)
        
        # store off partial items read from socket
        self.residue = ''
            
    def accept_connection(self, timeout):
        
        read_list = [self.server_socket]

        while True:
            readable, writable, exceptional = select.select(read_list, [], [], timeout)
            
            if not (readable or writable or exceptional):
                # we've timed out
                return False
            
            elif exceptional:
                print("Exceptional socket in accept. Do something about this?")
                raise Exception
            
            # the only thing in the read list is the server socket, so if
            # something is readable, we must have a new connection
            else:
            
                self.client_socket, address = self.server_socket.accept()
                print "Connection from", address

                self.client_socket.settimeout(timeout)               
                return True
            

    def read_items(self, num_bytes, timeout):
        '''
        read from the socket and combine results with any item fragments 
        sitting around in self.residue
        
        return the complete items and any remaining fragments
        
        '''
        read_list = [self.client_socket]

        while True:
            readable, writable, exceptional = select.select(read_list, [], [], timeout)
            
            if not (readable or writable or exceptional):
                # we've timed out, for example if the client was still crunching on data
                timed_out = True
                items = None
                fragment = None
                
            
            elif exceptional:
                print("Exceptional socket in read_items. Do something about this?")
                timed_out = None
                items = None
                fragment = None
                
                raise Exception            
            # the only thing in the read list is the client socket, so if
            # something is readable, pull some samples in
            else:
                
                timed_out = False
                    
                residue_len = len(self.residue)
                
                recv = self.client_socket.recv(num_bytes)
                
                
                num_complete_items = int(math.floor((len(recv) + residue_len)/self.itemsize))
                
                
                items = np.fromstring(self.residue + recv[:num_complete_items*self.itemsize-residue_len], 
                                      dtype=self.itemtype)
                
                fragment = recv[num_complete_items*self.itemsize-residue_len:]
                
                #print("generated {} items with {} remaining fragment bytes".format(len(items), len(fragment)))
                
                
            return timed_out, items, fragment
            

    def work(self, input_items, output_items):
        out = output_items[0]
        
        if self.client_socket is None:
            connect_success = self.accept_connection(self.socket_timeout)
            
            # if the accept connection call timed out, return zero and try again
            # this resolves deadlocks if there are multiple servers in a given
            # flowgraph
            if not connect_success:
                return 0
        
        # if we're here, we must have had a client socket at one point.
        
        # figure out how much to try to read from the socket
        n_output_items = len(out)
        n_bytes_to_read = n_output_items*self.itemsize - len(self.residue)
        
        
        timed_out, items, fragment = self.read_items(n_bytes_to_read, timeout=self.socket_timeout)
        
        
        if not timed_out:
        
            # detect client socket closing
            if len(items) == 0:
                print("client closed connection, shutting down tcp server source")
                return -1
        
            else:
        
                self.residue = fragment
                out[:len(items)] = items
                return len(items)
        
        else:
            return 0
        


