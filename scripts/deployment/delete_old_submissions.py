import os
import shutil
import time

# Define the directory path
tmp_directory = '/tmp'

# Calculate the cutoff time (5 minutes ago)
cutoff_time = time.time() - 5 * 60  # 5 minutes ago

# List all directories in /tmp starting with 'tmp'
tmp_folders = [d for d in os.listdir(tmp_directory) if os.path.isdir(os.path.join(tmp_directory, d)) and d.startswith('tmp')]

for folder in tmp_folders:
    folder_path = os.path.join(tmp_directory, folder)

    # Check if the folder was created more than 5 minutes ago
    folder_creation_time = os.path.getctime(folder_path)
    if folder_creation_time < cutoff_time:
        shutil.rmtree(folder_path)
        print(f"Deleted folder: {folder_path}")
    else:
        print(f"Skipped folder: {folder_path} (created less than 5 minutes ago)")
