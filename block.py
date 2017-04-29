import json
import hashlib
import binascii


class Block:

    def __init__(self, author, transactions, previous_block, nounce=None,
                 digest=None):
        if author is None:
            raise Exception("A block must have an author.")
        if transactions is None:
            raise Exception("A block should contain at least one transaction.")
        if previous_block is None:
            raise Exception("A block must contain a reference to a " +
                            "previous one.")

        self._author = author
        self._transactions = transactions
        self._previous_block = previous_block
        self._nounce = nounce
        self._digest = digest

    @staticmethod
    def from_json(data):
        transactions = []
        for transaction in data['transactions']:
            transaction_object = Transaction(transaction['body']
                                                        ['from_wallet'],
                                             transaction['body']['to_wallets'],
                                             transaction['signature'])
            transactions.append(transaction_object)

        block = Block(data['author'], transactions,
                      binascii.a2b_base64(data['previous']),
                      binascii.a2b_base64(data['nounce']),
                      binascii.a2b_base64(data['digest']))
        return block

    def transactions(self):
        return sorted(self._transactions,
                      lambda transaction1, transaction2:
                      transaction1.from_wallet() < transaction2.from_wallet())

    def previous(self):
        return self._previous_block

    def transactions_digest(self):
        ordered_transactions = self.transactions()
        queue = []
        for transaction in ordered_transactions:
            queue.append(hashlib.sha256(transaction.json()))

        while len(queue) > 1:
            pair, queue = queue[:2], queue[2:]
            pair_hash = hashlib.sha256(pair[0].digest() + pair[1].digest())
            queue.append(pair_hash)

        return queue[0].digest()

    def proof_of_work(self, difficulty):
        if self._nounce is None:
            zeros = [0 for _ in range(difficulty)]
            transactions_digest = self.transactions_digest()
            nounce = 0
            digest = hashlib.sha256(transactions_digest + str(nounce)).digest()
            while (digest[:difficulty] != bytearray(zeros)):
                nounce = nounce + 1
                digest = hashlib.sha256(transactions_digest +
                                        str(nounce)).digest()

            self._nounce = nounce
            self._digest = digest

    def nounce(self):
        return self._nounce

    def digest(self):
        return self._digest

    def valid(self):
        if self._nounce is not None:
            transactions_digest = self.transactions_digest()
            calculated_digest = hashlib.sha256(transactions_digest +
                                               str(self._nounce)).digest()
            return calculated_digest == self._digest
        else:
            return False

    def author(self):
        return self._author

    def json(self):
        if self.nounce() is not None:
            previous = binascii.b2a_base64(self.previous()) \
                            if self.previous() is not None else None
            dictionary = {
                'author': self.author(),
                'nounce': binascii.b2a_base64(bytes([self.nounce()])),
                'digest': binascii.b2a_base64(self.digest()),
                'previous': previous,
                'transactions': [t.json() for t in self.transactions()]
            }

            return json.dumps(dictionary)
