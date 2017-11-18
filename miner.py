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
        self._last_block_index = len(known_blocks)
        self._mining = False
        self._network_difficulty = int(2 + math.sqrt(len(known_blocks)))

    def new_block(self, data, *args, **kwargs):
        """
        Removes transactions already mined from the queue and changes previous block.

        :param data:
        :param args:
        :param kwargs:
        :return:
        """
        Node.new_block(self, data, args, kwargs)
        self._last_block_index += 1

        block = Block.from_json(data)
        self._transaction_queue_lock.acquire()
        # Remove transactions already processed from the queue
        for transaction in block.transactions():
            if transaction in self._transaction_queue:
                self._transaction_queue.remove(transaction)
        self._transaction_queue_lock.release

        known_blocks = self._quantcoin.blocks()
        self._last_block = known_blocks[-1].digest() if len(known_blocks) > 0 else 'genesis_block'
        print("last_block: {}".format(self._last_block))
        self._last_block_index = len(known_blocks)

    def send(self, data, *args, **kwargs):
        """
        Register transaction on queue for mining

        :param data:
        :param args:
        :param kwargs:
        :return:
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
        self._mining = True
        # print("Starting mining")
        network = Network(self._quantcoin)
        while self._mining:
            # print("acquiring _transaction_queue_lock")
            known_blocks = self._quantcoin.blocks()
            self._last_block = known_blocks[-1].digest() if len(known_blocks) > 0 else 'genesis_block'
            self._transaction_queue_lock.acquire()
            if min_transaction_count > len(self._transaction_queue):
                logging.info("Not enough transactions: {} transactions.".format(len(self._transaction_queue)))
                print("Not enough transactions: {} transactions.".format(len(self._transaction_queue)))
                self._transaction_queue_lock.release()
                time.sleep(5)
                continue
            if min_commission > 0:
                commission = sum(t.commission() for t in self._transaction_queue)
                if commission < min_commission:
                    logging.info("Target commission not reached: {} commission reached.".format(commission))
                    print("Target commission not reached: {} commission reached.".format(commission))
                    self._transaction_queue_lock.release()
                    time.sleep(5)
                    continue

            block = Block(author=self._wallet,
                          transactions=self._transaction_queue,
                          previous_block=binascii.a2b_base64(self._last_block))
            self._transaction_queue_lock.release()
            logging.info("Starting to mine block.")
            # print("Starting to mine block {}.".format(self.last_block_index()))
            block_index = self.last_block_index()
            start_nonce = 0
            while (block_index == self.last_block_index() and not block.proof_of_work(self._network_difficulty,
                                                                                      start_nonce, start_nonce + 100)):
                start_nonce += 101

            if block.nonce() is not None:
                logging.info("Block found! Block digest: {}; Transactions: {}"
                             .format(block.digest(), len(block.transactions())))
                print("Block found! Block digest: {}; Transactions: {}"
                      .format(block.digest(), len(block.transactions())))

                self._transaction_queue_lock.acquire()
                self._transaction_queue = []
                self._transaction_queue_lock.release()

                network.new_block(block)

    def last_block_index(self):
        """
        Returns the last known block index
        """
        return self._last_block_index

    def stop_mining(self):
        self._mining = False

    def mining(self):
        return self._mining
