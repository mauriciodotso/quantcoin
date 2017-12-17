import binascii
import json
import logging
import math
import threading
import time

from block import Block
from node import Network, Node
from transaction import Transaction


class Miner(Node):
    """
    This node supports mining. It will register transactions announced and
    will try to include them on new blocks it is mining. When a new block is
    announced it will start mining from that block
    """

    def __init__(self, wallet, quantcoin, ip="0.0.0.0", port=65345):
        Node.__init__(self, quantcoin=quantcoin, ip=ip, port=port)

        self._wallet = wallet
        self._transaction_queue = []
        self._transaction_queue_lock = threading.Lock()

        known_blocks = quantcoin.blocks()
        self._last_block = known_blocks[-1].digest() if len(known_blocks) > 0 else 'genesis_block'
        self._last_block_index = number_of_blocks = len(known_blocks)
        self._mining = False
        self._network_difficulty = int(52 - (50 / 1 + number_of_blocks // 100000))

    def new_block(self, data, *args, **kwargs):
        """
        Removes transactions already mined from the queue and changes previous block.

        :param data: The new block as a dictionary
        """
        Node.new_block(self, data, args, kwargs)

        block = Block.from_json(data['block'])

        self._transaction_queue_lock.acquire()
        # Remove transactions already processed from the queue
        for transaction in block.transactions():
            if transaction in self._transaction_queue:
                self._transaction_queue.remove(transaction)
        self._transaction_queue_lock.release()

        known_blocks = self._quantcoin.blocks()
        self._last_block = known_blocks[-1].digest() if len(known_blocks) > 0 else 'genesis_block'
        self._last_block_index = number_of_blocks = len(known_blocks)
        self._network_difficulty = int(52 - (50 / 1 + number_of_blocks // 100000))

    def send(self, data, *args, **kwargs):
        """
        Register transaction on queue for mining

        :param data: The message data for transaction
        """
        Node.send(self, data, args, kwargs)
        logging.debug("Transaction received. {}".format(data['transaction']))
        transaction_data = json.loads(data['transaction'])
        transaction = Transaction(from_wallet=transaction_data['body']['from'],
                                  to_wallets=transaction_data['body']['to'],
                                  signature=transaction_data['signature'],
                                  public_key=transaction_data['public_key'])

        if transaction.verify():
            self._transaction_queue_lock.acquire()
            self._transaction_queue.append(transaction)
            self._transaction_queue_lock.release()

    def mine(self, min_transaction_count=0, min_commission=-1):
        """
        Does the mining process based on a mining queue.

        :param min_transaction_count: The minimum number of transactions to be added to the block
        :param min_commission: The minimum commission to start mining
        """
        self._mining = True
        print("Starting miner")
        network = Network(self._quantcoin)
        while self._mining:
            known_blocks = self._quantcoin.blocks()
            number_of_blocks = len(known_blocks)
            self._last_block = known_blocks[-1].digest() if number_of_blocks > 0 else 'genesis_block'
            self._transaction_queue_lock.acquire()
            if min_transaction_count > len(self._transaction_queue):
                logging.info("Not enough transactions: {} transactions.".format(len(self._transaction_queue)))
                self._transaction_queue_lock.release()
                time.sleep(5)
                continue
            if min_commission > 0:
                commission = sum(t.commission() for t in self._transaction_queue)
                if commission < min_commission:
                    logging.info("Target commission not reached: {} commission reached.".format(commission))
                    self._transaction_queue_lock.release()
                    time.sleep(5)
                    continue

            block = Block(author=self._wallet,
                          transactions=self._transaction_queue,
                          previous_block=binascii.a2b_base64(self._last_block))

            self._transaction_queue = []
            self._transaction_queue_lock.release()

            logging.info("Starting to mine block.")
            block_index = self.last_block_index()
            start_nonce = 0
            while (block_index == self.last_block_index() and self.mining() and
                    not block.proof_of_work(self._network_difficulty,
                                            start_nonce, start_nonce + 100)):
                start_nonce += 101

            if block.nonce() is not None:
                network.new_block(block)
                logging.info("Block found! Block digest: {}; Transactions: {}"
                             .format(block.digest(), len(block.transactions())))
                print("Block found! Block digest: {}; Transactions: {}; difficulty: {}"
                      .format(block.digest(), len(block.transactions()), self._network_difficulty))

        print("Terminating miner...")

    def last_block_index(self):
        """
        Returns the last known block index
        """
        return self._last_block_index

    def stop_mining(self):
        """
        Turns off mining
        """
        self._mining = False

    def mining(self):
        """
        Informs if mining is active
        :return: True if mining
        """
        return self._mining
