DaVinci Resolve Unused Media Cleaner
====================================

Version: 1.1
Author: Grooveland Designs
Website: https://www.groovelanddesigns.co.uk

-----
Changelog
-----

v1.1
- Added summary of deleted/moved files by type (video, audio, image, other) in the log window.
- Improved file type filtering and logging.
- Clarified that the script works only with DaVinci Resolve Studio (paid version).
- Minor GUI improvements and bug fixes.

v1.0
- Initial release: scan timelines, detect unused media, move or delete unused clips, remove missing/offline clips, dry run mode.

-----
Description
-----

This tool helps you clean up your DaVinci Resolve projects by identifying unused media clips and optionally either moving them to a folder or sending them to the Windows Recycle Bin. It also removes missing/offline clips from the Media Pool and provides a summary of processed files by type (video, audio, image, other).

Note: This script works only with DaVinci Resolve Studio (paid version).

-----
Key Features
-----

- Scans all timelines to detect which clips are used
- Identifies unused media in the Media Pool
- Option to:
  * Move unused clips to a folder
  * Delete unused clips to the Recycle Bin (Windows only)
- Removes missing/offline clips from the Media Pool
- Dry Run mode to preview changes without modifying files
- Provides a summary of deleted/moved files by type

-----
System Requirements
-----

- Windows 10 or later
- DaVinci Resolve Studio (tested with version 20)
- Python 3.8+ installed (silent installation included in bundled Python version)

-----
Installation
-----

1. Run `drmediacleaner.exe` or `drmediacleanerpython.exe`.
2. The installer will copy the script to the DaVinci Resolve Scripts folder.
3. IMPORTANT: In your Preferences go to **System → General** and ensure **External Scripting** is enabled (Local/Network).
4. Open DaVinci Resolve, go to the Scripts menu, and find "Unused Media Cleaner".
5. If using the bundled Python version, it installs silently and will be ready automatically.

-----
Usage
-----

1. Open DaVinci Resolve and start the project you want to clean.
2. Go to the Scripts menu and launch "Unused Media Cleaner".
3. Choose options:
   - Dry Run (recommended for first use)
   - Move unused clips to a folder or delete to Recycle Bin
4. Click "Scan & Clean Unused Media" to start.
5. After processing, review the summary of files moved/deleted by type in the log window.

-----
Notes
-----

- The script does not modify clips currently in use in timelines.
- Dry Run mode allows you to see which clips would be moved or deleted without making changes.
- Always back up your project before performing batch operations.
- Works with DaVinci Resolve Studio (paid version) only; free version does not support scripting API fully.

-----
Safety
-----

- The installer and script are unsigned, so Windows may warn you. This is normal.
- The script only affects clips within the current DaVinci Resolve project.

-----
Support
-----

For questions or issues, visit: https://www.groovelanddesigns.co.uk
