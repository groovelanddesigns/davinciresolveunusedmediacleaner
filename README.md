DaVinci Resolve Unused Media Cleaner
====================================

Version: 1.2

Author: Grooveland Designs

Website: https://www.groovelanddesigns.co.uk

Enjoying the plugin? Support our work with a coffee ☕ → https://buymeacoffee.com/groovelanddesigns

-----
Changelog
-----

v1.2 
- FIX: Improved protection for Compound, Fusion, and Multicam clips — media files used within these are now safely preserved
- NEW: Integrated Update Checker — checks GitHub for new versions and downloads the latest .zip to your Downloads folder
- Improved detection and handling of nested timelines
- Optimized error handling and improved overall stability
- Verified compatibility with DaVinci Resolve Studio 18, 19, and 20
- Minor GUI layout and usability improvements

v1.1
- Improved file type filtering (video, audio, image, other) and logging
- Added summary of deleted/moved files by type in the log window
- Clarified that the script works only with DaVinci Resolve Studio (paid version)
- Minor GUI improvements and bug fixes

v1.0
- Initial release: scan timelines, detect unused media, move or delete unused clips, remove missing/offline clips, dry run mode.

-----
Description
-----

This tool cleans up your DaVinci Resolve projects by identifying unused media clips and optionally either moving them to a folder or sending them to the Windows Recycle Bin. It also removes missing/offline clips from the Media Pool and provides a detailed summary of processed files by type (video, audio, image, other).

Note: Works only with DaVinci Resolve Studio (paid version).

-----
Key Features
-----

- Scans all timelines to detect used clips
- Identifies and removes unused media from the Media Pool
- Option to:
  * Move unused clips to a folder
  * Delete unused clips to the Recycle Bin (Windows only)
- Protects all files nested within Compound, Fusion or Multicam Files
- Removes missing/offline clips from the Media Pool
- Dry Run mode for safe previews before cleanup
- Provides a detailed summary by file type

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
4. Open DaVinci Resolve, go to the Scripts menu, and launch "Unused Media Cleaner".
5. If using the bundled Python version, it installs silently and will be ready automatically.

-----
Usage
-----

1. Open DaVinci Resolve Studio and start the project you want to clean.
2. Go to the Scripts menu and run "Unused Media Cleaner".
3. Choose options:
   - Dry Run (recommended for first-time use)
   - Move unused clips to a folder or delete to Recycle Bin
   - Select which file types to include (video, audio, images, other)
4. Click "Scan & Clean Unused Media" to start.
5. After processing, review the summary and results in the log window.

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

- The installer and script are unsigned, so Windows may show a warning - this is normal.
- The script only affects clips within the current DaVinci Resolve project.

-----
Support
-----

For updates, help, or feedback, visit:
https://www.groovelanddesigns.co.uk
