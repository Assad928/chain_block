

from utility.hash_util import hash_string_256, hash_block
from wallet import Wallet

class Verification:
    """Une classe d'assistance qui propose diverses méthodes de vérification et de validation statiques et basées sur les classes."""
    @staticmethod
    def valid_proof(transactions, last_hash, proof):
        """Valider un numéro de preuve de travail et voir s'il résout l'algorithme du puzzle (deux 0 en tête)

        Arguments:
            :transactions: Les transactions du bloc pour lequel la preuve est créée.
            :last_hash: Le hachage du bloc précédent qui sera stocké dans le bloc actuel.
            :proof: Le numéro de preuve que nous testons.
        """
        # Créer une chaîne avec toutes les entrées de hachage
        guess = (str([tx.to_ordered_dict() for tx in transactions]) + str(last_hash) + str(proof)).encode()
        # Hash la chaîne
        # Ce n'est PAS le même hachage que celui qui sera stocké dans le précédent_hach. Ce n'est pas un hachage d'un bloc. Il n'est utilisé que pour l'algorithme de preuve de travail.
        guess_hash = hash_string_256(guess)
        # Seul un hachage (basé sur les entrées ci-dessus) qui commence par deux 0 est considéré comme valide
        # Cette condition est bien sûr définie par vous. Vous pourriez également avoir besoin de 10 premiers 0 - cela prendrait beaucoup plus de temps (et cela vous permet de contrôler la vitesse à laquelle de nouveaux blocs peuvent être ajoutés)
        return guess_hash[0:2] == '00'
        
    @classmethod
    def verify_chain(cls, blockchain):
        """ Vérifiez la blockchain actuelle et renvoyez True si elle est valide, False sinon."""
        for (index, block) in enumerate(blockchain):
            if index == 0:
                continue
            if block.previous_hash != hash_block(blockchain[index - 1]):
                return False
            if not cls.valid_proof(block.transactions[:-1], block.previous_hash, block.proof):
                print('Proof of work is invalid')
                return False
        return True

    @staticmethod
    def verify_transaction(transaction, get_balance, check_funds=True):
        """Vérifiez une transaction en vérifiant si l'expéditeur dispose de suffisamment d'informations.

        Arguments:
            :transaction: La transaction à vérifier.
        """
        if check_funds:
            sender_balance = get_balance(transaction.sender)
            return sender_balance >= transaction.amount and Wallet.verify_transaction(transaction)
        else:
            return Wallet.verify_transaction(transaction)

    @classmethod
    def verify_transactions(cls, open_transactions, get_balance):
        """Vérifie toutes les transactions ouvertes."""
        return all([cls.verify_transaction(tx, get_balance, False) for tx in open_transactions])