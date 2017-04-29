#!/usr/bin/python
import sys
import getopt
import thread
import threading
import time
from cmd import Cmd
from node import Node, Network
from quantcoin import QuantCoin
from block import Block


class Client(Cmd):
    prompt = "[QuantCoin Shell]$ "
    intro = "Wellcome to QuantCoin shell. Type 'help' to get started."

    def __init__(self, quantcoin, ip, port):
        Cmd.__init__(self)
        self._node_data_lock = threading.Lock()
        self._block_data_lock = threading.Lock()

        self._quantcoin = quantcoin
        self._quantcoin.store_node((ip, port))
        node = Node(quantcoin, ip, port)
        thread.start_new_thread(node.run, ())
        self._network = Network(quantcoin)
        thread.start_new_thread(self._update_job, (ip, port))

    def emptyline(self):
        if self.lastcmd:
            self.lastcmd = ""
            return self.onecmd("\n")

    def do_help(self, line):
        print("""
        Wellcome to the QuantCoin client. The commands available are explained
        next.

        \tcreate_wallet <seed?>:
        \t\tCreates a new wallet and saves in the client internal storage. The
        \t\tparameter seed is optional. It's useful for brainwallets if you
        \t\twant that.
        """)

    def _update_job(self, ip, port):
        while True:
            self._network.register(ip, port)
            self.do_update("peers")
            self.do_update("blocks")
            time.sleep(10)

    def do_create_wallet(self, line):
        wallet = QuantCoin.create_wallet()
        self._quantcoin.store_wallet(wallet)
        print(wallet)

    def do_wallets(self, line):
        print(self._quantcoin.wallets())

    def do_exit(self, line):
        print("Bye!")
        self._quantcoin.save(self._quantcoin.database)
        return True

    def do_peers(self, line):
        print(self._quantcoin.all_nodes())

    def do_blocks(self, line):
        print(self._quantcoin.blocks())

    def _nodes_data_handler(self, node_data, socket):
        self._node_data_lock.acquire()
        for node in node_data:
            self._quantcoin.store_node(tuple(node))
        self._node_data_lock.release()

    def _blocks_data_handler(self, block_data, socket):
        self._block_data_lock.acquire()
        for block in block_data:
            self._quantcoin.store_block(Block.from_json(block))
        self._block_data_lock.release()

    def do_update(self, line):
        if line in ("p", "peers"):
            self._network.get_nodes(self._nodes_data_handler)
        if line in ("b", "blocks"):
            self._network.get_blocks(self._blocks_data_handler)


def print_help():
    print("client.py")
    print("\tLaunch the client of the quantcoin network.")
    print("\tOptions:")
    print("\t\t-h(--help)\tShows this help message")
    print("\t\t-m(--mine)\tLaunch the client only for mining")


if __name__ == "__main__":
    import thread

    try:
        application_args = sys.argv[1:]
        opts, _ = getopt.getopt(application_args,
                                "hmi:p:ds:", ["help", "mine", "ip:", "port:",
                                              "debug", "storage:"])
    except getopt.GetoptError:
        print_help()
        exit()

    ip = "0.0.0.0"
    port = 65345
    debug = False
    database = 'default.qc'
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print_help()
            exit()
        elif opt in ("-m", "--mine"):
            # TODO do the mining thing
            print("Mining daemon requested")
            exit()
        elif opt in ('-i', '--ip'):
            ip = arg
        elif opt in ('-p', '--port'):
            port = int(arg)
        elif opt in ('-d', '--debug'):
            debug = True
        elif opt in ('-s', '--storage'):
            database = arg

    if debug:
        import logging
        import sys
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

        channel = logging.StreamHandler(sys.stdout)
        channel.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
                    "[%(levelname)s] %(asctime)s: %(message)s")
        channel.setFormatter(formatter)
        root.addHandler(channel)
    quantcoin = QuantCoin()
    quantcoin.load(database)
    quantcoin.database = database

    client = Client(quantcoin, ip, port)
    client.cmdloop()
