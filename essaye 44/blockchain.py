from functools import reduce
import hashlib as hl

import json
import pickle
import requests


from utility.hash_util import hash_block
from utility.verification import Verification
from block import Block
from transaction import Transaction
from wallet import Wallet


MINING_REWARD = 10

print(__name__)


class Blockchain:
    """La classe Blockchain gère la chaîne de blocs ainsi que les transactions ouvertes et le nœud sur lequel elle s'exécute.
    Les attributs:
        :chain: La liste des blocs
        :open_transactions (privée): La liste des transactions ouvertes
        :hosting_node: Le nœud connecté (qui exécute la blockchain).
    """

    def __init__(self, public_key, node_id):
        """Le constructeur de la classe Blockchain."""
        # Notre bloc de départ pour la blockchain
        genesis_block = Block(0, '', [], 100, 0)
        # Initialiser notre liste (vide) de blockchain
        self.chain = [genesis_block]
        #Transactions non gérées
        self.__open_transactions = []
        self.public_key = public_key
        self.__peer_nodes = set()
        self.node_id = node_id
        self.resolve_conflicts = False
        self.load_data()

    
    @property
    def chain(self):
        return self.__chain[:]

    
    @chain.setter
    def chain(self, val):
        self.__chain = val

    def get_open_transactions(self):
        """Renvoie une copie de la liste des transactions ouvertes."""
        return self.__open_transactions[:]

    def load_data(self):
        """Initialiser la blockchain + ouvrir les données de transactions à partir d'un fichier."""
        try:
            with open('blockchain-{}.txt'.format(self.node_id), mode='r') as f:
                # file_content = pickle.loads(f.read())
                file_content = f.readlines()
                # blockchain = file_content['chain']
                # open_transactions = file_content['ot']
                blockchain = json.loads(file_content[0][:-1])
                # Nous devons convertir les données chargées car les transactions doivent utiliser OrderedDict
                updated_blockchain = []
                for block in blockchain:
                    converted_tx = [Transaction(
                        tx['sender'], tx['recipient'], tx['signature'], tx['amount']) for tx in block['transactions']]
                    updated_block = Block(
                        block['index'], block['previous_hash'], converted_tx, block['proof'], block['timestamp'])
                    updated_blockchain.append(updated_block)
                self.chain = updated_blockchain
                open_transactions = json.loads(file_content[1][:-1])
                
                updated_transactions = []
                for tx in open_transactions:
                    updated_transaction = Transaction(
                        tx['sender'], tx['recipient'], tx['signature'], tx['amount'])
                    updated_transactions.append(updated_transaction)
                self.__open_transactions = updated_transactions
                peer_nodes = json.loads(file_content[2])
                self.__peer_nodes = set(peer_nodes)
        except (IOError, IndexError):
            pass
        finally:
            print('Cleanup!')

    def save_data(self):
        
        try:
            with open('blockchain-{}.txt'.format(self.node_id), mode='w') as f:
                saveable_chain = [block.__dict__ for block in [Block(block_el.index, block_el.previous_hash, [
                    tx.__dict__ for tx in block_el.transactions], block_el.proof, block_el.timestamp) for block_el in self.__chain]]
                f.write(json.dumps(saveable_chain))
                f.write('\n')
                saveable_tx = [tx.__dict__ for tx in self.__open_transactions]
                f.write(json.dumps(saveable_tx))
                f.write('\n')
                f.write(json.dumps(list(self.__peer_nodes)))
                # save_data = {
                #     'chain': blockchain,
                #     'ot': open_transactions
                # }
                # f.write(pickle.dumps(save_data))
        except IOError:
            print('Saving failed!')

    def proof_of_work(self):
        """Générez une preuve de travail pour les transactions ouvertes, le hachage du bloc précédent et un nombre aléatoire (qui est deviné jusqu'à ce qu'il rentre)."""
        last_block = self.__chain[-1]
        last_hash = hash_block(last_block)
        proof = 0
        # Essayez différents numéros PoW et renvoyez le premier valide
        while not Verification.valid_proof(self.__open_transactions, last_hash, proof):
            proof += 1
        return proof

    def get_balance(self, sender=None):
        """Calculez et retournez le solde d'un participant
        """
        if sender == None:
            if self.public_key == None:
                return None
            participant = self.public_key
        else:
            participant = sender
        # Récupérer une liste de tous les montants de pièces envoyés pour la personne donnée (des listes vides sont retournées si la personne n'était PAS l'expéditeur)
        # Cela récupère les quantités envoyées de transactions qui étaient déjà incluses dans les blocs de la blockchain
        tx_sender = [[tx.amount for tx in block.transactions
                      if tx.sender == participant] for block in self.__chain]
        # Récupérer une liste de tous les montants de pièces envoyés pour la personne donnée (des listes vides sont retournées si la personne n'était PAS l'expéditeur)
        # Cela récupère les quantités envoyées de transactions ouvertes (pour éviter de doubler les dépenses)
        open_tx_sender = [tx.amount
                          for tx in self.__open_transactions if tx.sender == participant]
        tx_sender.append(open_tx_sender)
        print(tx_sender)
        amount_sent = reduce(lambda tx_sum, tx_amt: tx_sum + sum(tx_amt)
                             if len(tx_amt) > 0 else tx_sum + 0, tx_sender, 0)
        # Ces récupérations ont reçu des montants en pièces de transactions qui étaient déjà inclus dans des blocs de la blockchain
        # Nous ignorons les transactions ouvertes ici car vous ne devriez pas pouvoir dépenser de pièces avant que la transaction ne soit confirmée + incluse dans un bloc
        tx_recipient = [[tx.amount for tx in block.transactions
                         if tx.recipient == participant] for block in self.__chain]
        amount_received = reduce(lambda tx_sum, tx_amt: tx_sum + sum(tx_amt)
                                 if len(tx_amt) > 0 else tx_sum + 0, tx_recipient, 0)
         #Retourner le total
        return amount_received - amount_sent

    def get_last_blockchain_value(self):
        """ retourne la derniere valeur de notre blockchain. """
        if len(self.__chain) < 1:
            return None
        return self.__chain[-1]

    # Cette fonction accepte deux arguments.
    # Un requis (transaction_amount) et un facultatif (last_transaction)
    # Celui en option est facultatif car il a une valeur par défaut => [1]

    def add_transaction(self, recipient, sender, signature, amount=1.0, is_receiving=False):
        """ Ajoutez une nouvelle valeur ainsi que la dernière valeur de blockchain à la blockchain.

        Arguments:
            :sender: L'expéditeur de l'information.
            :recipient: Le destinataire de l'information.
            :amount: Le nombre d'information envoyées avec la transaction (par défaut = 1.0)
        """
        # transaction = {
        #     'sender': sender,
        #     'recipient': recipient,
        #     'amount': amount
        # }
        # if self.public_key == None:
        #     return False
        transaction = Transaction(sender, recipient, signature, amount)
        if Verification.verify_transaction(transaction, self.get_balance):
            self.__open_transactions.append(transaction)
            self.save_data()
            if not is_receiving:
                for node in self.__peer_nodes:
                    url = 'http://{}/broadcast-transaction'.format(node)
                    try:
                        response = requests.post(url, json={
                                                 'sender': sender, 'recipient': recipient, 'amount': amount, 'signature': signature})
                        if response.status_code == 400 or response.status_code == 500:
                            print('Transaction declined, needs resolving')
                            return False
                    except requests.exceptions.ConnectionError:
                        continue
            return True
        return False

    def mine_block(self):
        """Créez un nouveau bloc et ajoutez-lui des transactions ouvertes."""
        #Récupérer le dernier bloc actuellement de la blockchain
        if self.public_key == None:
            return None
        last_block = self.__chain[-1]
        # Hachage du dernier bloc (=> pour pouvoir le comparer à la valeur de hachage stockée)
        hashed_block = hash_block(last_block)
        proof = self.proof_of_work()
        
        # reward_transaction = {
        #     'sender': 'MINING',
        #     'recipient': owner,
        #     'amount': MINING_REWARD
        # }
        reward_transaction = Transaction(
            'MINING', self.public_key, '', MINING_REWARD)
         #Copiez la transaction au lieu de manipuler la liste d'origine open_transactions
         #Cela garantit que si, pour une raison quelconque, l'extraction échoue, nous n'avons pas la transaction de récompense stockée dans les transactions ouvertes
        copied_transactions = self.__open_transactions[:]
        for tx in copied_transactions:
            if not Wallet.verify_transaction(tx):
                return None
        copied_transactions.append(reward_transaction)
        block = Block(len(self.__chain), hashed_block,
                      copied_transactions, proof)
        self.__chain.append(block)
        self.__open_transactions = []
        self.save_data()
        for node in self.__peer_nodes:
            url = 'http://{}/broadcast-block'.format(node)
            converted_block = block.__dict__.copy()
            converted_block['transactions'] = [
                tx.__dict__ for tx in converted_block['transactions']]
            try:
                response = requests.post(url, json={'block': converted_block})
                if response.status_code == 400 or response.status_code == 500:
                    print('Block declined, needs resolving')
                if response.status_code == 409:
                    self.resolve_conflicts = True
            except requests.exceptions.ConnectionError:
                continue
        return block

    def add_block(self, block):
        """Ajoutez un bloc qui a été reçu via la diffusion à la blockchain locale."""
        # Créer une liste d'objets de transaction
        transactions = [Transaction(
            tx['sender'], tx['recipient'], tx['signature'], tx['amount']) for tx in block['transactions']]
        #  Valider la preuve de travail du bloc et stocker le résultat (Vrai ou Faux) dans une variable
        proof_is_valid = Verification.valid_proof(
            transactions[:-1], block['previous_hash'], block['proof'])
        # Vérifiez si previous_hash stocké dans le bloc est égal au hachage du dernier bloc de la blockchain locale et stockez le résultat dans un bloc
        hashes_match = hash_block(self.chain[-1]) == block['previous_hash']
        if not proof_is_valid or not hashes_match:
            return False
       # Créer un objet Block
        converted_block = Block(
            block['index'], block['previous_hash'], transactions, block['proof'], block['timestamp'])
        self.__chain.append(converted_block)
        stored_transactions = self.__open_transactions[:]
        # Vérifiez quelles transactions ouvertes ont été incluses dans le bloc reçu et supprimez-les
        # Cela pourrait être amélioré en attribuant à chaque transaction un identifiant qui l'identifierait de manière unique.
        for itx in block['transactions']:
            for opentx in stored_transactions:
                if opentx.sender == itx['sender'] and opentx.recipient == itx['recipient'] and opentx.amount == itx['amount'] and opentx.signature == itx['signature']:
                    try:
                        self.__open_transactions.remove(opentx)
                    except ValueError:
                        print('Item was already removed')
        self.save_data()
        return True

    def resolve(self):
        """Vérifie toutes les chaînes de blocs des nœuds homologues et remplace celle locale par des chaînes valides plus longues."""
        # Initialiser la chaîne gagnante avec la chaîne locale
        winner_chain = self.chain
        replace = False
        for node in self.__peer_nodes:
            url = 'http://{}/chain'.format(node)
            try:
                # Envoyer une demande et stocker la réponse
                response = requests.get(url)
                # Récupérer les données JSON sous forme de dictionnaire
                node_chain = response.json()
                # Convertir la liste des dictionnaires en une liste d'objets de bloc ET de transaction
                node_chain = [Block(block['index'], block['previous_hash'], [Transaction(
                    tx['sender'], tx['recipient'], tx['signature'], tx['amount']) for tx in block['transactions']],
                                    block['proof'], block['timestamp']) for block in node_chain]
                node_chain_length = len(node_chain)
                local_chain_length = len(winner_chain)
                # Stockez la chaîne reçue comme chaîne gagnante actuelle si elle est plus longue ET valide
                if node_chain_length > local_chain_length and Verification.verify_chain(node_chain):
                    winner_chain = node_chain
                    replace = True
            except requests.exceptions.ConnectionError:
                continue
        self.resolve_conflicts = False
        
        self.chain = winner_chain
        if replace:
            self.__open_transactions = []
        self.save_data()
        return replace

    def add_peer_node(self, node):
        """Ajoute un nouveau nœud à l'ensemble de nœuds homologues.

        Arguments:
            :node: L'URL du nœud à ajouter.
        """
        self.__peer_nodes.add(node)
        self.save_data()

    def remove_peer_node(self, node):
        """Supprime un nœud de l'ensemble de nœuds homologues.

        Arguments:
            :node: L'URL du nœud à supprimer.
        """
        self.__peer_nodes.discard(node)
        self.save_data()

    def get_peer_nodes(self):
        """Renvoie une liste de tous les nœuds homologues connectés."""
        return list(self.__peer_nodes)
