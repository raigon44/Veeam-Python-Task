"""
FolderSynchronize

This module defines a FolderSynchronize class and a function to check the validity of input parameters.
Run this module directly to synchronize between 2 folders.
It needs the following parameters (which have to provided through command line):
--src_path : Path to the source folder
--replica_path: Path to the replica folder
--log_file_path: Path to the log file
--sync_interval_in_seconds: Time intervals at which the synchronization script have to be executed

Author: Raigon Augustin
Date: 22.09.2023
"""
import hashlib
import os
import logging
import time
import shutil
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from config import FolderSyncConfig


parser = ArgumentParser()
parser.add_argument('--src_path', required=True)
parser.add_argument('--replica_path', required=True)
parser.add_argument('--log_file_path', required=True)
parser.add_argument('--sync_interval_in_seconds', type=int, required=True)
args = parser.parse_args()


class FolderSynchronize:
    """
    FolderSynchronize class

    This class have methods which can copy files in parallel, check if the file in 2 directories are the same, and to synchronize between
    the source and a replica folders
    """
    def __init__(self, source_folder_path: str, dest_folder_path: str):
        """
        Constructor of the FolderSynchronize class. Initialize the source, destination locations
        :param source_folder_path:
        :param dest_folder_path:
        """
        self.source_folder_path = source_folder_path
        self.dest_folder_path = dest_folder_path

    @staticmethod
    def create_directory(path_to_folder: str):
        """
        This function creates the folder in the specified path
        :return:
        """
        os.makedirs(path_to_folder)
        return

    @staticmethod
    def create_hash_file(file_path: str):
        """
        This function creates the hash file for a given file. To avoid inefficiencies while creating hash for large files
        here file is read in chunks of a certain size (defined in the config file)
        :param file_path:
        :return: hash file
        """
        file_md5 = hashlib.md5()
        with open(file_path, 'rb') as fp:
            while True:
                data = fp.read(FolderSyncConfig.hashing_file_chunk_size)
                if not data:
                    break
                file_md5.update(data)
        return file_md5

    def is_file_modified(self, source_file: str, destination_file: str):
        """
        This function checks if the given file present in the source and replica folders are modified after the last run
        :return: True if file was modified, False otherwise
        """
        return self.create_hash_file(source_file).hexdigest() == self.create_hash_file(destination_file).hexdigest()

    @staticmethod
    def copy_file(s):
        """
        Copies the file from source to replica folder
        :param s: list containing path to source file, target location and field indicating if file is modified or newly created
        :return: None
        """
        if s[2] == 'new':
            logger.info(f'Copying new file {s[0]} to {s[1]}')
        else:
            logger.info(f'Updating modified file {s[0]} to {s[1]}')
        shutil.copy2(s[0], s[1])
        return

    @staticmethod
    def copy_files_executor(copy_file, process_list, max_workers):
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(copy_file, process_list)
        return

    def create_new_directory_in_replica_folder(self, source_root, source_directories):
        """
        This function creates new directory
        :param source_root:
        :param source_directories:
        :return: None
        """
        for directory in source_directories:
            src_dir = os.path.join(source_root, directory)
            dest_dir = os.path.join(self.dest_folder_path, os.path.relpath(src_dir, self.source_folder_path))
            if not os.path.exists(dest_dir):
                self.create_directory(dest_dir)
                logger.info(f'Non-existent directory {dest_dir} created in the replica folder!!')

        return

    def remove_unwanted_directories_in_replica_folder(self, destination_root, destination_directories):
        """
        This function removes the directories from replica folder which are not present in the source folder
        :param destination_root:
        :param destination_directories:
        :return:
        """
        for directory in destination_directories:
            dest_dir = os.path.join(destination_root, directory)
            src_dir = os.path.join(self.source_folder_path, os.path.relpath(dest_dir, self.dest_folder_path))
            if not os.path.exists(src_dir):
                os.removedirs(dest_dir)
                logger.info(
                    f'Directory {dest_dir} not present in the source folder. Deleting it from the Replica Folder!!')
        return

    def remove_unwanted_files_in_replica_folder(self, destination_root, destination_files):
        """
        This function removes the files from the replica folder which are not present in the source folder
        :param destination_root:
        :param destination_files:
        :return:
        """
        for file in destination_files:
            dest_file = os.path.join(destination_root, file)
            src_file = os.path.join(self.source_folder_path, os.path.relpath(dest_file, self.dest_folder_path))

            if os.path.exists(src_file):
                continue
            else:
                os.remove(dest_file)
                logger.info(f'Deleting the file {dest_file} which is not present in the source folder.')
        return

    def sync_source_with_replica(self):
        """
        This function syncs the source folder with the replica folder
        :return:
        """

        if not os.path.exists(self.source_folder_path):
            logger.error(f'The entered source folder path {self.source_folder_path} does not exist')
            exit(1)

        if not os.path.exists(self.dest_folder_path):
            logger.info(f'The replica folder {self.dest_folder_path} is not present in the system. Creating the folder ..')
            self.create_directory(self.dest_folder_path)

        files_to_copy = []

        for src_root, src_dirs, src_files in os.walk(self.source_folder_path):

            # Creates new directories in replica folder which are not yet present
            self.create_new_directory_in_replica_folder(src_root, src_dirs)

            # Check if the file is present int replica folder and copies if not present or it has been modified
            for file in src_files:
                src_file = os.path.join(src_root, file)
                dest_file = os.path.join(self.dest_folder_path, os.path.relpath(src_file, self.source_folder_path))
                if os.path.exists(dest_file):
                    if not self.is_file_modified(src_file, dest_file):  # Checks if the file has been modified after last sync
                        os.remove(dest_file)
                        logger.info(f'Deleting the old file {dest_file} from the destination')
                        files_to_copy.append([src_file, dest_file, 'modified']) # File to copy added to the list
                    else:
                        logger.debug('File not modified. No need to copy!!')
                        continue
                else:
                    logger.debug(f'File {dest_file} not present in Replica Folder. Adding to the list')
                    files_to_copy.append([src_file, dest_file, 'new'])  # File to copy added to the list
                    if len(files_to_copy) >= FolderSyncConfig.file_copy_batch_size:
                        logger.debug(f'Number of files to copy exceeded the threshold. Starting the parallel copy...')
                        self.copy_files_executor(self.copy_file, files_to_copy, FolderSyncConfig.max_workers)  # Calls the function to perform parallel copy of the files
                        logger.debug(f'Completed the copying')
                        files_to_copy = []

        if len(files_to_copy) > 0:
            logger.debug('Copying the remaining files to the destination folder.')
            self.copy_files_executor(self.copy_file, files_to_copy, FolderSyncConfig.max_workers)

        for dest_root, dest_dirs, dest_files in os.walk(self.dest_folder_path, topdown=False):

            # Removes files in replica folder which are not present in the source folder
            self.remove_unwanted_files_in_replica_folder(dest_root, dest_files)

            # Removes the folders from the replica directory which are not present in the source directory
            self.remove_unwanted_directories_in_replica_folder(dest_root, dest_dirs)

        return


