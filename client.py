#!/usr/bin/python
import sys
import getopt
from node import Node
from quantcoin import QuantCoin


def print_help():
    print("client.py")
    print("\tLaunch the client of the quantcoin network.")
    print("\tOptions:")
    print("\t\t-h(--help)\tShows this help message")
    print("\t\t-m(--mine)\tLaunch the client only for mining")


if __name__ == "__main__":
    try:
        application_args = sys.argv[1:]
        opts, _ = getopt.getopt(application_args,
                                "hmi:p:d", ["help", "mine", "ip:", "port:",
                                            "debug"])
    except getopt.GetoptError:
        print_help()
        exit()

    ip = "0.0.0.0"
    port = 65345
    debug = False
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
    quantcoin.load()
    node = Node(quantcoin, ip, port)
    node.run()
