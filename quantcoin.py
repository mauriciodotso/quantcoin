import logging
import string
import random
import json
from block import Block
import os
import binascii
import hashlib
from Crypto.Cipher import AES
from Crypto import Random


class QuantCoin:

    def __init__(self):
        self._blocks = []
        self._peers = []
        self._wallets = []

    def load(self, database):
        logging.debug("Loading from database")
        if os.path.exists(database):
            with open(database, 'rb') as fp:
                storage = json.load(fp)
                blocks = storage['blocks']
                self._blocks = [Block.from_json(block) for block in blocks]
                self._peers = [tuple(peer) for peer in storage['peers']]
        else:
            logging.debug("Requested database does not exists(database={})".
                          format(database))
            return False

    def save(self, database):
        logging.debug("Saving to database")
        with open(database, 'wb') as fp:
            json_blocks = [block.json() for block in self._blocks]
            storage = {
                'blocks': json_blocks,
                'peers': self._peers,
                }
            json.dump(storage, fp)

    def load_private(self, database, password):
        logging.debug("Loading from private database")
        if os.path.exists(database):
            with open(database, 'rb') as fp:
                with open(database + '.iv') as fpiv:
                    iv = fpiv.read()
                aes = AES.new(hashlib.sha256(password).digest(),
                              AES.MODE_CBC, iv)
                storage_json = self.__unpad(aes.decrypt(fp.read()))
                try:
                    self._wallets = json.loads(storage_json)['wallets']
                except Exception:
                    print("Your password is problably wrong!")
                    exit()
        else:
            logging.debug("Requested private database " +
                          "does not exists(database={})".format(database))
            return False

    def save_private(self, database, password):
        logging.debug("Saving to private database")
        with open(database, 'wb') as fp:
            storage = {
                'wallets': self._wallets
            }
            storage_json = json.dumps(storage)
            iv = Random.new().read(AES.block_size)
            with open(database + ".iv", 'wb') as fpiv:
                fpiv.write(iv)
            aes = AES.new(hashlib.sha256(password).digest(), AES.MODE_CBC, iv)
            encrypted_storage = aes.encrypt(self.__pad(storage_json))
            fp.write(encrypted_storage)

    def __pad(self, m):
        return m + (16 - len(m) % 16) * chr(16 - len(m) % 16)

    def __unpad(self, m):
        return m[0:-ord(m[-1])]

    def all_nodes(self):
        logging.debug("All nodes requested")
        return self._peers

    def blocks(self):
        logging.debug("All blocks requested")
        return self._blocks

    def block(self, start, end):
        logging.debug("Block range requested(from={},to={})".
                      format(start, end))
        return self._blocks[start:end]

    def wallets(self):
        return self._wallets

    def store_wallet(self, wallet):
        if wallet not in self._wallets:
            self._wallets.append(wallet)

    def store_block(self, block):
        if block not in self._blocks:
            self._blocks.append(block)

    def store_node(self, node):
        if node not in self._peers:
            self._peers.append(node)

    @staticmethod
    def create_wallet(seed=None):
        from ecdsa import SigningKey, SECP256k1
        from ecdsa.util import randrange_from_seed__trytryagain
        logging.debug("Creating wallet(seed={})".format(seed))
        if seed is None:
            seed = ''.join([random.SystemRandom().
                            choice(string.ascii_letters + string.digits)
                            for _ in range(50)])
        seed = int(hashlib.sha256(seed).hexdigest(), 16)
        secret_exponent = randrange_from_seed__trytryagain(seed,
                                                           SECP256k1.order)
        private_key = SigningKey.from_secret_exponent(secret_exponent,
                                                      curve=SECP256k1)
        public_key = private_key.get_verifying_key()
        address = 'QC' + hashlib.sha1(public_key.to_string()).hexdigest()
        wallet = {
            'private_key': binascii.b2a_base64(private_key.to_string()),
            'public_key': binascii.b2a_base64(public_key.to_string()),
            'address': address
        }
        return wallet
