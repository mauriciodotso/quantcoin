import socket
import thread
import logging
import json
import binascii
import random
import exceptions
from block import Block
from transaction import Transaction


class Node:

    def __init__(self, quantcoin, ip="0.0.0.0", port=65345):
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
            "new_block": self.new_block
        }

    def get_nodes(self, *args, **kwargs):
        logging.debug("Node list requested")
        nodes = self._quantcoin.all_nodes()
        return json.dumps(nodes)

    def get_blocks(self, data, *args, **kwargs):
        logging.debug("Blocks requested (ranged: {})".format('range' in data))
        blocks = []
        if 'range' in data:
            blocks = self._quantcoin.block(data['range'][0], data['range'][1])
        else:
            blocks = self._quantcoin.blocks()

        blocks = [block.json() for block in blocks]
        return json.dumps(blocks)

    def register(self, data, *args, **kwargs):
        logging.debug("Node registering(Node: {})".format(data))
        self._quantcoin.store_node((data['address'], data['port']))

    def new_block(self, data, *args, **kwargs):
        logging.debug("New block announced(block: {})".format(data))
        block = Block.from_json(data)
        assert block.previous() == self._quantcoin.last_block().digest()
        assert block.valid()
        logging.debug("Block accepted")
        self._quantcoin.store_block(block)

    def handle(self, connection, address):
        logging.debug("handling connection(address={})".format(address))
        data = connection.recv(10000)  # FIXME Is this a good size?
        if data is not None:
            try:
                data = json.loads(data)
                response = self._cmds[data['cmd']](data, connection)
                if response is not None:
                    connection.send(response)
            except exceptions.NameError as e:
                logging.debug("An exception occured on connection handle. {}".
                              format(e))

    def run(self):
        logging.debug("Node running(ip={}, port={})".
                      format(self._ip, self._port))
        s = socket.socket()
        s.bind((self._ip, self._port))
        s.listen(5)
        while True:
            connection, address = s.accept()
            thread.start_new_thread(self.handle, (connection, address))


class Network:

    def __init__(self, quantcoin):
        self._quantcoin = quantcoin

    def _send_cmd(self, cmd, receive_function=None):
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
            logging.debug("No nodes registered")

    def register(self, ip, port):
        logging.debug("Sending register command(ip={}, port={})".
                      format(ip, port))
        cmd = {
            'cmd': 'register',
            'address': ip,
            'port': port
        }

        thread.start_new_thread(self._send_cmd, (cmd,))

    def new_block(self, block):
        logging.debug("Sending new block")
        cmd = block.json()
        cmd['cmd'] = 'new_block'

        thread.start_new_thread(self._send_cmd, (cmd,))

    def get_nodes(self, nodes_data_handler):
        logging.debug("Asking for nodes")
        cmd = {
            'cmd': 'get_nodes'
        }

        thread.start_new_thread(self._send_cmd, (cmd, nodes_data_handler))

    def get_blocks(self, blocks_data_handler):
        logging.debug("Asking for all blocks")
        cmd = {
            'cmd': 'get_blocks'
        }

        thread.start_new_thread(self._send_cmd, (cmd, blocks_data_handler))

    def get_range_blocks(self, start, end, blocks_data_handler):
        logging.debug("Asking for a range of blocks(start={}, end={})".
                      format(start, end))
        cmd = {
            'cmd': 'get_blocks',
            'range': [start, end]
        }

        thread.start_new_thread(self._send_cmd, (cmd, blocks_data_handler))
