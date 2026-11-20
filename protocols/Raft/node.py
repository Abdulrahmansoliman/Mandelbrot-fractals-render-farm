import random

from protocols.Raft.message import RequestVoteMessage
from protocols.Raft.storage import RaftStorage


class RaftNode:
    def __init__(self, node_id, database_path):
        self.node_id = node_id
        self.storage = RaftStorage(database_path)

        # These will be saved to SQLite when storage is implemented.
        self.current_term = 0
        self.logs = []
        self.voted_for = None
        self.commit_length = 0

        self.current_role = "Follower"
        self.current_leader = None
        self.votes_received = set()
        self.sent_length = {}
        self.acked_length = {}
        self.timeout = random.randint(1, 15)

    def recover_crash(self):
        self.current_role = "Follower"
        self.current_leader = None
        self.votes_received = set()
        self.sent_length = {}
        self.acked_length = {}

    def suspect(self):
        self.current_term += 1
        self.current_role = "Candidate"
        self.current_leader = None
        self.voted_for = self.node_id
        self.votes_received = {self.node_id}
        self.timeout = random.randint(1, 15)

        last_term = 0

        if self.logs:
            last_term = self.logs[-1][1]

        return RequestVoteMessage(
            self.node_id,
            self.current_term,
            len(self.logs),
            last_term,
        )