def is_input_parameters_valid():
    """
    Checks the correctness of the input parameters entered
    :return: True if all the parameters are valid, False otherwise
    """

    if type(args.src_path) is not str:
        logger.error(f'The argument {args.src_path} should be a string.')
        return False
    if type(args.replica_path) is not str:
        logger.error(f'The argument {args.replica_path} should be a string.')
        return False
    if type(args.sync_interval_in_seconds) is not int:
        logger.error(f'The argument {args.sync_interval_in_seconds} should be an integer.')
        return False
    else:
        return True


if __name__ == '__main__':

    logger = logging.getLogger("Folder_Sync")
    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    logging_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(logging_format)

    logger.addHandler(console_handler)

    if type(args.log_file_path) is not str:
        logger.error(f'The argument {args.log_file_path} should be a string.')
        exit(1)

    if not os.path.exists(args.log_file_path):
        logger.info(f'The log file is not available in the system. Trying to create it..')
        try:
            with open(args.log_file_path, 'r') as log_file:
                logger.info(f'Successfully created the log file {args.log_file_path}')
        except FileNotFoundError as fe:
            logger.error(f'FileNotFoundError occurred: {fe}')
            exit(1)

    log_file_handler = logging.FileHandler(args.log_file_path)
    log_file_handler.setLevel(logging.INFO)

    log_file_handler.setFormatter(logging_format)
    logger.addHandler(log_file_handler)

    if is_input_parameters_valid():
        sync_obj = FolderSynchronize(args.src_path, args.replica_path)

        while True:
            try:
                logger.info('Calling the folder synchronization function')
                sync_obj.sync_source_with_replica()
            except Exception as e:
                logger.error(e)
                exit(1)
            time.sleep(args.sync_interval_in_seconds)
    else:
        logger.error(f'Please recheck the input parameters!!')
        exit(1)
