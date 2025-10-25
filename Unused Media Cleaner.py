# -*- coding: utf-8 -*- 
"""
DaVinci Resolve Unused Media Cleaner (Windows-only, no external deps)
- Scans timelines to find used file paths
- Compares against Media Pool to find unused clips
- Option to Move unused files to named folder OR send to Recycle Bin (Windows Shell API)
- Removes corresponding clips from Media Pool; also removes missing/offline clips
- Dry Run mode (no changes)
- Checks scripting preferences before connecting
- Lets user select which file types to process (video/audio/images/other)
"""

import os
import sys
import shutil
import threading
import ctypes
from ctypes.wintypes import HWND, LPCWSTR, UINT
import tkinter as tk
from tkinter import (
    Tk, Button, Checkbutton, IntVar, Text, Scrollbar, END,
    Label, Entry, messagebox, Radiobutton, DISABLED, NORMAL
)

# --- Optional: add Resolve scripting module path if running outside Resolve's menu ---
RESOLVE_MODULE_PATH = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
if RESOLVE_MODULE_PATH not in sys.path and os.path.isdir(RESOLVE_MODULE_PATH):
    sys.path.append(RESOLVE_MODULE_PATH)

try:
    import DaVinciResolveScript
except ImportError:
    print("ERROR: Could not import DaVinciResolveScript. Check scripting module path.")
    sys.exit(1)

# ---------- Windows Recycle Bin (no 3rd-party libs) ----------
def move_to_recycle_bin_win(path: str) -> tuple[bool, str]:
    """Send a file or folder to the Windows Recycle Bin using SHFileOperationW."""
    class SHFILEOPSTRUCT(ctypes.Structure):
        _fields_ = [
            ("hwnd", HWND),
            ("wFunc", UINT),
            ("pFrom", LPCWSTR),
            ("pTo", LPCWSTR),
            ("fFlags", ctypes.c_uint),
            ("fAnyOperationsAborted", ctypes.c_bool),
            ("hNameMappings", ctypes.c_void_p),
            ("lpszProgressTitle", LPCWSTR),
        ]

    FO_DELETE = 3
    FOF_ALLOWUNDO = 0x0040
    FOF_NOCONFIRMATION = 0x0010
    FOF_SILENT = 0x0004
    flags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT

    pfrom = os.path.abspath(path) + "\0\0"

    op = SHFILEOPSTRUCT()
    op.hwnd = None
    op.wFunc = FO_DELETE
    op.pFrom = pfrom
    op.pTo = None
    op.fFlags = flags
    op.fAnyOperationsAborted = False
    op.hNameMappings = None
    op.lpszProgressTitle = None

    ret = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
    if ret == 0:
        return True, ""
    else:
        return False, f"SHFileOperationW returned code {ret}"

