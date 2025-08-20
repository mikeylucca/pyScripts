#!/usr/bin/env python3

import os
import sys
import shutil
import hashlib
import logging
import time
import argparse
from pathlib import Path
from typing import Set, Optional


class FolderSynchronizer:
	"""
	A class to handle one-way folder synchronization between source and replica folders.
	"""
	
	def __init__(self, source_path: str, replica_path: str, log_file_path: str):
		"""
		Initialize the synchronizer with source, replica, and log file paths.
		"""
		self.source_path = Path(source_path).resolve()
		self.replica_path = Path(replica_path).resolve()
		self.log_file_path = Path(log_file_path).resolve()
		
		# Setup logging
		self._setup_logging()
		
	def _setup_logging(self):
		"""Setup logging to both file and console."""
		# Create log directory if it doesn't exist
		self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
		
		# Configure logging
		logging.basicConfig(
			level=logging.INFO,
			format='%(asctime)s - %(levelname)s - %(message)s',
			handlers=[
				logging.FileHandler(self.log_file_path, mode='a'),
				logging.StreamHandler(sys.stdout)
			]
		)
		self.logger = logging.getLogger(__name__)
	
	def calculate_file_hash(self, file_path: Path) -> str:
		"""
		Calculate SHA-256 hash of a file. -- SHA256 over MD5 due to its reliability, even though some performance maybe lost.
		"""
		hash_sha256 = hashlib.sha256()
		try:
			with open(file_path, "rb") as f:
				for chunk in iter(lambda: f.read(4096), b""):
					hash_sha256.update(chunk)
			return hash_sha256.hexdigest()
		except IOError as e:
			self.logger.error(f"Error reading file {file_path}: {e}")
			return ""

	def get_directory_structure(self, path: Path) -> Set[Path]:
		"""
		Get all files and directories in a given path recursively.
		"""
		structure = set()
		if not path.exists():
			return structure
			
		try:
			for root, dirs, files in os.walk(path):
				root_path = Path(root)
				
				# Add directories
				for dir_name in dirs:
					rel_path = (root_path / dir_name).relative_to(path)
					structure.add(rel_path)
				
				# Add files
				for file_name in files:
					rel_path = (root_path / file_name).relative_to(path)
					structure.add(rel_path)
					
		except Exception as e:
			self.logger.error(f"Error scanning directory {path}: {e}")
			
		return structure
	
	def files_are_identical(self, source_file: Path, replica_file: Path) -> bool:
		"""
		Check if two files are identical by comparing their SHA256 hashes.
		"""
		if not (source_file.exists() and replica_file.exists()):
			return False
			
		if source_file.stat().st_size != replica_file.stat().st_size:
			return False
			
		return self.calculate_file_hash(source_file) == self.calculate_file_hash(replica_file)
	
	def copy_file(self, source_file: Path, replica_file: Path) -> None:
		"""
		Copy a file from source to replica, creating directories as needed.
		"""
		try:
			# Create parent directories if they don't exist
			replica_file.parent.mkdir(parents=True, exist_ok=True)
			
			# Copy the file
			shutil.copy2(source_file, replica_file)
			self.logger.info(f"COPIED: {source_file} -> {replica_file}")
			
		except Exception as e:
			self.logger.error(f"Error copying {source_file} to {replica_file}: {e}")
	
	def remove_path(self, path: Path) -> None:
		"""
		Remove a file or directory.
		"""
		try:
			if path.is_file():
				path.unlink()
				self.logger.info(f"REMOVED FILE: {path}")
			elif path.is_dir():
				shutil.rmtree(path)
				self.logger.info(f"REMOVED DIRECTORY: {path}")
		except Exception as e:
			self.logger.error(f"Error removing {path}: {e}")
	
	def create_directory(self, dir_path: Path) -> None:
		"""
		Create a directory.
		"""
		try:
			dir_path.mkdir(parents=True, exist_ok=True)
			self.logger.info(f"CREATED DIRECTORY: {dir_path}")
		except Exception as e:
			self.logger.error(f"Error creating directory {dir_path}: {e}")
	
	def synchronize(self) -> None:
		"""
		Perform one-way synchronization from source to replica folder.
		"""
		self.logger.info(f"Starting synchronization: {self.source_path} -> {self.replica_path}")
		
		# Check if source folder exists
		if not self.source_path.exists():
			self.logger.error(f"Source folder does not exist: {self.source_path}")
			return
		
		# Create replica folder if it doesn't exist
		self.replica_path.mkdir(parents=True, exist_ok=True)
		
		# Get directory structures
		source_structure = self.get_directory_structure(self.source_path)
		replica_structure = self.get_directory_structure(self.replica_path)
		
		# Process source items (copy new/updated files and directories)
		for rel_path in source_structure:
			source_item = self.source_path / rel_path
			replica_item = self.replica_path / rel_path
			
			if source_item.is_dir():
				if not replica_item.exists():
					self.create_directory(replica_item)
			else:  # It's a file
				if not replica_item.exists():
					self.copy_file(source_item, replica_item)
				elif not self.files_are_identical(source_item, replica_item):
					self.copy_file(source_item, replica_item)
		
		# Remove items from replica that don't exist in source
		for rel_path in replica_structure:
			if rel_path not in source_structure:
				replica_item = self.replica_path / rel_path
				self.remove_path(replica_item)
		
		self.logger.info("Synchronization completed")


def parse_arguments() -> Optional[tuple[str, str, int, int, str]]:
	"""
	Parse command line arguments in the required order.
	"""
	parser = argparse.ArgumentParser(
		description="Sync source folder to replica folder"
	)
	parser.add_argument("source_path", help="Path to source folder")
	parser.add_argument("replica_path", help="Path to replica folder")
	parser.add_argument("interval", type=int, help="Interval between synchronizations (in seconds)")
	parser.add_argument("amount", type=int, help="Number synchronizations to perform")
	parser.add_argument("log_file_path", help="Path to log file")
	args = parser.parse_args()

	if args.interval < 0 or args.amount < 0:
		print("Error: interval and amount need to be positive")
		return None
	
	return args.source_path, args.replica_path, args.interval, args.amount, args.log_file_path


def main():
	"""
	Main entry point for the folder synchronization program.
	"""
	try:
		# Parse command line arguments
		args = parse_arguments()
		if args is None:
			return
		source_path, replica_path, interval, amount, log_file_path = args
		
		# Create synchronizer instance
		synchronizer = FolderSynchronizer(source_path, replica_path, log_file_path)
		
		# Log program start
		synchronizer.logger.info(f"Program started with parameters:")
		synchronizer.logger.info(f"  Source: {source_path}")
		synchronizer.logger.info(f"  Replica: {replica_path}")
		synchronizer.logger.info(f"  Interval: {interval} seconds")
		synchronizer.logger.info(f"  Amount: {amount} synchronizations")
		synchronizer.logger.info(f"  Log file: {log_file_path}")
		
		# Perform synchronizations
		for sync_count in range(amount):
			synchronizer.logger.info(f"Synchronization {sync_count + 1}/{amount}")
			synchronizer.synchronize()
			
			# Wait for the specified interval before next sync (except after the last one)
			if sync_count < amount - 1 and interval > 0:
				synchronizer.logger.info(f"Waiting {interval} seconds before next synchronization...")
				time.sleep(interval)
		
		synchronizer.logger.info("All synchronizations completed. Program finished.")
		
	except Exception as e:
		print(f"Unexpected error: {e}")
		return

if __name__ == "__main__":
	main()
