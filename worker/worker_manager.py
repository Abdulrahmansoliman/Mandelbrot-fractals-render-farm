from multiprocessing import Process

from worker.worker import Worker


class WorkerManager:
    def __init__(self, worker_count=3, coordinator_url="http://127.0.0.1:8000"):
        if worker_count < 1:
            raise ValueError("Worker count must be at least 1")

        self.worker_count = worker_count
        self.coordinator_url = coordinator_url
        self.processes = []

    def run(self):
        """
        I will add each worker to a seperate process for each one as they 
        independent.
        """
        try:
            for index in range(self.worker_count):
                worker_id = f"worker_{index + 1}"
                worker = Worker(worker_id, self.coordinator_url)
                process = Process(target=worker.run, name=worker_id)
                process.start()
                self.processes.append(process)
                print(f"Started {worker_id} (PID {process.pid})", flush=True)

            for process in self.processes:
                process.join()

            if any(process.exitcode != 0 for process in self.processes):
                raise RuntimeError("A worker stopped with an error")
        finally:
            self.stop()

    def stop(self):
        for process in self.processes:
            if process.is_alive():
                process.terminate()
        """
        Wait till all the processes terminate
        """
        for process in self.processes:
            process.join()
