#!/usr/bin/python
from node import Node
import logging


class Miner(Node):
    '''
    The full nodex
    '''

    def new_block(self, data, *args, **kwargs):
        '''
        Verifies and interrupts mining if a new block was found
        '''
        Node.new_block(self, data, args, kwargs)

    def send(self, data, *args, **kwargs):
        '''
        Adds the transactions to the blocks queue to mine
        '''
        logging.debug("Transaction received. Adding to the queue.")

if __name__ == "__main__":
    print("lallala")
