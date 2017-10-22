import binascii
import exceptions
import hashlib
import json
import logging
import random
import socket
import thread

from ecdsa import SECP256k1, VerifyingKey

from block import Block


class Node:
    """
    A Node in the network communicate with others sharing the public store.
    Most of the commands handled by a node have to do with the maintenance of
    a synced public store.
    """

    def __init__(self, quantcoin, ip="0.0.0.0", port=65345):
        """
        Instantiates a node to handle network requests.
        """
        logging.debug("Creating Node: ip={}, port={}".format(ip, port))
        if quantcoin is None:
            raise Exception("A QuantCoin instance is necessary " +
                            "for node operation")
        self._ip = ip
        self._port = port
        self._quantcoin = quantcoin
        self._cmds = {
            "get_nodes": self.get_nodes,
            "get_blocks": self.get_blocks,
            "register": self.register,
            "new_block": self.new_block,
            "send": self.send
        }
        self._running = False

    def get_nodes(self, *args, **kwargs):
        """
        Responds to the command with all peers known by this node.
        """
        logging.debug("Node list requested")
        nodes = self._quantcoin.all_nodes()
        return json.dumps(nodes)

    def get_blocks(self, data, *args, **kwargs):
        """
        Responds to the command with all blocks, or if a range was requested,
        with that range.
        """
        logging.debug("Blocks requested (ranged: {})".format('range' in data))
        blocks = []
        if 'range' in data:
            blocks = self._quantcoin.block(data['range'][0], data['range'][1])
        else:
            blocks = self._quantcoin.blocks()

        blocks = [block.json() for block in blocks]
        return json.dumps(blocks)

    def register(self, data, *args, **kwargs):
        """
        Store a peer that is announcing itself in the network.
        """
        logging.debug("Node registering(Node: {})".format(data))
        self._quantcoin.store_node((data['address'], data['port']))

    def new_block(self, data, *args, **kwargs):
        """
        Verifies and store if valid the new block announced in the network.
        """
        logging.debug("New block announced(block: {})".format(data))
        block = Block.from_json(data)
        assert block.previous() == self._quantcoin.last_block().digest()
        assert block.valid()

        for transaction in block.transactions():
            # If the transaction is the creation transaction we do not validate
            if transaction.from_wallet() is not None:
                assert transaction.amount_spent() <= \
                       self._quantcoin.amount_owned(transaction.from_wallet())

                # An address cannot send money to itself
                for to_address, _ in transaction.to_wallets():
                    assert to_address != transaction.from_wallet()

                transaction_public_key = None
                for address, public_key in self._quantcoin.public_wallets():
                    if address == transaction.from_wallet():
                        transaction_public_key = public_key
                        break

                pub_key = VerifyingKey.from_string(
                    binascii.a2b_base64(transaction_public_key),
                    curve=SECP256k1)

                assert pub_key.verify(transaction.signature(),
                                      transaction.prepare_for_signature(),
                                      hashfunc=hashlib.sha256)

        logging.debug("Block accepted")
        self._quantcoin.store_block(block)

    def send(self, data, *args, **kwargs):
        """
        Ignores the transaction announcement in the network.
        """
        logging.debug("Transaction received({})".format(data['transaction']))
        pass

    def handle(self, connection, address):
        """
        Handles a command received from another node calling the proper
        function.
        """
        logging.debug("handling connection(address={})".format(address))
        data = connection.recv(10000)  # FIXME Is this a good size?
        if data is not None:
            try:
                data = json.loads(data)
                response = self._cmds[data['cmd']](data, connection)
                if response is not None:
                    connection.send(response)
            except exceptions.NameError as e:
                logging.debug("An exception occurred on connection handle. {}".
                              format(e))

    def run(self):
        """
        Awaits and handles commands indefinitely.
        """
        logging.debug("Node running(ip={}, port={})".
                      format(self._ip, self._port))
        s = socket.socket()
        s.bind((self._ip, self._port))
        s.listen(5)
        self._running = True
        while self._running:
            connection, address = s.accept()
            thread.start_new_thread(self.handle, (connection, address))

    def stop(self):
        """
        Stops the node
        """
        self._running = False


