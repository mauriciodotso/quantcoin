import logging
import string
import random


class QuantCoin:

    def __init__(self):
        self._blocks = []
        self._peers = []
        self._wallets = []

    def load(self):
        logging.debug("Loading from database")
        pass

    def all_nodes(self):
        logging.debug("All nodes requested")
        pass

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
        self._wallets.append(wallet)

    def store_block(self, block):
        self._blocks.append(block)

    def store_node(self, node):
        self._peers.append(node)

    @staticmethod
    def create_wallet(seed=None):
        logging.debug("Creating wallet(seed={})".format(seed))
        if seed is None:
            seed = ''.join([random.SecureRandom().
                            choice(string.ascii_letters + string.digits)
                            for _ in range(50)])

        # TODO generate ecdsa keys
