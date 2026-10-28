from collections import deque
class Task:
    
    def __init__(self, max_attempts):
        self.pending = deque()
        self.tasks = {}
        self.max_attempts = max_attempts
        self.dead = []
    
    def add_task(self, tasks):
        
        for task in tasks:
            task_id = task["task_id"]
            
            if task_id in self.tasks:
                raise ValueError("This task is already there in the system")

            self.tasks[task_id] = {
                "task": task,
                "status": "PENDING",
                "worker_id": None,
                "attempts": 0,
                "result": None
            }

            self.pending.append(task_id)
    
    def peek_task(self):
        if not self.pending:
            raise ValueError("Task queue is empty")
        
        task_id = self.pending[0]
        
        # I am returning the tile information, I won't remove the task
        # from the queue, i will do so when successfult assigned by the coordinator 
        # in Raft
        return self.tasks[task_id]["task"]
    
    
    def assign_task(self, worker_id):
        if not self.pending:
            raise ValueError("Task queue is empty")
        
        task_id = self.pending.popleft()  
        
        self.tasks[task_id]["status"] = "RUNNING"
        self.tasks[task_id]["attempts"] += 1
        self.tasks[task_id]["worker_id"] = worker_id
        
        return self.tasks[task_id]["task"]
    
    def fail_task(self, task_id):
        if task_id not in self.tasks:
            raise ValueError("Task ins't in the system")
                
        if self.tasks[task_id]["status"] != "RUNNING":
            raise ValueError("Task isn't in running tasks, it's either finished or pending")
                
        if self.tasks[task_id]["attempts"]< self.max_attempts:
            return False
        
        self.dead.append(task_id)
        self.tasks[task_id]["status"] = "FAILED"
        self.tasks[task_id]["worker_id"] = None
        return True
    
    def complete_task(self, task_id, worker_id, result):
        if task_id not in self.tasks:
            raise ValueError("Task ins't in the system")
                
        if self.tasks[task_id]["status"] != "RUNNING":
            return False
        if self.tasks[task_id]["worker_id"] != worker_id:
            return False
        
        self.tasks[task_id]["result"] = result
        self.tasks[task_id]["status"] = "COMPLETED"
        self.tasks[task_id]["worker_id"] = None
        
        return True
        
        
        
        
    def retry_task(self, task_id):
        if task_id not in self.tasks:
            raise ValueError("Task ins't in the system")
        
        if self.tasks[task_id]["status"] != "RUNNING":
            raise ValueError("Task isn't in running tasks, only running ones can be retried")
        
        if self.tasks[task_id]["attempts"] >= self.max_attempts:
            return self.fail_task(task_id)
        self.tasks[task_id]["status"] = "PENDING"
        self.tasks[task_id]["worker_id"] = None

        self.pending.append(task_id)   
        return True 
        
                
        
        
        
                
        
            