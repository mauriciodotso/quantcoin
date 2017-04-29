#!/usr/bin/python
import sys
import getopt
import thread
import threading
import time
import hashlib
import binascii
from cmd import Cmd
from node import Node, Network
from quantcoin import QuantCoin
from block import Block
from transaction import Transaction
from ecdsa import SigningKey, SECP256k1


class Client(Cmd):
    '''
    A Shell client to the QuantCoin network. This shell is a full client to the
    QuantCoin network capable of doing all the operations necessary to manage
    the coins of a wallet in the network.
    '''
    prompt = "[QuantCoin Shell]$ "
    intro = "Wellcome to QuantCoin shell. Type 'help' to get started."

    def __init__(self, quantcoin, ip, port):
        '''
        Instantiates the Client Shell and setups the Node and the Network
        interface. The ip and port parameter will be used to register this
        in the QuantCoin network, so they should be visible in the external
        network.

            quantcoin: The QuanCoin storages facade.
            ip: This client public IP address.
            port: The port that this client will operate.
        '''
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
        '''
        Avoids executing the previous command if an emptyline is given to this
        shell.
        '''
        if self.lastcmd:
            self.lastcmd = ""
            return self.onecmd("\n")

    def do_help(self, line):
        '''
        Shows the help to the user.
        '''
        print("""
        Wellcome to the QuantCoin client. The commands available are explained
        next.

        \tcreate_wallet <seed?>:
        \t\tCreates a new wallet and saves in the client internal storage. The
        \t\tparameter seed is optional. It's useful for brainwallets if you
        \t\twant that.
        """)

    def _update_job(self, ip, port):
        '''
        Executes indefinetly the syncing of the public storage of the
        QuantCoin network.

            ip: This client public IP address.
            port: The port that this client will operate.
        '''
        while True:
            self._network.register(ip, port)
            self.do_update("peers")
            self.do_update("blocks")
            time.sleep(10)

    def do_create_wallet(self, line):
        '''
        Register a new wallet in this client. The wallet can be created at
        random of from a seed.
        '''
        line = line.strip()
        if line == '':
            line = None
        wallet = QuantCoin.create_wallet(line)
        self._quantcoin.store_wallet(wallet)
        print(wallet)

    def do_wallets(self, line):
        '''
        Shows the user all wallets owned by this client.
        '''
        print(self._quantcoin.wallets())

    def do_exit(self, line):
        '''
        Saves the public and private store and terminantes this shell.
        '''
        print("Bye!")
        self._quantcoin.save(self._quantcoin.database)
        self._quantcoin.save_private(self._quantcoin.private_database,
                                     self._quantcoin.password)
        return True

    def do_peers(self, line):
        '''
        Shows the user all peers known by this client.
        '''
        print(self._quantcoin.all_nodes())

    def do_blocks(self, line):
        '''
        Shows the user the actual known blockchain.
        '''
        print(self._quantcoin.blocks())

    def _nodes_data_handler(self, node_data, socket):
        '''
        Handles the node data received from the network.
        '''
        self._node_data_lock.acquire()
        for node in node_data:
            self._quantcoin.store_node(tuple(node))
        self._node_data_lock.release()

    def _blocks_data_handler(self, block_data, socket):
        '''
        Handles the block data received from the network.
        '''
        self._block_data_lock.acquire()
        for block in block_data:
            self._quantcoin.store_block(Block.from_json(block))
        self._block_data_lock.release()

    def do_update(self, line):
        '''
        Manually updates the public storage.
        '''
        if line in ("p", "peers"):
            self._network.get_nodes(self._nodes_data_handler)
        if line in ("b", "blocks"):
            self._network.get_blocks(self._blocks_data_handler)

    def do_send(self, line):
        '''
        Creates a transaction.
        '''
        params = line.strip().split()
        if len(params) < 3:
            print("Missing parameters")
            return False
        if len(params[2:]) % 2 != 0:
            print("Parameters syntax wrong")
            return False

        transaction_base_args, params = params[:2], params[2:]
        my_address, commission = transaction_base_args
        to_wallets = [(None, commission)]
        while len(params) > 0:
            address, amount = params[:2]
            params = params[2:]
            to_wallets.append((address, amount))

        transaction = Transaction(my_address, to_wallets)
        to_sign = transaction.prepare_for_signature()
        using_wallet = None
        for wallet in self._quantcoin.wallets():
            if wallet['address'] == my_address:
                using_wallet = wallet
                break

        if using_wallet is None:
            print("You do not own a wallet with the address {}".
                  format(my_address))
            return False

        priv_key = SigningKey.from_string(binascii.a2b_base64(
                                          using_wallet['private_key']),
                                          curve=SECP256k1)
        signature = priv_key.sign(to_sign, hashfunc=hashlib.sha256)
        transaction.signed(binascii.b2a_base64(signature))
        self._network.send(transaction.json())


def print_help():
    '''
    Shows the help to the shell options.
    '''
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
    private_database = 'default.qc-priv'
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
    password = raw_input("Password: ")
    quantcoin.load_private(private_database, password)
    quantcoin.private_database = private_database
    quantcoin.password = password

    client = Client(quantcoin, ip, port)
    client.cmdloop()