# ---------- GUI ----------
class UnusedMediaCleanerGUI:
    def __init__(self, root: Tk):
        self.root = root
        root.title("DaVinci Resolve Unused Media Cleaner (Windows)")
        root.geometry("880x760")

        # Options
        self.dry_run_var = IntVar(value=0)
        self.action_var = IntVar(value=2)  # 1=Move, 2=Recycle Bin

        Label(root, text="Options:").pack(anchor='w', padx=10, pady=(10,5))
        Checkbutton(root, text="Dry Run (no move/delete or Media Pool removal)", variable=self.dry_run_var)\
            .pack(anchor='w', padx=20)

        Label(root, text="Action for unused media:").pack(anchor='w', padx=10, pady=(12,0))
        Radiobutton(root, text="Move to folder", variable=self.action_var, value=1,
                    command=self._toggle_folder_entry).pack(anchor='w', padx=20)
        Radiobutton(root, text="Delete to Recycle Bin (Windows)", variable=self.action_var, value=2,
                    command=self._toggle_folder_entry).pack(anchor='w', padx=20)

        # Folder name (only used when moving)
        row = tk.Frame(root)
        row.pack(anchor='w', padx=10, pady=(10,5), fill='x')
        Label(row, text="Folder name for moved files:").pack(side='left')
        self.unused_folder_entry = Entry(row, width=22)
        self.unused_folder_entry.insert(0, "Unused")
        self.unused_folder_entry.pack(side='left', padx=6)

        # File type filters
        Label(root, text="File types to process:").pack(anchor='w', padx=10, pady=(12,0))
        self.include_video = IntVar(value=1)
        self.include_audio = IntVar(value=1)
        self.include_images = IntVar(value=1)
        self.include_other = IntVar(value=1)
        Checkbutton(root, text="Video files", variable=self.include_video).pack(anchor='w', padx=20)
        Checkbutton(root, text="Audio files", variable=self.include_audio).pack(anchor='w', padx=20)
        Checkbutton(root, text="Graphics / Images", variable=self.include_images).pack(anchor='w', padx=20)
        Checkbutton(root, text="Other file types", variable=self.include_other).pack(anchor='w', padx=20)

        # Buttons
        self.scan_button = Button(root, text="Scan & Clean Unused Media", command=self.start_scan, height=2)
        self.scan_button.pack(pady=12)

        # Log box
        self.log_text = Text(root, wrap='word', height=28)
        self.log_text.pack(fill='both', expand=True, padx=10, pady=(0,8))

        scrollbar = Scrollbar(root, command=self.log_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=scrollbar.set)

        # Resolve handles
        self.resolve = None
        self.project = None
        self.media_pool = None

    def _toggle_folder_entry(self):
        if self.action_var.get() == 2:
            self.unused_folder_entry.config(state=DISABLED)
        else:
            self.unused_folder_entry.config(state=NORMAL)

    def log(self, msg: str):
        self.log_text.insert(END, msg + "\n")
        self.log_text.see(END)
        self.root.update_idletasks()

    def start_scan(self):
        self.scan_button.config(state="disabled")
        self.log_text.delete('1.0', END)
        threading.Thread(target=self.scan_and_clean, daemon=True).start()

    def scan_and_clean(self):
        try:
            folder_name = self.unused_folder_entry.get().strip()
            if self.action_var.get() == 1 and not folder_name:
                self.log("WARNING: Unused folder name cannot be empty.")
                self.scan_button.config(state="normal")
                return

            # Try connecting to Resolve
            self.log("INFO: Checking DaVinci Resolve scripting preferences...")
            self.resolve = DaVinciResolveScript.scriptapp("Resolve")
            if not self.resolve:
                messagebox.showerror(
                    "Connection Failed",
                    "Could not connect to DaVinci Resolve.\n\n"
                    "Make sure Resolve is running and that in Preferences > System > General "
                    "under External Scripting, you have selected 'Local' or 'Network'."
                )
                self.scan_button.config(state="normal")
                return

            pm = self.resolve.GetProjectManager()
            self.project = pm.GetCurrentProject()
            if not self.project:
                self.log("WARNING: No project is currently open.")
                self.scan_button.config(state="normal")
                return

            self.media_pool = self.project.GetMediaPool()
            root_folder = self.media_pool.GetRootFolder()

            # Gather all media pool clips
            def gather_clips(folder):
                collected = []
                clips = folder.GetClips() or {}
                for _, clip in clips.items():
                    ctype = (clip.GetClipProperty("Type") or "").lower()
                    fpath = clip.GetClipProperty("File Path")
                    if not fpath or ctype == "folder":
                        continue

                    # Filter by type
                    if ("video" in ctype and not self.include_video.get()):
                        continue
                    elif ("audio" in ctype and not self.include_audio.get()):
                        continue
                    elif (ctype in ["still", "image"] and not self.include_images.get()):
                        continue
                    elif (ctype not in ["video", "audio", "still", "image"] and not self.include_other.get()):
                        continue

                    collected.append(clip)

                sub = folder.GetSubFolders() or {}
                for _, subfolder in sub.items():
                    collected += gather_clips(subfolder)
                return collected

            all_clips = gather_clips(root_folder)
            self.log(f"INFO: Current project: {self.project.GetName()}")
            self.log(f"INFO: Total eligible clips in Media Pool: {len(all_clips)}")

            # Collect used paths
            used_paths = set()
            timelines = []
            idx = 1
            while True:
                tl = self.project.GetTimelineByIndex(idx)
                if not tl:
                    break
                timelines.append(tl)
                idx += 1
            self.log(f"INFO: Timelines found: {len(timelines)}")

            for tl in timelines:
                self.log(f"INFO: Scanning timeline: {tl.GetName()}")
                for track_type in ["video","audio"]:
                    track_count = tl.GetTrackCount(track_type)
                    for track_index in range(1, track_count+1):
                        items = tl.GetItemsInTrack(track_type, track_index) or {}
                        for _, item in items.items():
                            mpi = item.GetMediaPoolItem()
                            if not mpi:
                                continue
                            path = mpi.GetClipProperty("File Path")
                            if path and os.path.exists(path):
                                used_paths.add(os.path.normpath(path))
            self.log(f"INFO: Total used clip file paths: {len(used_paths)}")

            # Determine unused & missing clips
            unused_clips = []
            missing_clips = []
            for clip in all_clips:
                clip_path = clip.GetClipProperty("File Path")
                if not clip_path:
                    continue
                norm = os.path.normpath(clip_path)
                if not os.path.exists(norm):
                    missing_clips.append((clip,norm))
                elif norm not in used_paths:
                    unused_clips.append((clip,norm))

            self.log(f"INFO: Unused clips found: {len(unused_clips)}")
            for clip,path in unused_clips:
                self.log(f" - {os.path.basename(path)} ({path})")
            self.log(f"INFO: Missing clips to remove from Media Pool: {len(missing_clips)}")
            for clip,path in missing_clips:
                self.log(f" - {os.path.basename(path)}")

            if not unused_clips and not missing_clips:
                self.log("INFO: No unused or missing media found.")
                self.scan_button.config(state="normal")
                return

            if self.dry_run_var.get():
                self.log("INFO: Dry Run - no changes will be made.")
                self.scan_button.config(state="normal")
                return

            action_label = "Move to folder" if self.action_var.get()==1 else "Delete to Recycle Bin"
            proceed = messagebox.askyesno(
                "Confirm Clean",
                f"{action_label} {len(unused_clips)} unused files and remove {len(missing_clips)} missing clips. Proceed?"
            )
            if not proceed:
                self.log("INFO: Operation cancelled by user.")
                self.scan_button.config(state="normal")
                return

            moved_or_deleted = 0
            removed_from_pool = 0
            errors = 0

            # Initialize summary counters
            summary = {"video":0, "audio":0, "image":0, "other":0}

            # Process unused clips
            for clip,path in unused_clips:
                if not os.path.exists(path):
                    self.log(f"WARNING: File not found (skipping): {path}")
                    errors += 1
                    continue

                try:
                    # Determine type
                    ctype = (clip.GetClipProperty("Type") or "").lower()
                    if "video" in ctype:
                        summary["video"] += 1
                    elif "audio" in ctype:
                        summary["audio"] += 1
                    elif ctype in ["still","image"]:
                        summary["image"] += 1
                    else:
                        summary["other"] += 1

                    if self.action_var.get() == 1:
                        parent = os.path.dirname(path)
                        dest_dir = os.path.join(parent, folder_name)
                        os.makedirs(dest_dir, exist_ok=True)
                        dest_path = os.path.join(dest_dir, os.path.basename(path))
                        shutil.move(path,dest_path)
                        self.log(f"MOVED: {os.path.basename(path)} -> {dest_dir}")
                    else:
                        ok, err = move_to_recycle_bin_win(path)
                        if ok:
                            self.log(f"DELETED: {os.path.basename(path)} to Recycle Bin")
                        else:
                            self.log(f"ERROR: Recycle Bin failed for {os.path.basename(path)}: {err}")
                            errors += 1
                            continue

                    moved_or_deleted += 1
                    if self.media_pool.DeleteClips([clip]):
                        removed_from_pool += 1
                    else:
                        self.log(f"WARNING: Failed to remove from Media Pool: {clip.GetName()}")
                        errors += 1
                except Exception as e:
                    self.log(f"ERROR: Processing {os.path.basename(path)}: {e}")
                    errors += 1

            # Remove missing clips
            for clip,path in missing_clips:
                try:
                    if self.media_pool.DeleteClips([clip]):
                        removed_from_pool += 1
                        self.log(f"REMOVED offline clip from Media Pool: {os.path.basename(path)}")
                    else:
                        self.log(f"WARNING: Failed to remove offline clip: {clip.GetName()}")
                        errors += 1
                except Exception as e:
                    self.log(f"ERROR: Removing offline clip {os.path.basename(path)}: {e}")
                    errors += 1

            # Log summary
            self.log("\n=== SUMMARY OF DELETED/MOVED FILES BY TYPE ===")
            self.log(f"Video files: {summary['video']}")
            self.log(f"Audio files: {summary['audio']}")
            self.log(f"Image/Graphics files: {summary['image']}")
            self.log(f"Other files: {summary['other']}")
            self.log(f"Total files processed: {moved_or_deleted}, removed from Media Pool: {removed_from_pool}, errors: {errors}")

        except Exception as e:
            self.log(f"FATAL ERROR: {e}")

        self.scan_button.config(state="normal")


if __name__ == "__main__":
    root = Tk()
    app = UnusedMediaCleanerGUI(root)
    app._toggle_folder_entry()
    root.mainloop()
