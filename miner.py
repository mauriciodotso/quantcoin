import logging
import threading
from node import Node
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

    def new_block(self, data, *args, **kwargs):
        """
        Removes transactions already mined from the queue and changes previous block.

        :param data:
        :param args:
        :param kwargs:
        :return:
        """
        Node.new_block(self, data, args, kwargs)

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
        transaction_data = data['transaction']
        transaction = Transaction(from_wallet=transaction_data['body']['from_wallet'],
                                  to_wallets=transaction_data['body']['to_wallets'],
                                  signature=transaction_data['signature'])

        public_key_encoded = self._quantcoin.get_public_key(transaction.from_wallet())
        if public_key_encoded is None:
            logging.debug("Public key isn't known for address {}".format(transaction.from_wallet()))
            # FIXME(mauricio): Try to resolve address?
        else:
            if transaction.verify(public_key_encoded):
                self._transaction_queue_lock.acquire()
                self._transaction_queue.append(transaction)
                self._transaction_queue_lock.release()
