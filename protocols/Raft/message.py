from enum import Enum


class MessageType(Enum):
    RequestVote = "RequestVote"
    RequestVoteResult = "RequestVoteResult"
    AppendEntries = "AppendEntries"
    AppendEntriesResult = "AppendEntriesResult"


class RequestVoteMessage:
    def __init__(self, node_id, current_term, log_length, last_term):
        self.message_type = MessageType.RequestVote
        self.node_id = node_id
        self.current_term = current_term
        self.log_length = log_length
        self.last_term = last_term
