from multiprocessing import Process
from threading import Lock

from worker.worker import Worker


class WorkerManager:
    def __init__(self, worker_count=3, coordinator_url="http://127.0.0.1:8000"):
        if worker_count < 1:
            raise ValueError("Worker count must be at least 1")

        self.worker_count = worker_count
        self.coordinator_url = coordinator_url
        self.processes = []
        self.workers = []
        self.lock = Lock()
        self.killed_workers = set()

    def run(self):
        """
        I will add each worker to a seperate process for each one as they
        independent.
        """
        try:
            self.start()
            self.wait()
        finally:
            self.stop()

    def start(self):
        with self.lock:
            if self.processes:
                raise RuntimeError("Workers have already been started")
            for index in range(self.worker_count):
                worker_id = f"worker_{index + 1}"

                worker = Worker(worker_id, self.coordinator_url)
                process = Process(target=worker.run, name=worker_id)
                process.start()
                self.workers.append((worker_id, process))
                self.processes.append(process)
                print(f"Started {worker_id} (PID {process.pid})", flush=True)

    def wait(self):
        for process in self.processes:
            process.join()

        if any(process.exitcode != 0 and process.name not in self.killed_workers
               for process in self.processes):
            raise RuntimeError("A worker stopped with an error")

    def stop(self):
        for process in self.processes:
            if process.is_alive():
                process.terminate()
        """
        Wait till all the processes terminate
        """
        for process in self.processes:
            process.join()

    def kill(self, w_id):
        with self.lock:
            for worker_id, process in self.workers:
                if w_id == worker_id:
                    if not process.is_alive():
                        return False
                    process.terminate()
                    process.join()
                    self.killed_workers.add(worker_id)
                    return True
            raise ValueError(f"Worker {w_id} not found")
