import json


class Transaction(object):

    def __init__(self, from_wallet, to_wallets):
        '''
        Creates a transaction between two of more wallets.

        from_wallet -- the address of the sender of the money
        to_wallets -- the tuples with addresses of the receivers and ammounts
            received
        '''
        self._from_wallet = from_wallet
        if not isinstance(to_wallets, list):
            to_wallets = [to_wallets]
        self._to_wallets = to_wallets

    def json(self):
        '''
        Converts the object to a json
        '''
        dictionary = {
            'from': self.from_wallet(),
            'to': self.to_wallets(),
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
