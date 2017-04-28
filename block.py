import json
import hashlib
import binascii


class Block:

    def __init__(self, transactions, previous_block, nounce=None, digest=None):
        self._transactions = transactions
        self._previous_block = previous_block
        self._nounce = nounce
        self._digest = digest

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

    def valid_block(self):
        if self._nounce is not None:
            transactions_digest = self.transactions_digest()
            calculated_digest = hashlib.sha256(transactions_digest +
                                               str(self._nounce)).digest()
            return calculated_digest == self._digest

    def json(self):
        if self.nounce() is not None:
            previous = binascii.b2a_base64(self.previous()) \
                            if self.previous() is not None else None
            dictionary = {
                'nounce': binascii.b2a_base64(bytes([self.nounce()])),
                'digest': binascii.b2a_base64(self.digest()),
                'previous': previous,
                'transactions': [t.json() for t in self.transactions()]
            }

            return json.dumps(dictionary)


if __name__ == "__main__":
    from transaction import Transaction
    import random
    import string
    previous_block = None
    for _ in range(100):
        from_address = ''.join([random.choice(string.ascii_letters +
                               string.digits) for _ in range(50)])
        to_address = ''.join([random.choice(string.ascii_letters +
                             string.digits) for _ in range(50)])
        transaction1 = Transaction(from_address,
                                   (to_address, random.choice(range(100))))
        from_address = ''.join([random.choice(string.ascii_letters +
                               string.digits) for _ in range(50)])
        to_address = ''.join([random.choice(string.ascii_letters +
                             string.digits) for _ in range(50)])
        transaction2 = Transaction(from_address,
                                   (to_address, random.choice(range(100))))
        block = Block([transaction1, transaction2], previous_block)
        block.proof_of_work(2)  # 1 byte of difficulty
        print(block.json())
        previous_block = block.digest()
