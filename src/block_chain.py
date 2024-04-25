# DISCARD

# from datetime import datetime
# from hashlib import sha256
# from json import dumps


# class block:
#     index = 0
#     latest_hash = ""

#     def __init__(self, data: str, previous_hash="") -> None:
#         self.__indexing__ = block.index
#         self.__create_time__ = datetime.now()
#         self.__data__ = data
#         self.__previous_block_hash__ = previous_hash
#         self.__hash_data__ = block.__hash__(self)
#         block.latest_hash = self.__hash_data__
#         block.index += 1

#     def __str__(self) -> str:
#         return dumps(
#             {
#                 "index": self.__indexing__,
#                 "previous": self.__previous_block_hash__,
#                 "create_time": str(self.__create_time__),
#                 "data": self.__data__,
#                 "hash": self.__hash_data__,
#             }
#         )

#     @staticmethod
#     def __hash__(block) -> int:
#         return sha256(
#             (
#                 str(block.__indexing__)
#                 + str(block.__create_time__)
#                 + block.__data__
#                 + block.__previous_block_hash__
#             ).encode()
#         ).hexdigest()

#     @staticmethod
#     def verify(block_to_check, next_block):
#         return block.__hash__(block_to_check) == next_block.__previous_block_hash__

#     @classmethod
#     def get_last_hash():
#         return block.latest_hash

#     def get_last_hash(self):
#         return self.latest_hash


# class chain:

#     def __init__(self, genesis_block_token: str) -> None:
#         self.chain = [
#             block("THE GENSIS BLOCK", sha256(genesis_block_token.encode()).hexdigest())
#         ]
#         self.chain_size = 0

#     def new_block(self, data: str):
#         self.chain.append(block(data, self.get_latest_block().__hash_data__))
#         self.chain_size += 1

#     def get_latest_block(self):
#         return self.chain[-1]

#     def verify_block(self, block: block):
#         return (
#             block.__hash__(self.chain[block.__indexing__])
#             == self.chain[block.__indexing__ + 1].__previous_block_hash__
#         )

#     def view_block(self, index):
#         try:
#             return self.chain[index]
#         except Exception:
#             return "block does not exist"
