# FolderSynchronize

This module defines a `FolderSynchronize` class and a function to check the validity of input parameters. Run this module directly to synchronize between two folders.

## 1. Approach

### Task Description

The primary objective of this code is to synchronize files between a source folder and a replica folder efficiently. The code is designed to run as a script, taking input parameters through the command line.

### Approach Summary

- The code defines a `FolderSynchronize` class, which contains methods for copying files in parallel, checking if files in two directories are the same, and synchronizing between the source and replica folders.

- The script takes input parameters (source folder path, replica folder path, log file path, and synchronization interval) through the command line.

- The code uses a `ThreadPoolExecutor` to manage concurrent file copying for efficiency.

- It calculates MD5 hashes to determine if files have been modified since the last synchronization.

- Directories and files present in the source but not in the replica folder are created, and unwanted directories and files in the replica folder are removed.

## 2. Implementation

### Code Usage

To use this code for folder synchronization, follow these steps:

1. Specify the source folder path, replica folder path, log file path, and synchronization interval as command-line arguments when running the script.

2. If required, change the additional parameters by editing the config.py file. Set these parameters based on the resource availability.

  config.py file contains the following parameters:

  file_copy_batch_size: Number of files to be copied on a single batch

  max_workers: The maximum number of worker threads to use for concurrent copying.

  hashing_file_chunk_size: Holds an integer value representing the size (in bytes) of each chunk to be read from the file.

3. The code will continuously synchronize the folders at the specified time intervals. The time interval parameter is specified in seconds.

### Example

Here's an example of how to use the code:

```bash
python FolderSynchronize.py --src_path /path/to/source --replica_path /path/to/replica --log_file_path /path/to/FolderSynclog.log --sync_interval_in_seconds 60
```

In this example, the code will synchronize the source and replica folders every 60 seconds.

### Important Considerations

- Validate the input parameters to ensure correctness.
- The code creates a log file to record synchronization activities. Make sure to provide a valid log file path.
- Adjust the synchronization interval according to your requirements.
