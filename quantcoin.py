import logging
import string
import random
import json
from block import Block
import os


class QuantCoin:

    def __init__(self):
        self._blocks = []
        self._peers = []
        self._wallets = []

    def load(self, database):
        logging.debug("Loading from database")
        if os.path.exists(database):
            with open(database, 'rb') as fp:
                storage = json.load(fp)
                blocks = storage['blocks']
                self._blocks = [Block.from_json(block) for block in blocks]
                self._peers = [tuple(peer) for peer in storage['peers']]
                self._wallets = [tuple(wallet)
                                 for wallet in storage['wallets']]

                print(self._peers)
        else:
            logging.debug("Requested database does not exists(database={})".
                          format(database))
            return False

    def save(self, database):
        logging.debug("Saving to database")
        with open(database, 'wb') as fp:
            json_blocks = [block.json() for block in self._blocks]
            storage = {
                'blocks': json_blocks,
                'peers': self._peers,
                'wallets': self._wallets
                }
            json.dump(storage, fp)

    def all_nodes(self):
        logging.debug("All nodes requested")
        return self._peers

    def blocks(self):
        logging.debug("All blocks requested")
        return self._blocks

    def block(self, start, end):
        logging.debug("Block range requested(from={},to={})".
                      format(start, end))
        return self._blocks[start:end]

    def wallets(self):
        return self._wallets

    def store_wallet(self, wallet):
        if wallet not in self._wallets:
            self._wallets.append(wallet)

    def store_block(self, block):
        if block not in self._blocks:
            self._blocks.append(block)

    def store_node(self, node):
        if node not in self._peers:
            self._peers.append(node)

    @staticmethod
    def create_wallet(seed=None):
        logging.debug("Creating wallet(seed={})".format(seed))
        if seed is None:
            seed = ''.join([random.SystemRandom().
                            choice(string.ascii_letters + string.digits)
                            for _ in range(50)])

        # TODO generate ecdsa keys
        return seed
