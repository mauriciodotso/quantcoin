#!/usr/bin/python
import sys
import getopt


def print_help():
    print("client.py")
    print("\tLaunch the client of the quantcoin network.")
    print("\tOptions:")
    print("\t\t-h(--help)\tShows this help message")
    print("\t\t-m(--mine)\tLaunch the client only for mining")


if __name__ == "__main__":
    try:
        application_args = sys.argv[1:]
        opts, _ = getopt.getopt(application_args, "hm", ["help", "mine"])
    except getopt.GetoptError:
        print_help()
        sys.exit(1)

    if len(opts) == 0:
        print_help()
        sys.exit(1)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print_help()
            sys.exit(1)
        elif opt in ("-m", "--mine"):
            # TODO do the mining thing
            print("Mining daemon requested")
            sys.exit(1)

    print("Gui client requested")
