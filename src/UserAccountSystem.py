import bcrypt
import random
import json


class UserAccountSystem:

    def __init__(self):
        """
        Initializes the UserAccountSystem class with empty dictionaries/lists.
        """

        # Dictionary to store the username as key and a tuple of hashed password and salt
        self.__AccountLoginInfo = {}

        # Dictionary to store the send token of each user
        self.user_send_token_table = {}

        # Dictionary to store the receive token of each user
        self.user_recv_token_table = {}

        # Dictionary to store the user wallets
        self.__UserWallets = {}

        # List to store banned users
        self.__banned_users = []

    def login(self, username, password):
        """
        Validates the user's login credentials.

        Parameters:
        username (str): Username
        password (str): Password

        Returns:
        bool: True if login is successful, False otherwise.
        """
        # Check if the username exists
        if username in self.__AccountLoginInfo:
            # Retrieve the stored password hash and salt
            stored_password_hash, salt = self.__AccountLoginInfo[username]

            # Hash and salt the input password
            hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)

            # Compare the stored password hash with the hashed input password
            if hashed_password == stored_password_hash:
                return True  # Login successful
        return False  # Login unsuccessful

    def generate_token(self, username):
        """
        Generates a token based on the username.

        Parameters:
        username (str): Username

        Returns:
        str: Generated token
        """
        # Generating a random token based on the username
        return username + str(random.randint(1, 1000))

    def create_user(self, username, password):
        """
        Creates a new user account.

        Parameters:
        username (str): Username
        password (str): Password

        Returns:
        bool: True if the user is created successfully, False otherwise.
        """
        # Check if the username already exists
        if username in self.__AccountLoginInfo:
            return False  # Username already exists, cannot create user

        # Generate a salt for the password
        salt = bcrypt.gensalt()

        # Hash the password with the salt
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)

        # Add the new user to AccountLoginInfo
        self.__AccountLoginInfo[username] = (hashed_password, salt)

        # Generate tokens for sending and receiving
        send_token = self.generate_token(username)
        recv_token = self.generate_token(username)

        # Add the new user to user_send_token_table and user_recv_token_table
        self.user_send_token_table[username] = send_token
        self.user_recv_token_table[username] = recv_token

        return True  # User created successfully

    def user_wallet(self, username, wallet):
        """
        Adds a wallet for a user.

        Parameters:
        username (str): Username
        wallet (Wallet): Wallet object

        Returns:
        bool: True if the wallet is added successfully, False otherwise.
        """
        # Check if the username already has a wallet
        if username in self.__UserWallets:
            return False  # Wallet already exists for this user

        # Add the wallet for the user
        self.__UserWallets[username] = wallet

        return True  # Wallet added successfully

    def ban_user(self, username):
        """
        Bans a user.

        Parameters:
        username (str): Username

        Returns:
        bool: True if the user is banned successfully, False otherwise.
        """
        # Check if the user is already banned
        if username in self.__banned_users:
            return False  # User already banned

        # Add the user to the banned list
        self.__banned_users.append(username)

        return True  # User banned successfully
