import hashlib
import json
import time
import heapq
from collections import deque
from typing import Dict, List, Tuple


class Transaction:
    def __init__(self, sender: str, recipient: str, amount: float, fee: float):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.fee = fee

    def to_dict(self) -> Dict:
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "fee": self.fee,
        }

    def __lt__(self, other):
        return self.fee < other.fee


class Block:
    def __init__(
        self,
        index: int,
        transactions: List[Transaction],
        timestamp: float,
        previous_hash: str,
        nonce: int = 0,
    ):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        block_data = {
            "index": self.index,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
        }
        block_string = json.dumps(block_data, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def is_valid(self, blockchain) -> bool:
        # Check if the transactions in the block are valid
        for tx in self.transactions:
            if not blockchain.is_valid_transaction(tx):
                return False
        return True


class Blockchain:
    def __init__(self, mining_difficulty: int = 4):
        self.chain = [self.create_genesis_block()]
        self.transaction_pool: List[Transaction] = []
        self.mining_difficulty = mining_difficulty
        self.nodes: Dict[str, str] = {}  # {node_address: node_public_key}

    def create_genesis_block(self) -> Block:
        return Block(0, [], time.time(), "0")

    def add_transaction(self, transaction: Transaction) -> None:
        self.transaction_pool.append(transaction)
        heapq.heapify(self.transaction_pool)

    def is_valid_transaction(self, transaction: Transaction) -> bool:
        # Check if the sender has enough balance
        sender_balance = self.get_balance(transaction.sender)
        return sender_balance >= (transaction.amount + transaction.fee)

    def get_balance(self, account: str) -> float:
        balance = 0.0
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender == account:
                    balance -= tx.amount + tx.fee
                if tx.recipient == account:
                    balance += tx.amount
        # Include pending transactions from the transaction pool
        for tx in self.transaction_pool:
            if tx.sender == account:
                balance -= tx.amount + tx.fee
            if tx.recipient == account:
                balance += tx.amount
        return balance

    def mine_block(self) -> Block:
        transactions: List[Transaction] = []
        while self.transaction_pool and len(transactions) < 10:
            transactions.append(heapq.heappop(self.transaction_pool))

        latest_block = self.chain[-1]
        new_block = Block(
            index=latest_block.index + 1,
            transactions=transactions,
            timestamp=time.time(),
            previous_hash=latest_block.hash,
        )

        nonce = 0
        while new_block.hash[: self.mining_difficulty] != "0" * self.mining_difficulty:
            new_block.nonce = nonce
            new_block.hash = new_block.compute_hash()
            nonce += 1

        if new_block.is_valid(self):
            self.chain.append(new_block)
            return new_block
        else:
            # Add the transactions back to the pool
            self.transaction_pool.extend(transactions)
            heapq.heapify(self.transaction_pool)
            return None

    def register_node(self, address: str, public_key: str) -> None:
        self.nodes[address] = public_key

    def resolve_conflicts(self) -> bool:
        """
        Consensus algorithm to resolve conflicts between nodes in the network.
        Returns True if the chain was replaced, False otherwise.
        """
        longest_chain = self.chain
        max_length = len(self.chain)

        for node_address, node_public_key in self.nodes.items():
            response = self.request_chain(node_address)
            if (
                response
                and len(response) > max_length
                and self.is_valid_chain(response)
            ):
                longest_chain = response
                max_length = len(response)

        if longest_chain != self.chain:
            self.chain = longest_chain
            return True
        return False

    def request_chain(self, node_address: str) -> List[Block]:
        # Implement the logic to request the blockchain from a given node
        pass

    def is_valid_chain(self, chain: List[Block]) -> bool:
        if chain[0].index != 0 or chain[0].previous_hash != "0":
            return False

        for i in range(1, len(chain)):
            block = chain[i]
            prev_block = chain[i - 1]
            if block.previous_hash != prev_block.hash or not block.is_valid(self):
                return False

        return True

    def get_latest_block_hash(self) -> str:
        """
        Get the hash of the latest block in the blockchain.
        """
        if self.chain:
            return self.chain[-1].hash
        else:
            return None
