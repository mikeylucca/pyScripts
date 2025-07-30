#!/usr/bin/env python3

import os
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import logging
import subprocess
logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s - %(levelname)s - %(message)s',
	handlers=[
		logging.FileHandler('downloads_cleaner.log'),
		logging.StreamHandler()
	]
)
logger = logging.getLogger(__name__)

def get_windows_username():
	windows_user = os.getenv('USERNAME') or os.getenv('USER')
	if windows_user:
		return windows_user
	try:
		result = subprocess.run(['whoami.exe'], 
							  capture_output=True, text=True, shell=True, timeout=5)
		if result.returncode == 0 and result.stdout.strip():
			return result.stdout.strip()
	except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
		pass
	try:
		result = subprocess.run(['cmd.exe', '/c', 'echo %USERNAME%'], 
							  capture_output=True, text=True, shell=True, timeout=5)
		if result.returncode == 0 and result.stdout.strip():
			return result.stdout.strip()
	except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
		pass
	
	return None

def get_downloads_path():

	if os.path.exists("/mnt/c"):
		logger.info("WSL environment detected, looking for Windows Downloads folder")
		try:
			users_dir = "/mnt/c/Users"
			if os.path.exists(users_dir):
				user_dirs = []
				system_dirs = []
				
				for item in os.listdir(users_dir):
					user_path = os.path.join(users_dir, item)
					if os.path.isdir(user_path) and not item.startswith('.'):
						if item.lower() in ['default', 'public', 'all users', 'default user']:
							system_dirs.append(item)
						else:
							user_dirs.append(item)
				for username in user_dirs:
					downloads_path = os.path.join(users_dir, username, "Downloads")
					if os.path.exists(downloads_path):
						logger.info(f"Found Windows Downloads folder for user '{username}': {downloads_path}")
						return downloads_path
				for username in system_dirs:
					downloads_path = os.path.join(users_dir, username, "Downloads")
					if os.path.exists(downloads_path):
						logger.info(f"Found Windows Downloads folder in system directory '{username}': {downloads_path}")
						return downloads_path
		except Exception as e:
			logger.warning(f"Error scanning for Downloads folders: {e}")
		windows_user = get_windows_username()
		if windows_user:
			logger.info(f"Windows username detected: {windows_user}")
			

			windows_downloads_paths = [
				f"/mnt/c/Users/{windows_user}/Downloads",
				f"/mnt/c/Users/{windows_user}/downloads",
				f"/mnt/c/Users/{windows_user}/Desktop/Downloads"
			]
			
			for path in windows_downloads_paths:
				if os.path.exists(path):
					logger.info(f"Found Windows Downloads folder: {path}")
					return path
		

		common_usernames = ['Administrator', 'User', 'Default', 'Public']
		for username in common_usernames:
			path = f"/mnt/c/Users/{username}/Downloads"
			if os.path.exists(path):
				logger.info(f"Found Windows Downloads folder: {path}")
				return path
		
		logger.warning("Windows Downloads folder not found, falling back to Linux paths")
	

	linux_downloads_paths = [
		os.path.expanduser("~/Downloads"),
		os.path.expanduser("~/downloads"),
		"/home/$USER/Downloads",
		"/Users/$USER/Downloads",
		os.path.join(os.path.expanduser("~"), "Downloads")
	]
	
	for path in linux_downloads_paths:
		if os.path.exists(path):
			return path
	

	return os.path.expanduser("~/Downloads")

def is_older_than_days(file_path, days):
	try:
		mtime = os.path.getmtime(file_path)
		file_time = datetime.fromtimestamp(mtime)
		cutoff_time = datetime.now() - timedelta(days=days)
		
		return file_time < cutoff_time
	except (OSError, IOError) as e:
		logger.warning(f"Could not get modification time for {file_path}: {e}")
		return False

