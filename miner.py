import logging
from node import Node
from transaction import Transaction


class Miner(Node):
    """
    This node supports mining. It will register transactions announced and
    will try to include them on new blocks it is mining. When a new block is
    announced it will start mining from that block
    """

    def __init__(self, quantcoin, ip="0.0.0.0", port=65345):
        Node.__init__(self, quantcoin, ip, port)

        self._transaction_queue = []

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
        logging.debug("Transaction received. Adding to the queue.")
        transaction = Transaction()

if __name__ == "__main__":
    print("lallala")
