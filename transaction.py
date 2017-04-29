import json


class Transaction(object):
    '''
    A Transaction represents the movimentation of the coins in the network.
    Only one sender is allowed by transaction, but as many as needed receivers
    are allowed. A transaction is only valid if the ammount sent cant be
    verified to be owned by the sender. This process is made by the miners when
    building new blocks and the rest of the network when accepting a new block.

    An special kind of transaction has no sender. This transaction represents
    the coin creation. This transaction can only be made by a miner when
    creating a new block. The ammount of coins allowed in this kind of
    transaction is limited by the nodes in the network when accepting a new
    block.
    '''

    def __init__(self, from_wallet, to_wallets, signature=None):
        '''
        Creates a transaction between two or more wallets.

        from_wallet -- the address of the sender of the money
        to_wallets -- the tuples with addresses of the receivers and ammounts
            received. There is a special to_wallet tuple with a None wallet
            address, this case is the commission to the miner. The commission
            is optional.
        '''
        self._from_wallet = from_wallet
        if not isinstance(to_wallets, list):
            to_wallets = [to_wallets]
        self._to_wallets = to_wallets
        self._signature = signature

    def json(self):
        '''
        Converts the object to a json
        '''
        dictionary = {
            'body': {
                'from': self.from_wallet(),
                'to': self.to_wallets(),
            },
            'signature': self.signature()
        }

        return json.dumps(dictionary)

    def from_wallet(self):
        '''
        Retrieves the sender of the transaction
        '''
        return self._from_wallet

    def to_wallets(self):
        '''
        Retrieves the receivers of the transaction
        '''
        return self._to_wallets

    def is_creation_transaction(self):
        '''
        True if this transaction corresponds to a money creation transaction.
        This kind of transaction has no sender, thus the money is created. The
        receivers of this transaction usually would be the ones responsible
        for the block calculation.
        '''
        return self.from_wallet() is None

    def ammount_spent(self):
        '''
        The ammount spent on this transaction.
        '''
        total_ammount = 0.0
        for _, ammount in self.to_wallets():
            total_ammount += ammount

        return total_ammount

    def prepare_for_signature(self):
        '''
        Obtains only the data of the transaction that should be signed.
        '''
        data = {
            'from': self.from_wallet(),
            'to': self.to_wallets(),
        }

        return json.dumps(data)

    def signed(self, signature):
        '''
        Stores the signature into the transaction. After this the transaction
        is ready for inclusion in the blockchain.
        '''
        self._signature = signature

    def signature(self):
        '''
        Obtains the signature of this transaction
        '''
        return self._signature
