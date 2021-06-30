from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
import Crypto.Random
import binascii


class Wallet:
    """Crée, charge et détient des clés privées et publiques. Gère la signature et la vérification des transactions."""

    def __init__(self, node_id):
        self.private_key = None
        self.public_key = None
        self.node_id = node_id

    def create_keys(self):
        """Créez une nouvelle paire de clés privées et publiques."""
        private_key, public_key = self.generate_keys()
        self.private_key = private_key
        self.public_key = public_key

    def save_keys(self):
        """Enregistre les clés dans un fichier (wallet.txt)."""
        if self.public_key != None and self.private_key != None:
            try:
                with open('wallet-{}.txt'.format(self.node_id), mode='w') as f:
                    f.write(self.public_key)
                    f.write('\n')
                    f.write(self.private_key)
                return True
            except (IOError, IndexError):
                print('Saving wallet failed...')
                return False

    def load_keys(self):
        """Charge les clés du fichier wallet.txt en mémoire."""
        try:
            with open('wallet-{}.txt'.format(self.node_id), mode='r') as f:
                keys = f.readlines()
                public_key = keys[0][:-1]
                private_key = keys[1]
                self.public_key = public_key
                self.private_key = private_key
            return True
        except (IOError, IndexError):
            print('Loading wallet failed...')
            return False

    def generate_keys(self):
        """Générez une nouvelle paire de clés privée et publique."""
        private_key = RSA.generate(1024, Crypto.Random.new().read)
        public_key = private_key.publickey()
        return (binascii.hexlify(private_key.exportKey(format='DER')).decode('ascii'), binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii'))

    def sign_transaction(self, sender, recipient, amount):
        """ignorer une transaction et retourner la signature.
        
        Arguments:
            :sender: l'expediteur.
            :recipient: destinateur.
            :amount: le nombre se la transaction.
        """
        signer = PKCS1_v1_5.new(RSA.importKey(binascii.unhexlify(self.private_key)))
        h = SHA256.new((str(sender) + str(recipient) + str(amount)).encode('utf8'))
        signature = signer.sign(h)
        return binascii.hexlify(signature).decode('ascii')

    @staticmethod
    def verify_transaction(transaction):
        """Vérifiez la signature d'une transaction.
        Arguments:
            :transaction: La transaction à vérifier.
        """
        public_key = RSA.importKey(binascii.unhexlify(transaction.sender))
        verifier = PKCS1_v1_5.new(public_key)
        h = SHA256.new((str(transaction.sender) + str(transaction.recipient) + str(transaction.amount)).encode('utf8'))
        return verifier.verify(h, binascii.unhexlify(transaction.signature))