class Network:
    """
    A Network instance is capable of sending commands to other peers in the
    network.
    """

    def __init__(self, quantcoin):
        """
        Instantiates a Network. A QuantCoin instance is mandatory.
        """
        if quantcoin is None:
            raise Exception("A Network must have a QuanCoin instance to work.")
        self._quantcoin = quantcoin

    def _send_cmd(self, cmd, receive_function=None):
        """
        Sends the command to all peers known in the network. If the peer
        respond, the data is passed trough the callback receive_function if it
        was provided.

        :param cmd: the command to be sent to the network.
        :param receive_function: the callback function if data is produced by the
                it will be called from different threads.
                execution of the command. This function must be thread safe as
        """
        cmd_string = json.dumps(cmd)
        nodes = self._quantcoin.all_nodes()
        if nodes is not None:
            nodes = random.sample(nodes, len(nodes))
            for node in nodes:
                s = socket.socket()
                try:
                    s.connect(node)
                except Exception:
                    s.close()
                    continue

                s.send(cmd_string)
                if receive_function is not None:
                    data = s.recv(10000)
                    data = json.loads(data)
                    receive_function(data, s)
        else:
            logging.warn("No nodes registered. Cmd: {}".format(cmd))

    def register(self, ip, port):
        """
        Sends a register command to the network.

        :param ip: IP address of this node.
        :param port: The port that this node is operating.
        """
        logging.debug("Sending register command(ip={}, port={})".
                      format(ip, port))
        cmd = {
            'cmd': 'register',
            'address': ip,
            'port': port
        }

        thread.start_new_thread(self._send_cmd, (cmd,))

    def new_block(self, block):
        """
        Sends a new_block command to the network.

        :param block: The block to be added to the blockchain.
        """
        logging.debug("Sending new block")
        block_json = block.json()
        cmd = {
            'cmd': 'new_block',
            'block': block_json
        }

        thread.start_new_thread(self._send_cmd, (cmd,))

    def get_nodes(self, nodes_data_handler):
        """
        Asks for peers known in the network. The peer data will be retrieved
        through the nodes_data_handler callback.

        :param nodes_data_handler: The callback used to receive the node data.
        """
        logging.debug("Asking for nodes")
        cmd = {
            'cmd': 'get_nodes'
        }

        thread.start_new_thread(self._send_cmd, (cmd, nodes_data_handler))

    def get_blocks(self, blocks_data_handler):
        """
        Asks for the full blockchain. The blockchain will be received trough
        the blocks_data_handler callback.

        :param blocks_data_handler: The callback used to receive the full
                                    blockchain.
        """
        logging.debug("Asking for all blocks")
        cmd = {
            'cmd': 'get_blocks'
        }

        thread.start_new_thread(self._send_cmd, (cmd, blocks_data_handler))

    def get_range_blocks(self, start, end, blocks_data_handler):
        """
        Asks for a slice of the blockchain. The slice will be received trough
        the blocks_data_handler callback.

        :param blocks_data_handler: The callback used to receive the slice of the
                                    blockchain.
        """
        logging.debug("Asking for a range of blocks(start={}, end={})".
                      format(start, end))
        cmd = {
            'cmd': 'get_blocks',
            'range': [start, end]
        }

        thread.start_new_thread(self._send_cmd, (cmd, blocks_data_handler))

    def send(self, transaction):
        """
        Announces to the network a transaction.
        """
        logging.debug("Sending: {}".format(transaction.json()))
        cmd = {
            'cmd': 'send',
            'transaction': transaction.json()
        }

        thread.start_new_thread(self._send_cmd, (cmd,))
