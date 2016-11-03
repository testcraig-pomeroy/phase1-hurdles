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
# Boston, MA 02110-1301, USA.
# 

import select
import socket
import sys
import math
import time

import numpy as np
from gnuradio import gr

from block_utils import itemsize2dtype

class tcp_server_sink(gr.sync_block):
    """
    docstring for block tcp_server_sink
    """
    def __init__(self, itemsize, host, port):
        gr.sync_block.__init__(self,
            name="tcp_server_sink",
            in_sig=[itemsize2dtype[itemsize]],
            out_sig=None)

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

    def write_items(self, items, timeout):
        '''
        write to the socket and hold on to any item fragments that didn't 
        make it across. 
        
        return any remaining fragments
        
        '''
        write_list = [self.client_socket]

        while True:
            readable, writable, exceptional = select.select([], write_list, [], timeout)
            
            if not (readable or writable or exceptional):
                # we've timed out, for example if the client was still crunching on data
                timed_out = True
                items_written = 0                
                items_consumed = 0
                
            elif exceptional:
                print("Exceptional socket in read_items. Do something about this?")
                timed_out = None
                items_consumed = 0
                
                raise Exception            
            # the only thing in the read list is the client socket, so if
            # something is readable, pull some samples in
            else:
                
                timed_out = False
                    
                residue_len = len(self.residue)
                
                
                write_buff = self.residue + np.array(items).tobytes()
                
                try:
                    bytes_written = self.client_socket.send(write_buff)
                except socket.error as err:
                    errorcode=err[0]
                    
                    if errorcode == socket.errno.ECONNRESET:
                        print("connection reset by client, shutting down")
                    else:
                        print("caught exception {} on write, trying to shut down".format(err))
                        
                        
                    timed_out = False
                    items_consumed = -1
                    return timed_out, items_consumed
                if bytes_written == 0:
                    print("we couldn't write any bytes. Weird")
                    
                # we were only able to write some bytes from the residue, but not all
                elif ( bytes_written > 0) and (bytes_written < residue_len):
                    self.residue = self.residue[bytes_written:]
                    items_consumed = 0
                
                else:    
                    items_consumed = int(math.ceil( (bytes_written-residue_len)/float(self.itemsize)))
                    partial_bytes = items_consumed*self.itemsize - (bytes_written-residue_len)
                    self.residue = write_buff[items_consumed*self.itemsize:items_consumed*self.itemsize+partial_bytes]
                    
                                
                #print("generated {} items with {} remaining fragment bytes".format(len(items), len(fragment)))
                
                
            return timed_out, items_consumed




    def work(self, input_items, output_items):
        
        #print("server sink work called")

        if self.client_socket is None:
            connect_success = self.accept_connection(self.socket_timeout)
            
            # if the accept connection call timed out, return zero and try again
            # this resolves deadlocks if there are multiple servers in a given
            # flowgraph
            if not connect_success:
                return 0
        
        # if we're here, we must have had a client socket at one point.
        
        in0 = input_items[0]
        
        #print("processing input of len {}".format(len(in0)))
        timed_out, items_consumed = self.write_items(in0, timeout=self.socket_timeout)
        
        if not timed_out:
            return items_consumed
        
        else:
            return 0

        
        
        # <+signal processing here+>
        return len(input_items[0])

        
        
    def stop(self):
        
        print("tcp server sink complete, shutting down socket")
        
        try:
        
            self.client_socket.shutdown(socket.SHUT_RDWR)
            self.client_socket.close()
        except socket.error as err:
            errorcode = err[0]
            if errorcode == socket.errno.ENOTCONN:
                pass
            else:
                print("caught unhandled exception while shutting down: {}".format(err))    
        
        print("server sink shutdown complete")    
        return True    

