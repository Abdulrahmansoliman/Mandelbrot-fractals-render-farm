from pathlib import Path
from tempfile import TemporaryDirectory

from protocols.Raft.message import MessageType
from protocols.Raft.node import RaftNode


with TemporaryDirectory() as directory:
    database_path = Path(directory) / "node_1.sqlite"
    node = RaftNode("node_1", database_path)
    try:
        assert database_path.is_file()
        assert node.storage.connection.execute("SELECT 1").fetchone() == (1,)
        node.current_leader = "node_2"
        node.votes_received = {"node_2", "node_3"}

        first_request = node.suspect()

        assert node.current_role == "Candidate"
        assert node.current_leader is None
        assert node.current_term == 1
        assert node.voted_for == "node_1"
        assert node.votes_received == {"node_1"}
        assert first_request.message_type == MessageType.RequestVote
        assert first_request.node_id == "node_1"
        assert first_request.current_term == 1
        assert first_request.log_length == 0
        assert first_request.last_term == 0

        node.current_term = 4
        node.logs = [("first command", 1), ("second command", 3)]
        node.commit_length = 1
        node.votes_received.add("node_2")

        second_request = node.suspect()

        assert node.current_term == second_request.current_term == 5
        assert node.votes_received == {"node_1"}
        assert second_request.log_length == 2
        assert second_request.last_term == 3
        assert node.logs == [("first command", 1), ("second command", 3)]
        assert node.commit_length == 1
        assert first_request.current_term == 1
    finally:
        node.storage.close()

print("All Raft election-start tests passed!")
