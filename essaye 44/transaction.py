from collections import OrderedDict

from utility.printable import Printable

class Transaction(Printable):
    """Une transaction qui peut être ajoutée à un bloc dans la blockchain.
    Les attributs:

        :sender: L'expéditeur.
        :recipient: Destinateur.
        :signature: La signature de la transaction.
        :amount: Le nombre d'information envoyées.
    """
    def __init__(self, sender, recipient, signature, amount):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.signature = signature

    def to_ordered_dict(self):
        """Convertit cette transaction en un OrderedDict (le hash)."""
        return OrderedDict([('sender', self.sender), ('recipient', self.recipient), ('amount', self.amount)])
