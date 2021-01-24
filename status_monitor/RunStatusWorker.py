
from PrStatusWorker import PrStatusWorker
import threading

def initialize_worker():
    worker = PrStatusWorker()
    worker.start_pr_status_polling()

print("Starting the PR status monitor worker thread...")
worker_thread = threading.Thread(target=initialize_worker, name="pr_status_worker")
worker_thread.start()