def delete_item(item_path, dry_run=False):
	try:
		if os.path.isfile(item_path):
			if not dry_run:
				os.remove(item_path)
				logger.info(f"Deleted file: {item_path}")
			else:
				logger.info(f"[DRY RUN] Would delete file: {item_path}")
		elif os.path.isdir(item_path):
			if not dry_run:
				shutil.rmtree(item_path)
				logger.info(f"Deleted directory: {item_path}")
			else:
				logger.info(f"[DRY RUN] Would delete directory: {item_path}")
	except (OSError, IOError) as e:
		logger.error(f"Error deleting {item_path}: {e}")

def clean_downloads_folder(days=30, dry_run=False, exclude_patterns=None):
	downloads_path = get_downloads_path()
	
	if not os.path.exists(downloads_path):
		logger.error(f"Downloads folder not found: {downloads_path}")
		return
	
	logger.info(f"Starting cleanup of downloads folder: {downloads_path}")
	logger.info(f"Deleting items older than {days} days")
	if dry_run:
		logger.info("DRY RUN MODE - No files will be actually deleted")
	
	deleted_count = 0
	total_size_freed = 0
	
	try:

		items = os.listdir(downloads_path)
		
		for item_name in items:
			item_path = os.path.join(downloads_path, item_name)
			

			if exclude_patterns:
				skip_item = False
				for pattern in exclude_patterns:
					if pattern in item_name:
						logger.info(f"Skipping {item_name} (matches exclude pattern: {pattern})")
						skip_item = True
						break
				if skip_item:
					continue
			

			if is_older_than_days(item_path, days):

				try:
					if os.path.isfile(item_path):
						size = os.path.getsize(item_path)
						total_size_freed += size
					elif os.path.isdir(item_path):
						size = sum(
							os.path.getsize(os.path.join(dirpath, filename))
							for dirpath, dirnames, filenames in os.walk(item_path)
							for filename in filenames
						)
						total_size_freed += size
				except (OSError, IOError):
					size = 0
				
				delete_item(item_path, dry_run)
				deleted_count += 1
	
	except (OSError, IOError) as e:
		logger.error(f"Error accessing downloads folder: {e}")
		return
	

	logger.info(f"Cleanup completed!")
	logger.info(f"Items processed: {deleted_count}")
	logger.info(f"Total size that would be freed: {total_size_freed / (1024*1024):.2f} MB")
	
	if not dry_run:
		logger.info("Files have been deleted. Check downloads_cleaner.log for details.")
	else:
		logger.info("Dry run completed. No files were actually deleted.")

def main():
	parser = argparse.ArgumentParser(
		description="Clean downloads folder by deleting items older than specified days",
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog="""
Examples:
  %(prog)s                    # Delete items older than 30 days
  %(prog)s --days 7          # Delete items older than 7 days
  %(prog)s --dry-run         # Show what would be deleted without actually deleting
  %(prog)s --exclude .pdf .docx  # Exclude PDF and DOCX files from deletion
		"""
	)
	
	parser.add_argument(
		'--days', 
		type=int, 
		default=30,
		help='Number of days after which items should be deleted (default: 30)'
	)
	
	parser.add_argument(
		'--dry-run', 
		action='store_true',
		help='Show what would be deleted without actually deleting anything'
	)
	
	parser.add_argument(
		'--exclude', 
		nargs='+',
		help='File patterns to exclude from deletion (e.g., .pdf .docx important)'
	)
	
	parser.add_argument(
		'--verbose', 
		action='store_true',
		help='Enable verbose logging'
	)
	
	args = parser.parse_args()
	
	if args.verbose:
		logging.getLogger().setLevel(logging.DEBUG)
	

	if args.days < 1:
		logger.error("Days must be at least 1")
		return 1
	
	try:
		clean_downloads_folder(
			days=args.days,
			dry_run=args.dry_run,
			exclude_patterns=args.exclude
		)
		return 0
	except KeyboardInterrupt:
		logger.info("Operation cancelled by user")
		return 1
	except Exception as e:
		logger.error(f"Unexpected error: {e}")
		return 1

if __name__ == "__main__":
	exit(main())