DaVinci Resolve Unused Media Cleaner
====================================

Version: 2.0

Author: Grooveland Designs

Website: https://www.groovelanddesigns.co.uk

Enjoying the plugin? Support our work with a coffee ☕ → https://buymeacoffee.com/groovelanddesigns

-----
Changelog
-----

v2.0
- NEW: Full cross-platform support! The script now runs natively on both macOS and Windows.
- NEW: Native macOS Trash integration for safe media deletion.
- NEW: Dynamic OS-aware GUI that adapts terminology (e.g., "Trash" vs "Recycle Bin") based on your system.
- OS-specific installers added for easier deployment.

v1.2 
- FIX: Improved protection for Compound, Fusion, and Multicam clips — media files used within these are now safely preserved.
- NEW: Integrated Update Checker — checks GitHub for new versions and downloads the latest .zip to your Downloads folder.
- Improved detection and handling of nested timelines.
- Optimized error handling and improved overall stability.
- Verified compatibility with DaVinci Resolve Studio 18, 19, and 20.
- Minor GUI layout and usability improvements.

v1.1
- Improved file type filtering (video, audio, image, other) and logging.
- Added summary of deleted/moved files by type in the log window.
- Clarified that the script works only with DaVinci Resolve Studio (paid version).
- Minor GUI improvements and bug fixes.

v1.0
- Initial release: scan timelines, detect unused media, move or delete unused clips, remove missing/offline clips, dry run mode.

-----
Description
-----

This tool cleans up your DaVinci Resolve projects by identifying unused media clips and optionally either moving them to a dedicated folder or sending them directly to your system's Trash (macOS) or Recycle Bin (Windows). It also removes missing/offline clips from the Media Pool and provides a detailed summary of processed files by type (video, audio, image, other).

Note: Works only with DaVinci Resolve Studio (paid version).

-----
Key Features
-----

- Scans all timelines to detect used clips
- Identifies and removes unused media from the Media Pool
- Option to:
  * Move unused clips to a designated folder
  * Send unused clips to the native macOS Trash or Windows Recycle Bin
- Protects all files nested within Compound, Fusion or Multicam clips
- Removes missing/offline clips from the Media Pool
- Dry Run mode for safe previews before cleanup
- Provides a detailed summary by file type

-----
System Requirements
-----

- OS: Windows 10 (or later) OR macOS 12 (or later)
- Resolve: DaVinci Resolve Studio (tested with versions 18, 19, and 20)
- Python: Python 3.8 or newer 
  * Windows users: Can use the bundled Python installer version.
  * macOS users: Requires official installation from python.org.

-----
Installation
-----

--- For Windows Users ---
1. Run `drmediacleaner.exe` (Script only) OR `drmediacleanerpython.exe` (if you need Python installed silently).
2. The installer will copy the script to the DaVinci Resolve Scripts folder.

--- For macOS Users ---
1. Run the `DRMediaCleaner_v2.0.pkg` installer. It will automatically place the script into the correct Resolve Utility folder.
2. Download and install Python 3 from the official website: https://www.python.org/downloads/macos/
3. IMPORTANT: Once installed, open your Mac's "Applications > Python 3.x" folder and double-click the "Install Certificates.command" file. (This allows the script's Auto-Updater to work).

--- Final Step (Both OS) - IMPORTANT ---
1. In the top menu bar, go to Preferences -> System -> General.
2. Ensure "External Scripting using" is set to "Local" or "Network".
3. Save preferences.

-----
Usage
-----

1. Open DaVinci Resolve Studio and start the project you want to clean.
2. Go to the top menu bar: Workspace -> Scripts -> Utility -> Unused Media Cleaner.
3. Choose your options:
   - Dry Run (Highly recommended for first-time use to see what will happen)
   - Action: Move unused clips to a folder OR Delete to Trash/Recycle Bin
   - Select which file types to process (video, audio, images, other)
4. Click "Scan & Clean Unused Media" to start.
5. After processing, review the summary and results in the log window.

-----
Notes
-----

- The script does not modify clips currently in use in your timelines.
- Dry Run mode allows you to see exactly which clips would be moved or deleted without actually altering any files.
- Always back up your project (.drp) before performing batch operations!
- Works with DaVinci Resolve Studio (paid version) only; the free version does not fully support the external Python scripting API.

-----
Safety & Troubleshooting
-----

- Windows SmartScreen or macOS Gatekeeper may show a warning stating the installer is from an "unidentified developer" — this is normal for indie scripts. 
  * On Mac: You may need to Right-Click the .pkg and select "Open" to bypass the warning.
  * On Windows: Click "More Info" and then "Run Anyway".
- The script only affects files linked within the current, active DaVinci Resolve project.

-----
Support
-----

For updates, help, or feedback, visit:
https://www.groovelanddesigns.co.uk
