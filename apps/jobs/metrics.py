from prometheus_client import Counter

submissions_loaded_in_queue = Counter(
    "submissions_loaded_in_queue",
    "Counter for total number of submissions pushed into the queue when a submission is made",
)
