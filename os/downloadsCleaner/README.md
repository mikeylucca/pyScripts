# Downloads Folder Cleaner

A Python script to automatically clean your downloads folder by deleting files and folders older than a specified number of days.

## Features

- **WSL Support**: Automatically detects and accesses Windows Downloads folder from WSL
- **Automatic Downloads Path Detection**: Finds your downloads folder automatically
- **Configurable Age**: Default 30 days, but you can specify any number of days
- **Dry Run Mode**: Test what would be deleted without actually deleting anything
- **Exclusion Patterns**: Exclude specific file types or patterns from deletion
- **Detailed Logging**: Logs all operations to both console and file
- **Error Handling**: Robust error handling for various scenarios
- **Size Reporting**: Shows how much disk space would be freed

## Installation

1. Make sure you have Python 3.6+ installed
2. The script uses only standard library modules, so no additional dependencies are required
3. Make the script executable: `chmod +x downloadsCleaner.py`

## Usage

### Basic Usage

```bash
# Delete items older than 30 days (default)
python3 downloadsCleaner.py

# Delete items older than 7 days
python3 downloadsCleaner.py --days 7

# Dry run - see what would be deleted without actually deleting
python3 downloadsCleaner.py --dry-run

# Exclude certain file types from deletion
python3 downloadsCleaner.py --exclude .pdf .docx important

# Combine options
python3 downloadsCleaner.py --days 14 --dry-run --exclude .pdf
```

### Command Line Options

- `--days DAYS`: Number of days after which items should be deleted (default: 30)
- `--dry-run`: Show what would be deleted without actually deleting anything
- `--exclude PATTERNS`: File patterns to exclude from deletion (e.g., .pdf .docx important)
- `--verbose`: Enable verbose logging
- `--help`: Show help message

## Safety Features

- **Dry run mode** to preview what will be deleted
- **Exclusion patterns** to protect important files
- **Detailed logging** to track all operations
- **Error handling** to prevent crashes
- **Confirmation logging** for all deletions

## Logging

The script creates a log file `downloads_cleaner.log` in the same directory where you run the script. This log contains:

- All files and directories that were deleted
- Any errors that occurred during the process
- Summary statistics (number of items processed, space freed)
- Timestamps for all operations

## Examples

### Example 1: Basic Cleanup
```bash
python3 downloadsCleaner.py
```
This will delete all files and folders in your Downloads directory that are older than 30 days.

### Example 2: Conservative Cleanup
```bash
python3 downloadsCleaner.py --days 7 --dry-run --exclude .pdf .docx .jpg
```
This will show you what would be deleted if you removed items older than 7 days, while protecting PDF, DOCX, and JPG files.

### Example 3: Aggressive Cleanup
```bash
python3 downloadsCleaner.py --days 1 --exclude important
```
This will delete items older than 1 day, but skip any files/folders with "important" in the name.

## Automation

You can automate this script using cron jobs:

```bash
# Edit crontab
crontab -e

# Add this line to run the script every Sunday at 2 AM
0 2 * * 0 /path/to/python3 /path/to/downloadsCleaner.py --days 30
```

## WSL Support

This script is specifically designed to work with Windows Subsystem for Linux (WSL). When running in a WSL environment, it will:

1. **Automatically detect WSL environment** by checking for `/mnt/c` mount point
2. **Scan Windows user directories** to find the correct Downloads folder
3. **Prioritize actual user directories** over system directories (Default, Public, etc.)
4. **Fall back to Linux paths** if Windows Downloads folder is not found

The script will automatically find your Windows Downloads folder at `/mnt/c/Users/[YourWindowsUsername]/Downloads`.

## Troubleshooting

1. **Downloads folder not found**: The script will create a Downloads folder if it doesn't exist
2. **Permission errors**: Make sure you have read/write permissions for your Downloads folder
3. **Log file location**: The log file is created in the same directory where you run the script
4. **WSL path issues**: If the script can't find your Windows Downloads folder, check that `/mnt/c/Users/` is accessible
