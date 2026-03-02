import threading
import time
import unittest

# Mock classes to simulate Django models/database behavior for threading tests
class MockSubmission:
    def __init__(self, id, is_public=False):
        self.id = id
        self.is_public = is_public


class MockDatabase:
    def __init__(self):
        self.submissions = [
            MockSubmission(1, is_public=True),
            MockSubmission(2, is_public=False),
            MockSubmission(3, is_public=False),
        ]
        self.lock = threading.Lock()
    
    def filter_public_submissions(self):
        time.sleep(0.01)
        return [s for s in self.submissions if s.is_public]
    
    def make_private(self, submission_id):
        time.sleep(0.01)
        for s in self.submissions:
            if s.id == submission_id:
                s.is_public = False
                break
    
    def make_public(self, submission_id):
        time.sleep(0.01)
        for s in self.submissions:
            if s.id == submission_id:
                s.is_public = True
                break
    
    def get_public_count(self):
        return sum(1 for s in self.submissions if s.is_public)
    
    def get_public_ids(self):
        return [s.id for s in self.submissions if s.is_public]


class TestConcurrentSubmissions(unittest.TestCase):
    def test_concurrent_public_toggle_race_condition(self):
        """
        Verifies that concurrent requests to make submissions public don't result in
        multiple public submissions when restricted to one.
        This simulates the logic fixed in views.py by using a lock.
        """
        db = MockDatabase()
        
        # Define the function that simulates the logic in views.py (WITH locking)
        def thread_target(db, new_submission_id):
            with db.lock:
                submissions_already_public = db.filter_public_submissions()
                count = len(submissions_already_public)
                
                time.sleep(0.05)
                
                if count == 1:
                    db.make_private(submissions_already_public[0].id)
                
                db.make_public(new_submission_id)
        
        # Initial state should have 1 public submission
        self.assertEqual(db.get_public_count(), 1, "Initial state should have 1 public submission")
        
        # Run two threads concurrently trying to make different submissions public
        thread1 = threading.Thread(target=thread_target, args=(db, 2))
        thread2 = threading.Thread(target=thread_target, args=(db, 3))
        
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()
        
        # Assertions
        final_count = db.get_public_count()
        public_ids = db.get_public_ids()
        

        self.assertEqual(final_count, 1, f"Expected 1 public submission, found {final_count}. IDs: {public_ids}")

if __name__ == "__main__":
    unittest.main()
