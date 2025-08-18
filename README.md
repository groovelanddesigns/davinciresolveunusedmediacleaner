DaVinci Resolve Unused Media Cleaner
====================================

Version: 1.0
Author: Grooveland Designs
Website: https://www.groovelanddesigns.co.uk

Description
-----------
This tool helps you clean up your DaVinci Resolve projects by identifying unused media clips
and optionally either moving them to a folder or sending them to the Windows Recycle Bin.
It also removes missing/offline clips from the Media Pool.

Key Features
------------
- Scans all timelines to detect which clips are used
- Identifies unused media in the Media Pool
- Option to:
  * Move unused clips to a folder
  * Delete unused clips to the Recycle Bin (Windows only)
- Removes missing/offline clips from the Media Pool
- Dry Run mode to preview changes without modifying files

System Requirements
-------------------
- Windows 10 or later
- DaVinci Resolve (tested with 20)
- Python 3.8+ installed 

Installation
------------

1. Run `drmediacleaner.exe`.
2. The installer will copy the script to the DaVinci Resolve Scripts folder.
3. Open DaVinci Resolve, go to the Scripts menu, and find "Unused Media Cleaner".


Usage
-----
1. Open DaVinci Resolve and start the project you want to clean.
2. Go to the Scripts menu and launch "Unused Media Cleaner".
3. Choose options:
   - Dry Run (recommended for first use)
   - Move unused clips to a folder or delete to Recycle Bin
4. Click "Scan & Clean Unused Media" to start.

Notes
-----
- The script does not modify clips that are currently in use in timelines.
- Dry Run mode allows you to see which clips would be moved or deleted without making changes.
- Always back up your project before performing batch operations.

Safety
------
- The installer and script are unsigned, so Windows may warn you. This is normal.
- The script only affects clips within the current DaVinci Resolve project.

Support
-------
For questions or issues, visit: https://www.groovelanddesigns.co.uk
