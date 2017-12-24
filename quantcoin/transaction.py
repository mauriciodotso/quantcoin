import binascii
import hashlib
import json

from ecdsa import SECP256k1, SigningKey, VerifyingKey


class Transaction(object):
    """
    A Transaction represents the trade of the coins in the network.
    Only one sender is allowed by transaction, but as many as needed receivers
    are allowed. A transaction is only valid if the amount sent cant be
    verified to be owned by the sender. This process is made by the miners when
    building new blocks and the rest of the network when accepting a new block.

    An special kind of transaction has no sender. This transaction represents
    the coin creation. This transaction can only be made by a miner when
    creating a new block. The amount of coins allowed in this kind of
    transaction is limited by the nodes in the network when accepting a new
    block.
    """

    def __init__(self, from_wallet, to_wallets, signature=None, public_key=None):
        """

        :param from_wallet: the address of the sender of the money
        :param to_wallets: the tuples with addresses of the receivers and amounts
                           received. There is a special to_wallet tuple with a None wallet
                           address, this case is the commission to the miner. The commission
                           is optional and must be put as the first on to_wallet list.
        :param signature: The transaction's proof of that it's from the 'from_wallet'.
        :param public_key: The transaction's public key encoded.
        """
        self._from_wallet = from_wallet
        if not isinstance(to_wallets, list):
            to_wallets = [to_wallets]
        self._to_wallets = to_wallets
        self._signature = signature
        self._public_key = public_key

    def json(self):
        """
        Converts the object to a json
        """
        dictionary = {
            'body': {
                'from': self.from_wallet(),
                'to': self.to_wallets(),
            },
            'signature': self.signature(),
            'public_key': self.public_key()
        }

        return dictionary

    def from_wallet(self):
        """
        Retrieves the sender of the transaction
        """
        return self._from_wallet

    def to_wallets(self):
        """
        Retrieves the receivers of the transaction
        """
        return self._to_wallets

    def commission(self):
        """
        :return: The commission value offered by this transaction.
        """
        if self._to_wallets[0][0] is None:
            return self._to_wallets[0][1]
        else:
            return 0.0

    def is_creation_transaction(self):
        """
        True if this transaction corresponds to a money creation transaction.
        This kind of transaction has no sender, thus the money is created. The
        receivers of this transaction usually would be the ones responsible
        for the block calculation.
        """
        return self.from_wallet() is None

    def amount_spent(self):
        """
        The amount spent on this transaction.
        """
        total_amount = 0.0
        for _, amount in self.to_wallets():
            total_amount += amount

        return total_amount

    def prepare_for_signature(self):
        """
        Obtains only the data of the transaction that should be signed.
        """
        data = {
            'from': self.from_wallet(),
            'to': self.to_wallets(),
        }

        return json.dumps(data)

    def sign(self, private_key_encoded, public_key_encoded):
        """
        Does the transaction signature
        :param private_key_encoded: The private key encoded in Base64
        :param public_key_encoded: The public key encoded in Base64
        """
        to_sign = self.prepare_for_signature()
        priv_key = SigningKey.from_string(binascii.a2b_base64(private_key_encoded),
                                          curve=SECP256k1)
        signature = priv_key.sign(to_sign, hashfunc=hashlib.sha256)
        self.signed(binascii.b2a_base64(signature), public_key_encoded)

    def signed(self, signature, public_key):
        """
        Stores the signature into the transaction. After this the transaction
        is ready for inclusion in the blockchain.
        """
        self._signature = signature
        self._public_key = public_key

    def verify(self):
        """
        Verifies the transaction proof of authenticity
        :return: True if the transaction is authentic
        """
        if self._public_key is not None:
            to_verify = self.prepare_for_signature()
            pub_key = VerifyingKey.from_string(binascii.a2b_base64(self._public_key),
                                               curve=SECP256k1)
            return pub_key.verify(signature=binascii.a2b_base64(self.signature()),
                                  data=to_verify,
                                  hashfunc=hashlib.sha256)
        else:
            return False

    def signature(self):
        """
        Obtains the signature of this transaction
        """
        return self._signature

    def public_key(self):
        """
        Obtains the public key of the transaction
        """
        return self._public_key
