import sqlite3


class RaftStorage:
    def __init__(self, database_path):
        self.connection = sqlite3.connect(database_path)

    def close(self):
        self.connection.close()
