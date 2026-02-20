# -*- coding: utf-8 -*-
"""
DaVinci Resolve Unused Media Cleaner (Cross-Platform: Windows & macOS, no external deps)
Version 2.0
- Scans timelines to find used file paths
- Compares against Media Pool to find unused clips
- Option to Move unused files to named folder OR send to Trash/Recycle Bin natively
- Removes corresponding clips from Media Pool; also removes missing/offline clips
- Dry Run mode (no changes)
- Checks scripting preferences before connecting
- Lets user select which file types to process (video/audio/images/other)
- Usage-based protection for compound contents
- Option to check for updates and download new version (.zip) automatically 
"""

import os
import sys
import shutil
import threading
import subprocess
import urllib.request
import urllib.error
import json
import ssl
import tkinter as tk
from tkinter import (
    Tk, Button, Checkbutton, IntVar, Text, Scrollbar, END,
    Label, Entry, messagebox, Radiobutton, DISABLED, NORMAL
)

APP_VERSION = "2.0.0"
GITHUB_API_LATEST = "https://api.github.com/repos/groovelanddesigns/davinciresolveunusedmediacleaner/releases/latest"

# OS Detection
IS_WINDOWS = sys.platform.startswith('win')
IS_MAC = sys.platform.startswith('darwin')

# Dynamic UI & Paths based on OS
if IS_WINDOWS:
    TRASH_NAME = "Recycle Bin"
    RESOLVE_MODULE_PATH = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
    import ctypes
    from ctypes.wintypes import HWND, LPCWSTR, UINT
elif IS_MAC:
    TRASH_NAME = "Trash"
    RESOLVE_MODULE_PATH = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules"
else:
    TRASH_NAME = "Trash"
    RESOLVE_MODULE_PATH = "" # Linux fallback if needed

if RESOLVE_MODULE_PATH and RESOLVE_MODULE_PATH not in sys.path and os.path.isdir(RESOLVE_MODULE_PATH):
    sys.path.append(RESOLVE_MODULE_PATH)

try:
    import DaVinciResolveScript
except Exception:
    print("ERROR: Could not import DaVinciResolveScript. Check scripting module path or ensure Resolve is installed.")
    sys.exit(1)


# --- OS-Specific Trash Implementations ---

def move_to_recycle_bin_win(path: str) -> tuple[bool, str]:
    if not IS_WINDOWS: return False, "Not Windows"
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
    return (ret == 0, "" if ret == 0 else f"SHFileOperationW returned code {ret}")

def move_to_trash_mac(path: str) -> tuple[bool, str]:
    if not IS_MAC: return False, "Not macOS"
    try:
        abs_path = os.path.abspath(path)
        escaped_path = abs_path.replace('\\', '\\\\').replace('"', '\\"')
        script = f'tell application "Finder" to move POSIX file "{escaped_path}" to trash'
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        if result.returncode == 0:
            return True, ""
        else:
            return False, result.stderr.strip() or "Unknown AppleScript error"
    except Exception as e:
        return False, str(e)

def send_to_trash(path: str) -> tuple[bool, str]:
    """Router function to send to the correct native trash."""
    if IS_WINDOWS:
        return move_to_recycle_bin_win(path)
    elif IS_MAC:
        return move_to_trash_mac(path)
    else:
        return False, "Unsupported OS for native trash implementation."


# --- Main Application ---

class UnusedMediaCleanerGUI:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title("DaVinci Resolve Unused Media Cleaner")
        self.root.geometry("980x780")

        # Options
        self.dry_run_var = IntVar(value=0)
        self.action_var = IntVar(value=2)  # 1=Move, 2=Trash

        Label(root, text="Options:").pack(anchor='w', padx=10, pady=(10, 5))
        Checkbutton(root, text="Dry Run (no move/delete or Media Pool removal)", variable=self.dry_run_var)\
            .pack(anchor='w', padx=20)

        Label(root, text="Action for unused media:").pack(anchor='w', padx=10, pady=(12, 0))
        Radiobutton(root, text="Move to folder", variable=self.action_var, value=1,
                    command=self._toggle_folder_entry).pack(anchor='w', padx=20)
        Radiobutton(root, text=f"Delete to {TRASH_NAME}", variable=self.action_var, value=2,
                    command=self._toggle_folder_entry).pack(anchor='w', padx=20)

        row = tk.Frame(root)
        row.pack(anchor='w', padx=10, pady=(10, 5), fill='x')
        Label(row, text="Folder name for moved files:").pack(side='left')
        self.unused_folder_entry = Entry(row, width=30)
        self.unused_folder_entry.insert(0, "Unused")
        self.unused_folder_entry.pack(side='left', padx=6)

        Label(root, text="File types to process:").pack(anchor='w', padx=10, pady=(12, 0))
        self.include_video = IntVar(value=1)
        self.include_audio = IntVar(value=1)
        self.include_images = IntVar(value=1)
        self.include_other = IntVar(value=1)
        Checkbutton(root, text="Video files", variable=self.include_video).pack(anchor='w', padx=20)
        Checkbutton(root, text="Audio files", variable=self.include_audio).pack(anchor='w', padx=20)
        Checkbutton(root, text="Graphics / Images", variable=self.include_images).pack(anchor='w', padx=20)
        Checkbutton(root, text="Other file types", variable=self.include_other).pack(anchor='w', padx=20)

        self.scan_button = Button(root, text="Scan & Clean Unused Media", command=self.start_scan, height=2)
        self.scan_button.pack(pady=12)

        # Log area (expandable)
        self.log_text = Text(root, wrap='word', height=8)
        self.log_text.pack(fill='both', expand=True, padx=10, pady=(0, 8))
        scrollbar = Scrollbar(root, command=self.log_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=scrollbar.set)

        # Footer fixed at bottom (always visible)
        footer = tk.Frame(root)
        footer.pack(side='bottom', fill='x', padx=10, pady=8)
        Button(footer, text="Check for Updates", command=self.check_for_updates).pack(side='left')
        
        # version label bottom-right
        ver_label = Label(footer, text=f"v{APP_VERSION}", anchor='e', fg='gray')
        ver_label.pack(side='right')

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

    def _collect_filepaths_from_timeline(self, timeline, out_set, depth=0):
        if not timeline or depth > 8:
            return
        for track_type in ("video", "audio"):
            try:
                if not hasattr(timeline, "GetTrackCount") or not callable(timeline.GetTrackCount):
                    continue
                track_count = timeline.GetTrackCount(track_type) or 0
            except Exception:
                track_count = 0
            for ti in range(1, track_count + 1):
                try:
                    items = timeline.GetItemsInTrack(track_type, ti) or {}
                except Exception:
                    items = {}
                for _, item in items.items():
                    try:
                        mpi = item.GetMediaPoolItem()
                    except Exception:
                        mpi = None
                    if not mpi:
                        continue
                    try:
                        fp = mpi.GetClipProperty("File Path")
                    except Exception:
                        fp = None
                    if fp and os.path.exists(fp):
                        out_set.add(os.path.normpath(fp))

                    try:
                        ctype = (mpi.GetClipProperty("Type") or "").lower()
                    except Exception:
                        ctype = ""
                    if any(x in ctype for x in ("compound", "fusion", "multicam", "timeline")):
                        inner = None
                        for attr in ("GetTimeline", "GetSourceTimeline"):
                            try:
                                fn = getattr(mpi, attr, None)
                                if callable(fn):
                                    inner = fn()
                                else:
                                    inner = fn
                                if inner:
                                    break
                            except Exception:
                                inner = None
                        if not inner:
                            try:
                                inner = self.project.GetTimelineByName(mpi.GetName())
                            except Exception:
                                inner = None
                        if inner:
                            self._collect_filepaths_from_timeline(inner, out_set, depth + 1)

    def _discover_compound_children(self, mpi):
        found = set()
        for attr in ("GetTimeline", "GetSourceTimeline"):
            try:
                fn = getattr(mpi, attr, None)
                if callable(fn):
                    tl = fn()
                else:
                    tl = fn
                if tl:
                    self._collect_filepaths_from_timeline(tl, found)
            except Exception:
                pass
        try:
            for prop in ("Children", "ChildClips", "Clips"):
                try:
                    val = mpi.GetClipProperty(prop)
                except Exception:
                    val = None
                if not val:
                    continue
                if isinstance(val, str):
                    parts = [p.strip() for p in val.replace(";", ",").split(",") if p.strip()]
                    for p in parts:
                        if os.path.exists(p):
                            found.add(os.path.normpath(p))
                elif isinstance(val, (list, tuple, set)):
                    for el in val:
                        try:
                            if hasattr(el, "GetClipProperty"):
                                fp = el.GetClipProperty("File Path")
                                if fp:
                                    found.add(os.path.normpath(fp))
                            elif isinstance(el, str) and os.path.exists(el):
                                found.add(os.path.normpath(el))
                        except Exception:
                            pass
        except Exception:
            pass
        try:
            if hasattr(mpi, "GetMetadata"):
                md = mpi.GetMetadata() or {}
                for k, v in md.items():
                    if isinstance(v, str) and os.path.exists(v):
                        found.add(os.path.normpath(v))
        except Exception:
            pass
        return found

    def _find_media_pool_item_by_name(self, name):
        if not self.media_pool:
            return None
        try:
            root = self.media_pool.GetRootFolder()
        except Exception:
            return None
        stack = [root]
        while stack:
            folder = stack.pop()
            try:
                clips = folder.GetClips() or {}
            except Exception:
                clips = {}
            for _, c in clips.items():
                try:
                    if c.GetName() == name:
                        return c
                except Exception:
                    pass
            try:
                subs = folder.GetSubFolders() or {}
                for _, sf in subs.items():
                    stack.append(sf)
            except Exception:
                pass
        return None

    def scan_and_clean(self):
        try:
            folder_name = self.unused_folder_entry.get().strip()
            if self.action_var.get() == 1 and not folder_name:
                self.log("WARNING: Unused folder name cannot be empty.")
                self.scan_button.config(state="normal")
                return

            self.log("INFO: Checking DaVinci Resolve scripting preferences...")
            self.resolve = DaVinciResolveScript.scriptapp("Resolve")
            if not self.resolve:
                messagebox.showerror("Connection Failed",
                    "Could not connect to DaVinci Resolve. Ensure Resolve is running and External Scripting enabled.")
                self.scan_button.config(state="normal")
                return

            pm = self.resolve.GetProjectManager()
            self.project = pm.GetCurrentProject()
            if not self.project:
                self.log("WARNING: No project open.")
                self.scan_button.config(state="normal")
                return

            self.media_pool = self.project.GetMediaPool()
            root_folder = self.media_pool.GetRootFolder()

            all_file_clips = []
            def gather_file_clips(folder):
                clips = folder.GetClips() or {}
                for _, c in clips.items():
                    try:
                        ctype = (c.GetClipProperty("Type") or "").lower()
                    except Exception:
                        ctype = ""
                    if any(x in ctype for x in ("compound", "fusion", "multicam", "timeline")):
                        continue
                    try:
                        fp = c.GetClipProperty("File Path")
                    except Exception:
                        fp = None
                    if fp:
                        all_file_clips.append(c)
                for _, sf in (folder.GetSubFolders() or {}).items():
                    gather_file_clips(sf)
            gather_file_clips(root_folder)

            self.log(f"INFO: Current project: {self.project.GetName()}")
            self.log(f"INFO: Total eligible clips in Media Pool: {len(all_file_clips)}")

            used_paths = set()
            idx = 1
            while True:
                tl = self.project.GetTimelineByIndex(idx)
                if not tl:
                    break
                try:
                    self.log(f"INFO: Scanning timeline (including compounds): {tl.GetName()}")
                except Exception:
                    self.log("INFO: Scanning unnamed timeline (including compounds)")
                self._collect_filepaths_from_timeline(tl, used_paths)
                idx += 1

            usage_protected = set()
            for clip in all_file_clips:
                try:
                    usage = clip.GetClipProperty("Usage")
                except Exception:
                    usage = None
                try:
                    if usage is not None and str(usage).isdigit() and int(usage) > 0:
                        fp = clip.GetClipProperty("File Path")
                        if fp:
                            usage_protected.add(os.path.normpath(fp))
                except Exception:
                    pass
            if usage_protected:
                used_paths.update(usage_protected)
                self.log(f"INFO: Protected {len(usage_protected)} clips (Usage > 0).")

            def protect_from_compounds(folder):
                clips = folder.GetClips() or {}
                for _, c in clips.items():
                    try:
                        ctype = (c.GetClipProperty("Type") or "").lower()
                    except Exception:
                        ctype = ""
                    if any(x in ctype for x in ("compound", "fusion", "multicam", "timeline")):
                        try:
                            protected = self._discover_compound_children(c)
                        except Exception:
                            protected = set()
                        if protected:
                            used_paths.update(protected)
                            try:
                                cname = c.GetName()
                            except Exception:
                                cname = "<compound>"
                            self.log(f"INFO: Protected {len(protected)} clips inside compound: {cname}")
                for _, sf in (folder.GetSubFolders() or {}).items():
                    protect_from_compounds(sf)
            protect_from_compounds(root_folder)

            self.log(f"INFO: Total used clip file paths (including Usage & compound discovery): {len(used_paths)}")

            final_candidates = []
            for clip in all_file_clips:
                try:
                    ctype = (clip.GetClipProperty("Type") or "").lower()
                except Exception:
                    ctype = ""
                is_video = "video" in ctype
                is_audio = "audio" in ctype
                is_image = ctype in ("still", "image")
                is_other = not (is_video or is_audio or is_image)
                if is_video and not self.include_video.get():
                    continue
                if is_audio and not self.include_audio.get():
                    continue
                if is_image and not self.include_images.get():
                    continue
                if is_other and not self.include_other.get():
                    continue
                final_candidates.append(clip)

            unused_clips = []
            missing_clips = []
            for clip in final_candidates:
                try:
                    fp = clip.GetClipProperty("File Path")
                except Exception:
                    fp = None
                if not fp:
                    continue
                norm = os.path.normpath(fp)
                if not os.path.exists(norm):
                    missing_clips.append((clip, norm))
                elif norm not in used_paths:
                    unused_clips.append((clip, norm))

            self.log(f"INFO: Unused clips found: {len(unused_clips)}")
            for _, p in unused_clips:
                self.log(f" - {p}")
            self.log(f"INFO: Missing clips found: {len(missing_clips)}")
            for _, p in missing_clips:
                self.log(f" - {p}")

            if not unused_clips and not missing_clips:
                self.log("INFO: No unused or missing media found.")
                self.scan_button.config(state="normal")
                return

            if self.dry_run_var.get():
                self.log("INFO: Dry Run - no changes will be made.")
                self.scan_button.config(state="normal")
                return

            action_label = "Move to folder" if self.action_var.get() == 1 else f"Delete to {TRASH_NAME}"
            proceed = messagebox.askyesno("Confirm Clean",
                                          f"{action_label} {len(unused_clips)} unused files and remove {len(missing_clips)} missing clips. Proceed?")
            if not proceed:
                self.log("INFO: Operation cancelled by user.")
                self.scan_button.config(state="normal")
                return

            moved_or_deleted = 0
            removed_from_pool = 0
            errors = 0
            summary = {"video":0, "audio":0, "image":0, "other":0}

            for clip, path in unused_clips:
                if not os.path.exists(path):
                    self.log(f"WARNING: File not found (skipping): {path}")
                    errors += 1
                    continue
                try:
                    ctype = (clip.GetClipProperty("Type") or "").lower()
                except Exception:
                    ctype = ""
                if "video" in ctype:
                    summary["video"] += 1
                elif "audio" in ctype:
                    summary["audio"] += 1
                elif ctype in ("still", "image"):
                    summary["image"] += 1
                else:
                    summary["other"] += 1

                try:
                    if self.action_var.get() == 1:
                        parent = os.path.dirname(path)
                        dest_dir = os.path.join(parent, folder_name)
                        os.makedirs(dest_dir, exist_ok=True)
                        shutil.move(path, os.path.join(dest_dir, os.path.basename(path)))
                        self.log(f"MOVED: {path} -> {dest_dir}")
                    else:
                        # Unified trash function call here
                        ok, err = send_to_trash(path)
                        if ok:
                            self.log(f"DELETED: {path} to {TRASH_NAME}")
                        else:
                            self.log(f"ERROR: {TRASH_NAME} failed for {path}: {err}")
                            errors += 1
                            continue

                    moved_or_deleted += 1
                    try:
                        if self.media_pool.DeleteClips([clip]):
                            removed_from_pool += 1
                    except Exception:
                        pass
                except Exception as e:
                    self.log(f"ERROR: Processing {path}: {e}")
                    errors += 1

            for clip, path in missing_clips:
                try:
                    if self.media_pool.DeleteClips([clip]):
                        removed_from_pool += 1
                        self.log(f"REMOVED offline clip from Media Pool: {path}")
                    else:
                        self.log(f"WARNING: Failed to remove offline clip: {path}")
                        errors += 1
                except Exception as e:
                    self.log(f"ERROR: Removing offline clip {path}: {e}")
                    errors += 1

            self.log("\n=== SUMMARY ===")
            self.log(f"Video files: {summary['video']}")
            self.log(f"Audio files: {summary['audio']}")
            self.log(f"Image/Graphics files: {summary['image']}")
            self.log(f"Other files: {summary['other']}")
            self.log(f"Total processed: {moved_or_deleted}, removed from pool: {removed_from_pool}, errors: {errors}")

        except Exception as e:
            self.log(f"FATAL ERROR: {e}")

        self.scan_button.config(state="normal")

    def check_for_updates(self):
        try:
            # Attempt to connect normally first
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(GITHUB_API_LATEST, timeout=10, context=ctx) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            # If macOS SSL certs are missing, fallback to unverified context
            if "CERTIFICATE_VERIFY_FAILED" in str(e):
                try:
                    ctx = ssl._create_unverified_context()
                    with urllib.request.urlopen(GITHUB_API_LATEST, timeout=10, context=ctx) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                except Exception as inner_e:
                    messagebox.showwarning("Update Check Failed", f"Could not check for updates: {inner_e}")
                    return
            else:
                messagebox.showwarning("Update Check Failed", f"Could not check for updates: {e}")
                return
        except Exception as e:
            messagebox.showwarning("Update Check Failed", f"Could not check for updates: {e}")
            return

        latest_tag = (data.get("tag_name") or "").lstrip("v").strip()
        assets = data.get("assets", []) or []
        download_asset = None
        for a in assets:
            name = (a.get("name") or "").lower()
            url = a.get("browser_download_url")
            
            if not name or not url:
                continue
                
            # Filter out anything that isn't our core zip files
            if not (name.endswith(".zip") and "python" not in name and "drmediacleaner" in name):
                continue
                
            # OS-Specific Logic based on your file naming convention
            if IS_MAC:
                # Mac users ONLY download the file with "macOS" in the name
                if "macOS" in name:
                    download_asset = (name, url)
                    break
            elif IS_WINDOWS:
                # Windows users ONLY download the file WITHOUT "macOS" in the name
                if "macOS" not in name:
                    download_asset = (name, url)
                    break

        if not latest_tag:
            messagebox.showwarning("Update Check", "Could not determine latest release info.")
            return

        def version_tuple(v):
            parts = [p for p in v.split(".") if p.isdigit()]
            return tuple(int(p) for p in parts)

        try:
            if version_tuple(latest_tag) <= version_tuple(APP_VERSION):
                messagebox.showinfo("Up to Date", f"You are running the latest version ({APP_VERSION}).")
                return
        except Exception:
            if latest_tag <= APP_VERSION:
                messagebox.showinfo("Up to Date", f"You are running the latest version ({APP_VERSION}).")
                return

        if not download_asset:
            messagebox.showwarning("Update Available", f"New version {latest_tag} available but no suitable zip found.")
            return

        name, url = download_asset
        if not messagebox.askyesno("Download Update", f"New version {latest_tag} available.\nDownload {name} to your Downloads folder?"):
            return

        try:
            downloads = os.path.join(os.path.expanduser("~"), "Downloads")
            os.makedirs(downloads, exist_ok=True)
            dst = os.path.join(downloads, os.path.basename(url))
            
            # Using urlopen + shutil instead of urlretrieve to handle SSL contexts properly
            try:
                download_ctx = ssl.create_default_context()
                with urllib.request.urlopen(url, context=download_ctx) as response, open(dst, 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)
            except urllib.error.URLError as e:
                if "CERTIFICATE_VERIFY_FAILED" in str(e):
                    download_ctx = ssl._create_unverified_context()
                    with urllib.request.urlopen(url, context=download_ctx) as response, open(dst, 'wb') as out_file:
                        shutil.copyfileobj(response, out_file)
                else:
                    raise e
                    
            messagebox.showinfo("Downloaded", f"Update downloaded to:\n{dst}")
        except Exception as e:
            messagebox.showerror("Download Failed", f"Failed to download update: {e}")


if __name__ == "__main__":
    root = Tk()
    app = UnusedMediaCleanerGUI(root)
    app._toggle_folder_entry()
    
    # --- Force window to the front ---
    root.lift()
    root.attributes('-topmost', True)
    root.focus_force()
    
    # Remove the 'always on top' lock after 500ms so the user 
    # can still click back to Resolve without the script blocking the view
    root.after(500, lambda: root.attributes('-topmost', False))

    # macOS specific failsafe: forcefully tell the OS to bring the underlying process to the front
    if IS_MAC:
        try:
            os.system(f'''/usr/bin/osascript -e 'tell app "System Events" to set frontmost of the first process whose unix id is {os.getpid()} to true' ''')
        except Exception:
            pass
    # ---------------------------------

    root.mainloop()
