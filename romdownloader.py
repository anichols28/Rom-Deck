import tkinter as tk
from tkinter import filedialog, messagebox
import os
import shutil
from pathlib import Path
import time
import threading
from tkinter import ttk
import json
import subprocess
import sys
import base64
import hashlib
import platform
import io

def install_pip_if_needed():
    """Try to install pip on Steam Deck if missing"""
    try:
        # Check if pip exists
        result = subprocess.run(
            ["python3", "-m", "pip", "--version"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            return True  # pip already exists
    except:
        pass
    
    # Try to install pip using ensurepip
    print("pip not found. Attempting to install pip first...")
    try:
        result = subprocess.run(
            ["python3", "-m", "ensurepip", "--user"],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print("✓ pip installed successfully!")
            return True
        else:
            print(f"✗ Failed to install pip: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Could not install pip: {e}")
        return False

def install_package(pip_name, pacman_name=None, manual_hint=None):
    """Attempt to install a Python package automatically.

    pip_name:     package name for pip (e.g. 'paramiko', 'Pillow')
    pacman_name:  Arch/SteamOS package name (e.g. 'python-paramiko', 'python-pillow')
    manual_hint:  extra text shown if all methods fail
    """
    # On SteamOS, try pacman with read-only filesystem handling
    if pacman_name:
        try:
            print("Trying Steam Deck pacman (with filesystem unlock)...")
            # Disable read-only filesystem
            subprocess.run(["sudo", "steamos-readonly", "disable"],
                           capture_output=True, text=True, timeout=10)
            # Init pacman keys if needed
            subprocess.run(["sudo", "pacman-key", "--init"],
                           capture_output=True, text=True, timeout=30)
            subprocess.run(["sudo", "pacman-key", "--populate", "archlinux"],
                           capture_output=True, text=True, timeout=30)
            # Install the package
            result = subprocess.run(
                ["sudo", "pacman", "-Syu", "--noconfirm", "--overwrite", "*",
                 "--disable-download-timeout", pacman_name],
                capture_output=True, text=True, timeout=120)
            # Re-enable read-only filesystem
            subprocess.run(["sudo", "steamos-readonly", "enable"],
                           capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✓ {pip_name} installed successfully using pacman!")
                return True
            else:
                print(f"✗ pacman failed: {result.stderr.strip()}")
        except FileNotFoundError:
            print("✗ Not a SteamOS system, skipping pacman")
        except subprocess.TimeoutExpired:
            print("✗ pacman - timeout")
            # Re-enable read-only even on timeout
            subprocess.run(["sudo", "steamos-readonly", "enable"],
                           capture_output=True, text=True, timeout=10)
        except Exception as e:
            print(f"✗ pacman - error: {e}")
            subprocess.run(["sudo", "steamos-readonly", "enable"],
                           capture_output=True, text=True, timeout=10)

    methods = [
        (["python3", "-m", "pip", "install", "--user", "--break-system-packages", pip_name], "python3 with --break-system-packages"),
        (["python3", "-m", "pip", "install", "--user", pip_name], "python3 with --user"),
        ([sys.executable, "-m", "pip", "install", "--user", "--break-system-packages", pip_name], "current python with --break-system-packages"),
        ([sys.executable, "-m", "pip", "install", "--user", pip_name], "current python with --user"),
        (["pip3", "install", "--user", "--break-system-packages", pip_name], "pip3 with --break-system-packages"),
        (["pip3", "install", "--user", pip_name], "pip3 with --user"),
    ]

    for cmd, method_name in methods:
        try:
            print(f"Trying {method_name}...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print(f"✓ {pip_name} installed successfully using {method_name}!")
                return True
            else:
                print(f"✗ {method_name} failed: {result.stderr.strip()}")
        except FileNotFoundError:
            print(f"✗ {method_name} - command not found")
        except subprocess.TimeoutExpired:
            print(f"✗ {method_name} - timeout")
        except Exception as e:
            print(f"✗ {method_name} - error: {e}")

    print(f"\n⚠ All installation methods for {pip_name} failed.")
    print("Manual installation required:")
    print(f"\n  === For Steam Deck (Desktop Mode) ===")
    print(f"  Open Konsole and run:")
    if pacman_name:
        print(f"     sudo steamos-readonly disable")
        print(f"     sudo pacman-key --init")
        print(f"     sudo pacman-key --populate archlinux")
        print(f"     sudo pacman -S {pacman_name}")
        print(f"     sudo steamos-readonly enable")
    else:
        print(f"     pip install --user {pip_name}")
    print(f"\n  === For Linux PC ===")
    print(f"     sudo apt install python3-{pip_name.lower()}  (Debian/Ubuntu)")
    print(f"     pip install --user {pip_name}  (other distros)")
    print(f"\n  === For Windows ===")
    print(f"     pip install {pip_name}")
    if manual_hint:
        print(f"\n  {manual_hint}")
    print(f"\n  Then restart this application.\n")
    return False

# Try to import paramiko, install if needed
SFTP_AVAILABLE = False
try:
    import paramiko
    SFTP_AVAILABLE = True
except ImportError:
    print("\n" + "="*50)
    print("paramiko not found. Attempting automatic installation...")
    print("="*50 + "\n")
    if install_package("paramiko", pacman_name="python-paramiko",
                       manual_hint="NOTE: You can still use SMB (local network Z:\\ROMS). SFTP is only needed for remote access."):
        try:
            import paramiko
            SFTP_AVAILABLE = True
            print("\n✓ SFTP support enabled!")
        except:
            print("\n⚠ Installation succeeded but import failed.")
            print("  Please close and restart the application.")
    else:
        print("\n⚠ Automatic installation failed.")
        print("  SFTP features will be disabled until paramiko is installed.")
    print("="*50 + "\n")

# Try to import Pillow for box art display, install if needed
BOXART_AVAILABLE = False
try:
    from PIL import Image, ImageTk
    BOXART_AVAILABLE = True
except ImportError:
    print("\n" + "="*50)
    print("Pillow not found. Attempting automatic installation...")
    print("="*50 + "\n")
    if install_package("Pillow", pacman_name="python-pillow",
                       manual_hint="NOTE: Box art preview will be disabled without Pillow. Everything else works fine."):
        try:
            from PIL import Image, ImageTk
            BOXART_AVAILABLE = True
            print("\n✓ Box art support enabled!")
        except:
            print("\n⚠ Installation succeeded but import failed.")
            print("  Please close and restart the application.")
    else:
        print("\n⚠ Box art preview will be disabled.")
    print("="*50 + "\n")

class ROMDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("ROM Downloader")
        
        # Steam Deck resolution
        self.root.geometry("1280x800")
        self.root.attributes('-fullscreen', False)
        
        # Modern color scheme - dark theme
        self.bg_primary = "#0d1117"
        self.bg_secondary = "#161b22"
        self.bg_tertiary = "#21262d"
        self.accent_blue = "#58a6ff"
        self.accent_green = "#3fb950"
        self.text_primary = "#c9d1d9"
        self.text_secondary = "#8b949e"
        self.border_color = "#30363d"
        
        self.root.config(bg=self.bg_primary)
        
        # State variables
        self.network_path = None
        self.download_path = None
        self.selected_items = []
        self.config_file = Path.home() / ".rom_downloader_config.json"
        self.downloading = False
        self.search_filter = ""
        self.cancel_download_flag = False
        self.current_folder = None
        self.recent_connections = []
        self.sort_order = "name"
        self.file_items = []
        self.all_file_items = []  # Cached unfiltered items (avoids SFTP reload on search)
        self.auto_refresh_enabled = False
        self.refresh_job = None
        self.auto_connect = False  # Auto-connect on startup
        self._search_timer = None  # Debounce timer for search

        # SFTP connection variables
        self.sftp_client = None
        self.ssh_client = None
        self.connection_type = "smb"  # "smb" or "sftp"
        self.sftp_connection_info = None  # Stored for auto-reconnect
        self._sftp_lock = threading.Lock()  # Serialize all SFTP operations (not thread-safe)
        self.passwords_file = Path.home() / ".rom_downloader_passwords.json"
        self.saved_passwords = {}

        # Download history
        self.download_history_file = Path.home() / ".rom_downloader_history.json"
        self.download_history = self._load_download_history()

        # Box art
        self.sftp_root_path = None  # Root ROMS path for computing .metadata relative paths
        self._boxart_cache = {}  # path -> PhotoImage
        self._boxart_photo = None  # Reference to prevent garbage collection
        self._boxart_job = None  # Pending after() id for debouncing
        
        # Load settings
        self.load_settings()
        
        # Configure styles
        self.setup_styles()
        
        # Build UI
        self.build_ui()
        
        # Update initial state
        self.update_disk_space()
    
    def setup_styles(self):
        """Configure modern ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Button styles
        style.configure('Modern.TButton', 
                       font=('Segoe UI', 11, 'bold'),
                       background=self.bg_tertiary,
                       foreground=self.text_primary,
                       borderwidth=0,
                       focuscolor='none',
                       padding=(15, 10))
        
        style.map('Modern.TButton',
                 background=[('active', self.accent_blue)])
        
        # Accent button
        style.configure('Accent.TButton',
                       font=('Segoe UI', 11, 'bold'),
                       background=self.accent_blue,
                       foreground='white',
                       borderwidth=0,
                       padding=(15, 10))
        
        style.map('Accent.TButton',
                 background=[('active', '#1f6feb')])
        
        # Labels
        style.configure('Modern.TLabel',
                       background=self.bg_primary,
                       foreground=self.text_primary,
                       font=('Segoe UI', 10))
        
        style.configure('Header.TLabel',
                       background=self.bg_primary,
                       foreground=self.text_primary,
                       font=('Segoe UI', 14, 'bold'))
        
        # Entry fields
        style.configure('Modern.TEntry',
                       fieldbackground=self.bg_tertiary,
                       foreground=self.text_primary,
                       borderwidth=1,
                       padding=8)
        
        # Focused entry - white border
        style.configure('Focused.TEntry',
                       fieldbackground=self.bg_tertiary,
                       foreground=self.text_primary,
                       borderwidth=3,
                       bordercolor='white',
                       padding=8)
        
        # Frames
        style.configure('Card.TFrame',
                       background=self.bg_secondary,
                       borderwidth=1,
                       relief='flat')
        
        style.configure('Modern.TFrame',
                       background=self.bg_primary)
    
    def build_ui(self):
        """Build the modern UI"""
        # Main container with padding
        main_container = ttk.Frame(self.root, style='Modern.TFrame')
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # === TOP SECTION: Connection & Settings ===
        top_card = ttk.Frame(main_container, style='Card.TFrame')
        top_card.pack(fill=tk.X, pady=(0, 15))
        
        # Inner padding for card
        top_inner = ttk.Frame(top_card, style='Card.TFrame')
        top_inner.pack(fill=tk.BOTH, padx=15, pady=15)
        
        # Network path row
        path_frame = ttk.Frame(top_inner, style='Card.TFrame')
        path_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(path_frame, text="Network Path", style='Modern.TLabel').pack(anchor='w', pady=(0, 5))
        
        path_input_frame = ttk.Frame(path_frame, style='Card.TFrame')
        path_input_frame.pack(fill=tk.X)
        
        self.path_entry = ttk.Combobox(path_input_frame, font=('Segoe UI', 10), values=self.recent_connections)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.path_entry.set(self.network_path or "Z:\\ROMS or sftp://user@host/path")
        
        self.connect_btn = ttk.Button(path_input_frame, text="Connect", command=self.connect_drive, 
                  style='Accent.TButton', width=12)
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Auto-connect checkbox
        self.auto_connect_var = tk.BooleanVar(value=self.auto_connect)
        auto_connect_check = ttk.Checkbutton(path_input_frame, text="Auto-connect", 
                                            variable=self.auto_connect_var,
                                            command=self.toggle_auto_connect)
        auto_connect_check.pack(side=tk.LEFT)
        
        # Destination row
        dest_frame = ttk.Frame(top_inner, style='Card.TFrame')
        dest_frame.pack(fill=tk.X, pady=(0, 10))
        
        dest_label_frame = ttk.Frame(dest_frame, style='Card.TFrame')
        dest_label_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(dest_label_frame, text="Download To", style='Modern.TLabel').pack(side=tk.LEFT)
        
        self.console_label = ttk.Label(dest_label_frame, text="", font=('Segoe UI', 9), 
                                      foreground=self.accent_blue, background=self.bg_secondary)
        self.console_label.pack(side=tk.LEFT, padx=10)
        
        self.disk_space_label = ttk.Label(dest_label_frame, text="", font=('Segoe UI', 9),
                                         foreground=self.accent_green, background=self.bg_secondary)
        self.disk_space_label.pack(side=tk.LEFT)
        
        dest_input_frame = ttk.Frame(dest_frame, style='Card.TFrame')
        dest_input_frame.pack(fill=tk.X)
        
        self.dest_entry = ttk.Entry(dest_input_frame, font=('Segoe UI', 10))
        self.dest_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.dest_entry.insert(0, self.download_path or str(Path.home() / "Downloads"))
        self.dest_entry.bind('<FocusOut>', lambda e: self.update_disk_space())
        
        self.browse_btn = ttk.Button(dest_input_frame, text="Browse", command=self.choose_destination,
                  style='Modern.TButton', width=12)
        self.browse_btn.pack(side=tk.LEFT)
        
        # Search and options row
        search_frame = ttk.Frame(top_inner, style='Card.TFrame')
        search_frame.pack(fill=tk.X)
        
        ttk.Label(search_frame, text="Search", style='Modern.TLabel').pack(side=tk.LEFT, padx=(0, 10))
        
        self.search_entry = ttk.Entry(search_frame, font=('Segoe UI', 10))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.search_entry.bind('<KeyRelease>', self.on_search_change)
        
        ttk.Button(search_frame, text="Clear", command=self.clear_search,
                  style='Modern.TButton', width=8).pack(side=tk.LEFT, padx=(0, 10))
        
        self.auto_refresh_var = tk.BooleanVar(value=False)
        auto_check = ttk.Checkbutton(search_frame, text="Auto-refresh (30s)", 
                                    variable=self.auto_refresh_var,
                                    command=self.toggle_auto_refresh)
        auto_check.pack(side=tk.LEFT)
        
        # === MIDDLE SECTION: File Browser ===
        browser_card = ttk.Frame(main_container, style='Card.TFrame')
        browser_card.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        browser_inner = ttk.Frame(browser_card, style='Card.TFrame')
        browser_inner.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Create horizontal split: file list on left, box art preview on right
        browser_split = ttk.Frame(browser_inner, style='Card.TFrame')
        browser_split.pack(fill=tk.BOTH, expand=True)
        
        # Left side: File list
        file_list_frame = ttk.Frame(browser_split, style='Card.TFrame')
        file_list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Toolbar
        toolbar = ttk.Frame(file_list_frame, style='Card.TFrame')
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        self.back_btn = ttk.Button(toolbar, text="← Back", command=self.go_back,
                  style='Modern.TButton', width=8)
        self.back_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.open_btn = ttk.Button(toolbar, text="📁 Open", command=self.open_selected_folder,
                  style='Accent.TButton', width=8, state=tk.DISABLED)
        self.open_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Button(toolbar, text="Select All", command=self.select_all,
                  style='Modern.TButton', width=10).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(toolbar, text="Deselect", command=self.deselect_all,
                  style='Modern.TButton', width=10).pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Label(toolbar, text="Sort:", style='Modern.TLabel').pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(toolbar, text="Name", command=lambda: self.sort_files("name"),
                  style='Modern.TButton', width=6).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(toolbar, text="Size", command=lambda: self.sort_files("size"),
                  style='Modern.TButton', width=6).pack(side=tk.LEFT)
        
        self.selected_label = ttk.Label(toolbar, text="Selected: 0", 
                                       font=('Segoe UI', 10, 'bold'),
                                       foreground=self.accent_blue,
                                       background=self.bg_secondary)
        self.selected_label.pack(side=tk.RIGHT)
        
        # File listbox
        list_frame = ttk.Frame(file_list_frame, style='Card.TFrame')
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(
            list_frame,
            bg=self.bg_tertiary,
            fg=self.text_primary,
            selectmode=tk.BROWSE,  # BROWSE = single selection, easier for trackpad
            yscrollcommand=scrollbar.set,
            font=('Consolas', 11),
            activestyle='dotbox',
            highlightthickness=2,
            highlightcolor=self.accent_blue,
            highlightbackground=self.border_color,
            borderwidth=0,
            selectbackground=self.accent_blue,
            selectforeground='white',
            exportselection=False  # Keep selection when focus lost
        )
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        
        # Make listbox focusable and grab focus
        self.file_listbox.focus_set()
        
        # Bind events - simplified for Game Mode
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        self.file_listbox.bind('<ButtonRelease-1>', self.on_click_release)  # Click release instead of press
        self.file_listbox.bind('<Return>', self.open_current_item)  # Enter to open
        self.file_listbox.bind('<Double-Button-1>', self.on_double_click)

        # Right side: Box art preview
        if BOXART_AVAILABLE:
            self.boxart_frame = tk.Frame(browser_split, bg=self.bg_secondary, width=280)
            self.boxart_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
            self.boxart_frame.pack_propagate(False)  # Fixed width

            self.boxart_label = tk.Label(
                self.boxart_frame,
                bg=self.bg_secondary,
                text="No art",
                fg=self.text_secondary,
                font=('Segoe UI', 10),
            )
            self.boxart_label.pack(expand=True)

            self.boxart_title = tk.Label(
                self.boxart_frame,
                bg=self.bg_secondary,
                fg=self.text_primary,
                font=('Segoe UI', 9),
                wraplength=260,
            )
            self.boxart_title.pack(side=tk.BOTTOM, pady=(0, 5))

        # === BOTTOM SECTION: Download Controls ===
        download_card = ttk.Frame(main_container, style='Card.TFrame')
        download_card.pack(fill=tk.X)
        
        download_inner = ttk.Frame(download_card, style='Card.TFrame')
        download_inner.pack(fill=tk.X, padx=15, pady=15)
        
        # Buttons
        button_frame = ttk.Frame(download_inner, style='Card.TFrame')
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.download_btn = ttk.Button(button_frame, text="⬇ Download Selected",
                                      command=self.download_rom, state=tk.DISABLED,
                                      style='Accent.TButton')
        self.download_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.cancel_btn = ttk.Button(button_frame, text="✕ Cancel Download",
                                    command=self.cancel_download, state=tk.DISABLED,
                                    style='Modern.TButton')
        self.cancel_btn.pack(side=tk.LEFT)
        
        # Progress bar
        self.progress_canvas = tk.Canvas(
            download_inner,
            height=20,
            bg=self.bg_tertiary,
            highlightthickness=0
        )
        self.progress_canvas.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_rect = self.progress_canvas.create_rectangle(
            0, 0, 0, 20,
            fill=self.accent_green,
            outline=''
        )
        
        # Status label
        self.status_label = tk.Label(
            download_inner,
            text="Ready to download",
            fg=self.text_secondary,
            bg=self.bg_secondary,
            font=('Segoe UI', 10),
            anchor='center'
        )
        self.status_label.pack(fill=tk.X)
        
        # Setup controller/keyboard navigation
        self.setup_navigation()
    
    def setup_navigation(self):
        """Setup keyboard/controller navigation for Steam Deck"""
        # Set focus order - ONLY buttons and listbox (skip input fields)
        self.focusable_widgets = [
            self.connect_btn,
            self.browse_btn,
            self.back_btn,
            self.file_listbox,
            self.open_btn,
            self.download_btn,
        ]
        
        # Bind focus events to all widgets for visual feedback
        for widget in self.focusable_widgets:
            widget.bind('<FocusIn>', self.on_widget_focus_in)
            widget.bind('<FocusOut>', self.on_widget_focus_out)
            
            # Bind arrow keys directly to each widget
            widget.bind('<Down>', self.focus_next)
            widget.bind('<Up>', self.focus_prev)
            widget.bind('<Right>', self.focus_next)
            widget.bind('<Left>', self.focus_prev)
        
        # Button activation
        for widget in [self.connect_btn, self.browse_btn, self.back_btn, self.open_btn, self.download_btn]:
            widget.bind('<space>', lambda e, w=widget: w.invoke())
            widget.bind('<Return>', lambda e, w=widget: w.invoke())
        
        # Global hotkeys for common actions (Steam Deck buttons - map in controller settings)
        # Map these in Steam Input: F1 to B button, F2 to X button
        self.root.bind('<F1>', lambda e: self.go_back())  # B button - Go Back
        self.root.bind('<F2>', lambda e: self.trigger_download())  # X button - Download
        
        # Trigger buttons for fast navigation through large lists
        # Map these in Steam Input: F3 to Left Trigger, F4 to Right Trigger
        self.root.bind('<F3>', lambda e: self.skip_backward())  # Left Trigger - Skip Backward
        self.root.bind('<F4>', lambda e: self.skip_forward())  # Right Trigger - Skip Forward
        
        # Set initial focus to Connect button
        self.connect_btn.focus_set()
    
    def trigger_download(self):
        """Trigger download if button is enabled"""
        if self.download_btn['state'] != tk.DISABLED:
            self.download_rom()
    
    def skip_forward(self):
        """Skip forward through file list - 20 files or next letter (Right Trigger)"""
        try:
            total_items = self.file_listbox.size()
            if total_items == 0:
                return
            
            # Get current selection or start from beginning
            selection = self.file_listbox.curselection()
            current_idx = selection[0] if selection else -1
            
            # If nothing selected, start from 0
            if current_idx == -1:
                new_idx = 0
            else:
                # Try to find next letter first (for alphabetically sorted lists)
                next_letter_idx = self.find_next_letter(current_idx)
                
                # If next letter is close (within 20 items), use that
                # Otherwise skip by 20 items
                if next_letter_idx is not None and (next_letter_idx - current_idx) <= 20:
                    new_idx = next_letter_idx
                else:
                    # Skip forward by 20 items
                    new_idx = min(current_idx + 20, total_items - 1)
            
            # Update selection and ensure it's visible
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(new_idx)
            self.file_listbox.activate(new_idx)
            self.file_listbox.see(new_idx)
            self.on_file_select(None)
            
            # Give focus to listbox so user can see selection
            self.file_listbox.focus_set()
            
            return "break"
        except Exception as e:
            print(f"Skip forward error: {e}")
            import traceback
            traceback.print_exc()
    
    def skip_backward(self):
        """Skip backward through file list - 20 files or previous letter (Left Trigger)"""
        try:
            total_items = self.file_listbox.size()
            if total_items == 0:
                return
            
            # Get current selection or start from end
            selection = self.file_listbox.curselection()
            current_idx = selection[0] if selection else total_items
            
            # If nothing selected, start from end
            if current_idx >= total_items:
                new_idx = total_items - 1
            else:
                # Try to find previous letter first (for alphabetically sorted lists)
                prev_letter_idx = self.find_prev_letter(current_idx)
                
                # If previous letter is close (within 20 items), use that
                # Otherwise skip by 20 items
                if prev_letter_idx is not None and (current_idx - prev_letter_idx) <= 20:
                    new_idx = prev_letter_idx
                else:
                    # Skip backward by 20 items
                    new_idx = max(current_idx - 20, 0)
            
            # Update selection and ensure it's visible
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(new_idx)
            self.file_listbox.activate(new_idx)
            self.file_listbox.see(new_idx)
            self.on_file_select(None)
            
            # Give focus to listbox so user can see selection
            self.file_listbox.focus_set()
            
            return "break"
        except Exception as e:
            print(f"Skip backward error: {e}")
            import traceback
            traceback.print_exc()
    
    def find_next_letter(self, current_idx):
        """Find the next item that starts with a different letter"""
        try:
            total_items = self.file_listbox.size()
            if current_idx >= total_items - 1:
                return None
            
            current_item = self.file_listbox.get(current_idx)
            current_letter = self.get_first_letter(current_item)
            
            # Search forward for next letter
            for i in range(current_idx + 1, total_items):
                item = self.file_listbox.get(i)
                letter = self.get_first_letter(item)
                if letter and letter != current_letter:
                    return i
            
            return None
        except:
            return None
    
    def find_prev_letter(self, current_idx):
        """Find the previous item that starts with a different letter"""
        try:
            if current_idx <= 0:
                return None
            
            current_item = self.file_listbox.get(current_idx)
            current_letter = self.get_first_letter(current_item)
            
            # Search backward for previous letter
            prev_letter = None
            prev_idx = None
            
            for i in range(current_idx - 1, -1, -1):
                item = self.file_listbox.get(i)
                letter = self.get_first_letter(item)
                
                # If we hit a different letter, mark it
                if letter and letter != current_letter:
                    if prev_letter is None:
                        prev_letter = letter
                        prev_idx = i
                    elif letter != prev_letter:
                        # We've found the start of the previous letter section
                        return prev_idx
            
            # Return first different letter we found
            return prev_idx
        except:
            return None
    
    def get_first_letter(self, item):
        """Extract the first alphabetic character from an item name"""
        # Remove folder emoji if present
        clean_item = item.replace('📁  ', '').strip()
        
        # Get first alphanumeric character (uppercase for comparison)
        for char in clean_item:
            if char.isalpha():
                return char.upper()
            elif char.isdigit():
                return '#'  # Group all numbers together
        
        return None
    
    def on_widget_focus_in(self, event):
        """Add white highlight when widget gets focus"""
        widget = event.widget
        if isinstance(widget, tk.Listbox):
            widget.config(highlightthickness=3, highlightcolor='white')
        elif hasattr(widget, 'configure'):
            try:
                # For ttk widgets, we'll use a different approach
                if isinstance(widget, ttk.Button):
                    # Buttons show focus via style
                    pass
                elif isinstance(widget, (ttk.Entry, ttk.Combobox)):
                    widget.config(style='Focused.TEntry')
            except:
                pass
    
    def on_widget_focus_out(self, event):
        """Remove highlight when widget loses focus"""
        widget = event.widget
        if isinstance(widget, tk.Listbox):
            widget.config(highlightthickness=2, highlightcolor=self.accent_blue)
        elif hasattr(widget, 'configure'):
            try:
                if isinstance(widget, (ttk.Entry, ttk.Combobox)):
                    widget.config(style='Modern.TEntry')
            except:
                pass
    
    def focus_next(self, event=None):
        """Focus next widget (D-pad down/right)"""
        focused = self.root.focus_get()
        
        # Special handling for listbox - allow Up/Down for item navigation
        if isinstance(focused, tk.Listbox):
            if event and event.keysym in ['Down', 'Up']:
                # Let listbox handle it normally
                return
            # Left/Right on listbox moves to next widget
        
        try:
            if focused in self.focusable_widgets:
                idx = self.focusable_widgets.index(focused)
                next_idx = (idx + 1) % len(self.focusable_widgets)
                self.focusable_widgets[next_idx].focus_set()
            else:
                self.focusable_widgets[0].focus_set()
        except:
            self.focusable_widgets[0].focus_set()
        return "break"
    
    def focus_prev(self, event=None):
        """Focus previous widget (D-pad up/left)"""
        focused = self.root.focus_get()
        
        # Special handling for listbox - allow Up/Down for item navigation
        if isinstance(focused, tk.Listbox):
            if event and event.keysym in ['Down', 'Up']:
                # Let listbox handle it normally
                return
            # Left/Right on listbox moves to prev widget
        
        try:
            if focused in self.focusable_widgets:
                idx = self.focusable_widgets.index(focused)
                prev_idx = (idx - 1) % len(self.focusable_widgets)
                self.focusable_widgets[prev_idx].focus_set()
            else:
                self.focusable_widgets[-1].focus_set()
        except:
            self.focusable_widgets[-1].focus_set()
        return "break"
    
    # === Core Functions ===
    
    def load_settings(self):
        """Load saved settings"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.network_path = config.get('network_path')
                    self.download_path = config.get('download_path')
                    self.recent_connections = config.get('recent_connections', [])
                    self.auto_connect = config.get('auto_connect', False)
        except Exception as e:
            print(f"Could not load settings: {e}")
        
        # Load saved passwords
        try:
            if self.passwords_file.exists():
                with open(self.passwords_file, 'r') as f:
                    self.saved_passwords = json.load(f)
        except Exception as e:
            print(f"Could not load passwords: {e}")
        
        # Auto-connect if enabled and path exists
        if self.auto_connect and self.network_path:
            # Delay auto-connect to ensure UI is fully initialized
            self.root.after(1000, self.auto_connect_on_startup)
    
    def save_settings(self):
        """Save current settings"""
        try:
            config = {
                'network_path': self.path_entry.get().strip(),
                'download_path': self.dest_entry.get().strip(),
                'recent_connections': self.recent_connections,
                'auto_connect': self.auto_connect
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Could not save settings: {e}")
    
    def toggle_auto_connect(self):
        """Toggle auto-connect setting"""
        self.auto_connect = self.auto_connect_var.get()
        self.save_settings()
    
    def auto_connect_on_startup(self):
        """Auto-connect on startup if enabled"""
        try:
            if not self.network_path:
                return
            
            print(f"Auto-connecting to: {self.network_path}")
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, self.network_path)
            self.connect_drive()
        except Exception as e:
            print(f"Auto-connect failed: {e}")
            import traceback
            traceback.print_exc()
            # Don't crash - just continue with manual connection
    
    def _get_encryption_key(self):
        """Get or create encryption key for password storage."""
        key_file = Path.home() / ".rom_downloader_key"

        if key_file.exists():
            try:
                return key_file.read_bytes()
            except:
                pass

        # Create new key based on machine-specific data
        machine_id = f"{platform.node()}-{os.getlogin() if hasattr(os, 'getlogin') else 'user'}"
        key = hashlib.sha256(machine_id.encode()).digest()

        try:
            key_file.write_bytes(key)
            # Set restrictive permissions on Unix-like systems
            if os.name != 'nt':
                os.chmod(key_file, 0o600)
        except:
            pass

        return key

    def _encrypt_password(self, password):
        """Simple XOR encryption for password (better than plain text)."""
        try:
            key = self._get_encryption_key()
            password_bytes = password.encode('utf-8')

            # XOR encryption
            encrypted = bytearray()
            for i, byte in enumerate(password_bytes):
                encrypted.append(byte ^ key[i % len(key)])

            # Base64 encode for safe storage
            return base64.b64encode(bytes(encrypted)).decode('utf-8')
        except Exception as e:
            print(f"Encryption error: {e}")
            return password  # Fallback to plain text

    def _decrypt_password(self, encrypted_password):
        """Decrypt password."""
        try:
            key = self._get_encryption_key()

            # Base64 decode
            encrypted_bytes = base64.b64decode(encrypted_password.encode('utf-8'))

            # XOR decryption (same as encryption)
            decrypted = bytearray()
            for i, byte in enumerate(encrypted_bytes):
                decrypted.append(byte ^ key[i % len(key)])

            return bytes(decrypted).decode('utf-8')
        except Exception as e:
            print(f"Decryption error: {e}")
            return encrypted_password  # Fallback to plain text

    def save_password(self, host, user, password):
        """Save encrypted password for SFTP connection"""
        try:
            key = f"{user}@{host}"
            encrypted = self._encrypt_password(password)
            self.saved_passwords[key] = encrypted

            with open(self.passwords_file, 'w') as f:
                json.dump(self.saved_passwords, f)

            # Set restrictive permissions
            if os.name != 'nt':
                os.chmod(self.passwords_file, 0o600)
        except Exception as e:
            print(f"Could not save password: {e}")

    def get_saved_password(self, host, user):
        """Get decrypted saved password for SFTP connection"""
        key = f"{user}@{host}"
        encrypted = self.saved_passwords.get(key)
        if encrypted:
            return self._decrypt_password(encrypted)
        return None
    
    def add_to_recent_connections(self, path):
        """Add path to recent connections (max 10)"""
        if path in self.recent_connections:
            self.recent_connections.remove(path)
        self.recent_connections.insert(0, path)
        self.recent_connections = self.recent_connections[:10]
        self.path_entry['values'] = self.recent_connections
    
    def parse_sftp_url(self, url):
        """Parse SFTP URL: sftp://user@host:port/path or sftp://user:pass@host/path"""
        import re
        pattern = r'sftp://(?:([^:@]+)(?::([^@]+))?@)?([^:/]+)(?::(\d+))?(/.*)?'
        match = re.match(pattern, url)
        if match:
            user, password, host, port, path = match.groups()
            return {
                'user': user or 'root',
                'password': password,
                'host': host,
                'port': int(port) if port else 22,
                'path': path or '/'
            }
        return None
    
    def connect_sftp(self, connection_info):
        """Connect to SFTP server"""
        if not SFTP_AVAILABLE:
            response = messagebox.showerror(
                "SFTP Not Available", 
                "SFTP support requires the 'paramiko' package.\n\n"
                "The application attempted to install it automatically.\n"
                "Please restart the application to enable SFTP.\n\n"
                "If the issue persists, install manually with:\n"
                "pip install paramiko"
            )
            return False
        
        try:
            # Close existing connection if any
            self.disconnect_sftp()
            
            self.ssh_client = paramiko.SSHClient()

            # Load known hosts if available
            known_hosts_file = Path.home() / ".ssh" / "known_hosts"
            if known_hosts_file.exists():
                try:
                    self.ssh_client.load_host_keys(str(known_hosts_file))
                except:
                    pass

            # Auto-accept host keys (for personal use)
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            password = connection_info['password']
            save_password = False
            
            # If no password in URL, check saved passwords first
            if not password:
                password = self.get_saved_password(connection_info['host'], connection_info['user'])
                
            # If still no password, prompt for it
            if not password:
                from tkinter import simpledialog
                
                # Create custom dialog for password with remember checkbox
                password_dialog = tk.Toplevel(self.root)
                password_dialog.title("SFTP Password")
                password_dialog.geometry("400x200")
                password_dialog.configure(bg=self.bg_secondary)
                password_dialog.transient(self.root)
                password_dialog.grab_set()
                
                # Center the dialog
                password_dialog.update_idletasks()
                x = (password_dialog.winfo_screenwidth() // 2) - (400 // 2)
                y = (password_dialog.winfo_screenheight() // 2) - (200 // 2)
                password_dialog.geometry(f"400x200+{x}+{y}")
                
                result = {'password': None, 'remember': False}
                
                # Label
                label = tk.Label(
                    password_dialog,
                    text=f"Enter password for {connection_info['user']}@{connection_info['host']}:",
                    bg=self.bg_secondary,
                    fg=self.text_primary,
                    font=('Segoe UI', 10)
                )
                label.pack(pady=(20, 10))
                
                # Password entry
                password_entry = tk.Entry(
                    password_dialog,
                    show='*',
                    bg=self.bg_tertiary,
                    fg=self.text_primary,
                    font=('Segoe UI', 11),
                    insertbackground=self.text_primary
                )
                password_entry.pack(pady=10, padx=20, fill=tk.X)
                password_entry.focus()
                
                # Remember password checkbox
                remember_var = tk.BooleanVar(value=True)
                remember_check = tk.Checkbutton(
                    password_dialog,
                    text="Remember password",
                    variable=remember_var,
                    bg=self.bg_secondary,
                    fg=self.text_primary,
                    selectcolor=self.bg_tertiary,
                    activebackground=self.bg_secondary,
                    activeforeground=self.text_primary,
                    font=('Segoe UI', 10)
                )
                remember_check.pack(pady=5)
                
                def on_ok():
                    result['password'] = password_entry.get()
                    result['remember'] = remember_var.get()
                    password_dialog.destroy()
                
                def on_cancel():
                    password_dialog.destroy()
                
                # Buttons
                button_frame = tk.Frame(password_dialog, bg=self.bg_secondary)
                button_frame.pack(pady=10)
                
                ok_btn = tk.Button(
                    button_frame,
                    text="OK",
                    command=on_ok,
                    bg=self.accent_blue,
                    fg='white',
                    font=('Segoe UI', 10, 'bold'),
                    padx=20,
                    pady=5,
                    relief=tk.FLAT,
                    cursor='hand2'
                )
                ok_btn.pack(side=tk.LEFT, padx=5)
                
                cancel_btn = tk.Button(
                    button_frame,
                    text="Cancel",
                    command=on_cancel,
                    bg=self.bg_tertiary,
                    fg=self.text_primary,
                    font=('Segoe UI', 10, 'bold'),
                    padx=20,
                    pady=5,
                    relief=tk.FLAT,
                    cursor='hand2'
                )
                cancel_btn.pack(side=tk.LEFT, padx=5)
                
                # Bind Enter key to OK
                password_entry.bind('<Return>', lambda e: on_ok())
                password_dialog.bind('<Escape>', lambda e: on_cancel())
                
                # Wait for dialog to close
                self.root.wait_window(password_dialog)
                
                password = result['password']
                save_password = result['remember']
                
                if not password:
                    return False
            
            # Connect with password
            try:
                self.ssh_client.connect(
                    connection_info['host'],
                    port=connection_info['port'],
                    username=connection_info['user'],
                    password=password,
                    timeout=10,
                    look_for_keys=True,
                    allow_agent=True
                )
                
                # Keep connection alive during long browsing sessions
                transport = self.ssh_client.get_transport()
                if transport:
                    transport.set_keepalive(30)

                self.sftp_client = self.ssh_client.open_sftp()

                # Store connection info for auto-reconnect
                self.sftp_connection_info = {
                    'host': connection_info['host'],
                    'port': connection_info['port'],
                    'user': connection_info['user'],
                    'password': password,
                }

                # Save password if requested
                if save_password and password:
                    self.save_password(connection_info['host'], connection_info['user'], password)
                
                return True
                
            except paramiko.AuthenticationException as e:
                messagebox.showerror("SFTP Error", f"Authentication failed. Check your username and password.\n\n{str(e)}")
                return False
            except paramiko.SSHException as e:
                messagebox.showerror("SFTP Error", f"SSH error: {str(e)}")
                return False
            except Exception as e:
                messagebox.showerror("SFTP Error", f"Connection failed: {str(e)}")
                return False
            
        except Exception as e:
            messagebox.showerror("SFTP Error", f"Setup failed: {str(e)}")
            self.disconnect_sftp()
            return False
    
    def disconnect_sftp(self):
        """Close SFTP connection"""
        try:
            if self.sftp_client:
                self.sftp_client.close()
                self.sftp_client = None
            if self.ssh_client:
                self.ssh_client.close()
                self.ssh_client = None
        except:
            pass

    def _ensure_sftp_connected(self):
        """Check SFTP connection is alive, auto-reconnect if not."""
        if self.connection_type != "sftp":
            return True

        # Quick check: is the transport still active?
        try:
            if self.ssh_client and self.ssh_client.get_transport() and self.ssh_client.get_transport().is_active():
                # Send a harmless command to truly verify
                self.sftp_client.stat('.')
                return True
        except Exception:
            pass

        # Connection is dead — try to reconnect
        if not self.sftp_connection_info:
            return False

        print("SFTP connection lost, reconnecting...")
        try:
            self.disconnect_sftp()
            self.ssh_client = paramiko.SSHClient()
            known_hosts_file = Path.home() / ".ssh" / "known_hosts"
            if known_hosts_file.exists():
                try:
                    self.ssh_client.load_host_keys(str(known_hosts_file))
                except:
                    pass
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            info = self.sftp_connection_info
            self.ssh_client.connect(
                info['host'], port=info['port'],
                username=info['user'], password=info['password'],
                timeout=10, look_for_keys=True, allow_agent=True
            )
            transport = self.ssh_client.get_transport()
            if transport:
                transport.set_keepalive(30)
            self.sftp_client = self.ssh_client.open_sftp()
            print("SFTP reconnected successfully")
            return True
        except Exception as e:
            print(f"SFTP reconnect failed: {e}")
            self.root.after(0, lambda: messagebox.showerror(
                "Connection Lost",
                f"SFTP connection dropped and reconnect failed:\n{e}\n\nPlease reconnect manually."
            ))
            return False

    def _load_download_history(self):
        """Load download history from disk."""
        try:
            if self.download_history_file.exists():
                with open(self.download_history_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Could not load download history: {e}")
        return []

    def _save_download_history(self):
        """Save download history to disk."""
        try:
            with open(self.download_history_file, 'w') as f:
                json.dump(self.download_history[-500:], f)  # Keep last 500 entries
        except Exception as e:
            print(f"Could not save download history: {e}")

    def _record_download(self, filename, source_path, dest_path, size_bytes):
        """Record a completed download in history."""
        import datetime
        self.download_history.append({
            'name': filename,
            'source': source_path,
            'dest': dest_path,
            'size': size_bytes,
            'date': datetime.datetime.now().isoformat(),
        })
        self._save_download_history()

    def update_disk_space(self):
        """Update disk space indicator"""
        dest = self.dest_entry.get().strip()
        if dest and os.path.exists(dest):
            try:
                stat = shutil.disk_usage(dest)
                free_gb = stat.free / (1024**3)
                total_gb = stat.total / (1024**3)
                percent_free = (stat.free / stat.total) * 100
                
                color = self.accent_green if percent_free > 20 else "#f0883e" if percent_free > 10 else "#f85149"
                self.disk_space_label.config(text=f"💾 {free_gb:.1f}/{total_gb:.1f} GB free", foreground=color)
            except:
                self.disk_space_label.config(text="")
        else:
            self.disk_space_label.config(text="")
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh"""
        self.auto_refresh_enabled = self.auto_refresh_var.get()
        if self.auto_refresh_enabled:
            self.schedule_refresh()
        else:
            if self.refresh_job:
                self.root.after_cancel(self.refresh_job)
                self.refresh_job = None
    
    def schedule_refresh(self):
        """Schedule next refresh"""
        if self.auto_refresh_enabled and not self.downloading:
            self.load_files()
            self.refresh_job = self.root.after(30000, self.schedule_refresh)
    
    def find_matching_console_folder(self, folder_name):
        """Find matching console folder with fallback alternatives"""
        dest = self.dest_entry.get().strip()
        if not os.path.exists(dest):
            return None
        
        # Define fallback alternatives for certain console folders
        fallback_names = {
            'PS1': ['psx', 'playstation', 'ps1'],
            'psx': ['PS1', 'playstation', 'ps1'],
            'PS2': ['playstation2', 'ps2'],
            'PS3': ['playstation3', 'ps3'],
            'PS4': ['playstation4', 'ps4'],
            'PS5': ['playstation5', 'ps5'],
        }
        
        try:
            # First try exact match (case-insensitive)
            possible_path = os.path.join(dest, folder_name)
            if os.path.isdir(possible_path):
                return possible_path
            
            dest_items = os.listdir(dest)
            for item in dest_items:
                if item.lower() == folder_name.lower() and os.path.isdir(os.path.join(dest, item)):
                    return os.path.join(dest, item)
            
            # If no match found, try fallback alternatives
            if folder_name in fallback_names or folder_name.upper() in fallback_names:
                # Get fallback list (handle both cases)
                fallbacks = fallback_names.get(folder_name) or fallback_names.get(folder_name.upper(), [])
                for fallback in fallbacks:
                    for item in dest_items:
                        if item.lower() == fallback.lower() and os.path.isdir(os.path.join(dest, item)):
                            return os.path.join(dest, item)
        except:
            pass
        
        return None
    
    def update_console_label(self):
        """Update console folder detection"""
        if self.current_folder:
            matching = self.find_matching_console_folder(self.current_folder)
            if matching:
                folder_name = os.path.basename(matching)
                self.console_label.config(text=f"→ {folder_name}/")
            else:
                self.console_label.config(text="")
        else:
            self.console_label.config(text="")
    
    def connect_drive(self):
        path = self.path_entry.get().strip()
        if not path:
            messagebox.showerror("Error", "Please enter a network path")
            return
        
        # Detect connection type
        if path.startswith('sftp://'):
            # SFTP connection
            connection_info = self.parse_sftp_url(path)
            if not connection_info:
                messagebox.showerror("Error", "Invalid SFTP URL format.\nUse: sftp://user@host/path or sftp://user:pass@host:port/path")
                return
            
            if self.connect_sftp(connection_info):
                self.connection_type = "sftp"
                self.network_path = connection_info['path']
                self.sftp_root_path = connection_info['path']  # Remember root for .metadata
                self.current_folder = os.path.basename(self.network_path.rstrip('/'))
                self.add_to_recent_connections(path)
                self.save_settings()
                self.load_files()
                self.update_console_label()
                self.update_disk_space()
                self.status_label.config(text=f"✓ SFTP connected to {connection_info['host']}", fg=self.accent_green)
                print(f"SFTP connected: {path}")
        else:
            # SMB/Local connection
            print(f"Attempting SMB connection to: {path}")
            if not os.path.exists(path):
                error_msg = f"Cannot access: {path}"
                messagebox.showerror("Error", error_msg)
                self.status_label.config(text=f"✗ {error_msg}", fg="#f85149")
                print(error_msg)
                return
            
            self.connection_type = "smb"
            self.network_path = path
            self.sftp_root_path = path  # Remember root for .metadata
            self.current_folder = os.path.basename(path)
            self.add_to_recent_connections(path)
            self.save_settings()
            print(f"Loading files from: {self.network_path}")
            self.load_files()
            self.update_console_label()
            self.update_disk_space()
            self.status_label.config(text=f"✓ Connected to {path}", fg=self.accent_green)
            print(f"SMB connected successfully")
    
    def choose_destination(self):
        folder = filedialog.askdirectory(title="Select Download Location")
        if folder:
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(0, folder)
            self.download_path = folder
            self.save_settings()
            self.update_disk_space()
    
    def format_size(self, size_bytes):
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def load_files(self):
        """Load files in a background thread to avoid UI freezing"""
        if not self.network_path:
            print("load_files: No network path set")
            return
        
        # Show loading indicator
        self.file_listbox.delete(0, tk.END)
        self.file_listbox.insert(tk.END, "⏳ Loading files...")
        self.status_label.config(text="Loading files...", fg=self.text_secondary)
        
        # Run loading in background thread
        thread = threading.Thread(target=self._load_files_thread, daemon=True)
        thread.start()
    
    def _load_files_thread(self):
        """Background thread for loading files"""
        print(f"load_files: Loading from {self.network_path}")
        file_items = []
        
        try:
            if self.connection_type == "sftp":
                # SFTP file listing - use listdir_attr for batch operation
                with self._sftp_lock:
                    if not self._ensure_sftp_connected():
                        self.root.after(0, lambda: messagebox.showerror("Error", "SFTP not connected"))
                        return

                    import stat as stat_module
                    items_attr = self.sftp_client.listdir_attr(self.network_path)

                print(f"SFTP found {len(items_attr)} items")
                if not items_attr:
                    self.root.after(0, lambda: self._display_empty_folder())
                    return

                for item_attr in items_attr:
                    item_name = item_attr.filename
                    full_path = self.network_path.rstrip('/') + '/' + item_name
                    try:
                        is_dir = stat_module.S_ISDIR(item_attr.st_mode)
                        size = 0 if is_dir else item_attr.st_size

                        file_items.append({
                            'name': item_name,
                            'size': size,
                            'is_dir': is_dir,
                            'path': full_path
                        })
                    except Exception as e:
                        print(f"Error processing {item_name}: {e}")
            else:
                # SMB/Local file listing - use scandir for better performance
                print(f"Listing directory: {self.network_path}")
                try:
                    items = list(os.scandir(self.network_path))
                    print(f"Found {len(items)} items")
                except Exception as e:
                    error_msg = f"Failed to list directory: {str(e)}"
                    print(error_msg)
                    self.root.after(0, lambda msg=error_msg: messagebox.showerror("Error", msg))
                    self.root.after(0, lambda msg=error_msg: self.status_label.config(text=f"✗ {msg}", fg="#f85149"))
                    return
                    
                if not items:
                    self.root.after(0, lambda: self._display_empty_folder())
                    return
                
                for entry in items:
                    try:
                        is_dir = entry.is_dir()
                        size = 0 if is_dir else entry.stat().st_size
                        
                        file_items.append({
                            'name': entry.name,
                            'size': size,
                            'is_dir': is_dir,
                            'path': entry.path
                        })
                    except Exception as e:
                        print(f"Error accessing {entry.name}: {e}")
            
            print(f"Total file_items collected: {len(file_items)}")
            
            # Update UI in main thread
            self.root.after(0, lambda: self._display_loaded_files(file_items))
            
        except Exception as e:
            error_msg = f"Failed to load files: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("Error", msg))
            self.root.after(0, lambda msg=error_msg: self.status_label.config(text=f"✗ {msg}", fg="#f85149"))
    
    def _display_empty_folder(self):
        """Helper to display empty folder message"""
        self.file_listbox.delete(0, tk.END)
        self.file_listbox.insert(tk.END, "Folder is empty")
        self.status_label.config(text="Folder is empty", fg=self.text_secondary)
    
    def _display_loaded_files(self, file_items):
        """Helper to display loaded files in UI thread"""
        self.all_file_items = file_items  # Cache full unfiltered list
        self._apply_filter_and_display()
    
    def sort_files(self, sort_by):
        """Sort and display files with batch insert for speed"""
        self.sort_order = sort_by

        if sort_by == "name":
            sorted_items = sorted(self.file_items, key=lambda x: (not x['is_dir'], x['name'].lower()))
        elif sort_by == "size":
            sorted_items = sorted(self.file_items, key=lambda x: (not x['is_dir'], -x['size']))
        else:
            sorted_items = self.file_items

        # Store sorted items for reference
        self.sorted_items = sorted_items

        # Build all display strings first, then insert in one batch
        display_names = []
        for item in sorted_items:
            if item['is_dir']:
                display_names.append(f"📁  {item['name']}")
            else:
                size_str = self.format_size(item['size'])
                display_names.append(f"🎮  {item['name']} ({size_str})")

        # Batch insert — much faster than inserting one at a time
        self.file_listbox.delete(0, tk.END)
        if display_names:
            self.file_listbox.insert(tk.END, *display_names)
    
    def on_search_change(self, event=None):
        """Filter files based on search — debounced to avoid redraw on every keystroke"""
        if self._search_timer:
            self.root.after_cancel(self._search_timer)
        self._search_timer = self.root.after(200, self._do_search)

    def _do_search(self):
        """Execute the debounced search."""
        self.search_filter = self.search_entry.get().lower()
        self._apply_filter_and_display()

    def _apply_filter_and_display(self):
        """Filter cached items and display — no SFTP reload needed"""
        if self.search_filter:
            self.file_items = [
                item for item in self.all_file_items
                if self.search_filter in item['name'].lower()
            ]
        else:
            self.file_items = list(self.all_file_items)

        self.sort_files(self.sort_order)
        self.status_label.config(
            text=f"✓ Showing {len(self.file_items)}/{len(self.all_file_items)} items",
            fg=self.accent_green
        )

    def clear_search(self):
        """Clear search filter"""
        self.search_entry.delete(0, tk.END)
        self.search_filter = ""
        self._apply_filter_and_display()
    
    def select_all(self):
        """Select all items"""
        self.file_listbox.select_set(0, tk.END)
        self.on_file_select(None)
    
    def deselect_all(self):
        """Deselect all items"""
        self.file_listbox.selection_clear(0, tk.END)
        self.on_file_select(None)
    
    def on_file_select(self, event):
        selection = self.file_listbox.curselection()
        if selection:
            self.selected_items = [self.file_listbox.get(selection[0])]
        else:
            self.selected_items = []

        has_items = len(self.selected_items) > 0
        has_folder = (has_items and self.selected_items[0].startswith("📁"))

        self.selected_label.config(text=f"Selected: {len(self.selected_items)}")

        # Enable/disable Open button for folder
        if has_folder:
            self.open_btn.config(state=tk.NORMAL)
        else:
            self.open_btn.config(state=tk.DISABLED)

        # Enable/disable Download button
        if has_items and not self.downloading:
            self.download_btn.config(state=tk.NORMAL)
        else:
            self.download_btn.config(state=tk.DISABLED)

        # Update box art preview (debounced)
        if BOXART_AVAILABLE and has_items and selection:
            self._request_boxart(selection[0])
    
    def _request_boxart(self, listbox_index):
        """Request box art for the selected item (debounced)."""
        if self._boxart_job:
            self.root.after_cancel(self._boxart_job)
        self._boxart_job = self.root.after(150, lambda: self._load_boxart(listbox_index))

    def _load_boxart(self, listbox_index):
        """Determine metadata path and fetch box art in background."""
        if not hasattr(self, 'sorted_items') or listbox_index >= len(self.sorted_items):
            return

        item = self.sorted_items[listbox_index]
        item_name = item['name']

        # Strip file extension for the art filename (e.g. "Alundra (USA).zip" -> "Alundra (USA)")
        name_no_ext = os.path.splitext(item_name)[0] if not item['is_dir'] else item_name

        # Build metadata path: root/.metadata/relative_subdir/name.png
        if not self.sftp_root_path:
            return

        if self.connection_type == "sftp":
            root = self.sftp_root_path.rstrip('/')
            current = self.network_path.rstrip('/')
            # Get relative path from root (e.g. "/shared/ROMS/PS1" -> "PS1")
            if current.startswith(root):
                rel = current[len(root):].strip('/')
            else:
                rel = ""
            art_path = f"{root}/.metadata/{rel}/{name_no_ext}.png" if rel else f"{root}/.metadata/{name_no_ext}.png"
        else:
            root = self.sftp_root_path
            rel = os.path.relpath(self.network_path, root)
            if rel == '.':
                art_path = os.path.join(root, '.metadata', f"{name_no_ext}.png")
            else:
                art_path = os.path.join(root, '.metadata', rel, f"{name_no_ext}.png")

        # Check cache first
        if art_path in self._boxart_cache:
            self._show_boxart(self._boxart_cache[art_path], name_no_ext)
            return

        # Fetch in background thread
        thread = threading.Thread(target=self._fetch_boxart, args=(art_path, name_no_ext), daemon=True)
        thread.start()

    def _fetch_boxart(self, art_path, title):
        """Download box art image in a background thread."""
        if self.downloading:
            return  # Don't compete with download thread for SFTP access
        try:
            if self.connection_type == "sftp":
                if not self.sftp_client:
                    return
                # Read image data into memory (lock prevents conflict with file listing)
                with self._sftp_lock:
                    with self.sftp_client.file(art_path, 'r') as f:
                        img_data = f.read()
                img = Image.open(io.BytesIO(img_data))
            else:
                if not os.path.exists(art_path):
                    self.root.after(0, lambda: self._clear_boxart())
                    return
                img = Image.open(art_path)

            # Resize to fit the panel (max 260px wide, maintain aspect ratio)
            max_w, max_h = 260, 360
            img.thumbnail((max_w, max_h), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            # Cache and display on main thread
            self._boxart_cache[art_path] = photo
            self.root.after(0, lambda: self._show_boxart(photo, title))

        except Exception:
            # No art found or error — clear the panel
            self.root.after(0, lambda: self._clear_boxart())

    def _show_boxart(self, photo, title):
        """Display box art image in the panel."""
        if not BOXART_AVAILABLE:
            return
        self._boxart_photo = photo  # Prevent garbage collection
        self.boxart_label.config(image=photo, text="")
        self.boxart_title.config(text=title)

    def _clear_boxart(self):
        """Clear the box art panel."""
        if not BOXART_AVAILABLE:
            return
        self._boxart_photo = None
        self.boxart_label.config(image="", text="No art")
        self.boxart_title.config(text="")

    def on_click_release(self, event):
        """Handle click release - more reliable than press in Game Mode"""
        # Force selection at click position
        index = self.file_listbox.nearest(event.y)
        if index >= 0:
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(index)
            self.file_listbox.activate(index)
            self.file_listbox.see(index)
            # Manually trigger update
            self.on_file_select(None)
        return "break"
    
    def _navigate_to_folder(self, folder_name):
        """Navigate into a folder — single implementation for Enter, Open button, and double-click."""
        if self.connection_type == "sftp":
            self.network_path = self.network_path.rstrip('/') + '/' + folder_name
        else:
            self.network_path = os.path.join(self.network_path, folder_name)
        self.current_folder = folder_name
        if BOXART_AVAILABLE:
            self._clear_boxart()
        self.load_files()
        self.update_console_label()
        self.selected_label.config(text="Selected: 0")
        self.download_btn.config(state=tk.DISABLED)
        self.open_btn.config(state=tk.DISABLED)

    def _get_folder_name_at(self, index):
        """Return folder name at listbox index, or None if not a folder."""
        try:
            item = self.file_listbox.get(index)
            if item.startswith("📁"):
                return item.replace("📁  ", "")
        except (tk.TclError, IndexError):
            pass
        return None

    def open_current_item(self, event):
        """Open current item with Enter key"""
        folder = self._get_folder_name_at(self.file_listbox.index(tk.ACTIVE))
        if folder:
            self._navigate_to_folder(folder)
        return "break"

    def open_selected_folder(self):
        """Open the selected folder — button alternative for Steam Deck"""
        selection = self.file_listbox.curselection()
        if not selection:
            try:
                selection = (self.file_listbox.index(tk.ACTIVE),)
            except:
                return
        folder = self._get_folder_name_at(selection[0])
        if folder:
            self._navigate_to_folder(folder)

    def on_double_click(self, event):
        selection = self.file_listbox.curselection()
        if selection:
            folder = self._get_folder_name_at(selection[0])
            if folder:
                self._navigate_to_folder(folder)
    
    def go_back(self):
        if self.network_path:
            if self.connection_type == "sftp":
                parent = '/'.join(self.network_path.rstrip('/').split('/')[:-1]) or '/'
                if parent != self.network_path:
                    self.network_path = parent
                    self.current_folder = os.path.basename(parent.rstrip('/')) if parent != '/' else None
                    self.load_files()
                    self.update_console_label()
                    self.selected_label.config(text="Selected: 0")
                    self.download_btn.config(state=tk.DISABLED)
            else:
                parent = os.path.dirname(self.network_path)
                if parent != self.network_path:
                    self.network_path = parent
                    self.current_folder = os.path.basename(parent) if parent else None
                    self.load_files()
                    self.update_console_label()
                    self.selected_label.config(text="Selected: 0")
                    self.download_btn.config(state=tk.DISABLED)
    
    def update_progress_bar(self, percent):
        """Update progress bar"""
        self.root.update_idletasks()
        width = self.progress_canvas.winfo_width()
        if width <= 1:
            width = 1200
        new_width = int((percent / 100.0) * width)
        self.progress_canvas.coords(self.progress_rect, 0, 0, new_width, 20)
        self.progress_canvas.update()
    
    def calculate_eta(self, bytes_remaining, speed_bytes_per_sec):
        """Calculate ETA"""
        if speed_bytes_per_sec <= 0:
            return "..."
        
        seconds = bytes_remaining / speed_bytes_per_sec
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m"
        else:
            return f"{int(seconds // 3600)}h"
    
    def download_rom(self):
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "No item selected")
            return

        dest = self.dest_entry.get().strip()
        if not dest or not os.path.exists(dest):
            messagebox.showerror("Error", "Invalid destination")
            return

        download_dest = dest
        if self.current_folder:
            matching = self.find_matching_console_folder(self.current_folder)
            if matching:
                download_dest = matching

        # Build download list directly from sorted_items — no display text parsing
        items_to_download = []
        for idx in selection:
            if idx < 0 or idx >= len(self.sorted_items):
                continue
            file_item = self.sorted_items[idx]
            items_to_download.append((file_item['path'], file_item['name'], file_item['is_dir'], download_dest))

        if not items_to_download:
            messagebox.showerror("Error", "No valid items selected")
            return

        # Overwrite check
        existing = [name for _, name, _, dd in items_to_download if os.path.exists(os.path.join(dd, name))]
        if existing:
            names = "\n".join(existing[:5])
            if len(existing) > 5:
                names += f"\n... and {len(existing) - 5} more"
            if not messagebox.askyesno("Files Exist", f"These files already exist:\n\n{names}\n\nOverwrite?"):
                return

        self.downloading = True
        self.cancel_download_flag = False
        self.download_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        thread = threading.Thread(target=self.batch_download, args=(items_to_download,), daemon=True)
        thread.start()
    
    def batch_download(self, items_to_download):
        """Download multiple files and folders"""
        total_items = len(items_to_download)
        start_time = time.time()
        total_bytes = 0
        
        self.status_label.config(text=f"Downloading {total_items} item(s)...", fg=self.text_primary)
        self.status_label.update()
        self.root.update()
        
        for index, (source, name, is_folder, destination) in enumerate(items_to_download):
            if self.cancel_download_flag:
                break

            download_dest = os.path.join(destination, name)
            if self.connection_type == "sftp":
                if is_folder:
                    bytes_copied = self.download_sftp_folder(source, download_dest, name, index + 1, total_items)
                else:
                    bytes_copied = self.download_sftp_file(source, download_dest, name, index + 1, total_items)
            else:
                if is_folder:
                    bytes_copied = self.download_folder_with_progress(source, download_dest, name, index + 1, total_items)
                else:
                    bytes_copied = self.download_with_progress(source, download_dest, name, index + 1, total_items)

            total_bytes += bytes_copied
            if bytes_copied > 0:
                self._record_download(name, source, download_dest, bytes_copied)
        
        if not self.cancel_download_flag:
            elapsed = time.time() - start_time
            avg_speed_mbps = (total_bytes / (1024 * 1024)) / elapsed if elapsed > 0 else 0
            self.update_progress_bar(100)
            self.status_label.config(text=f"✓ Complete! {total_items} item(s) | Avg: {avg_speed_mbps:.1f} MB/s", 
                                    fg=self.accent_green)
            self.status_label.update()
            time.sleep(3)
        
        self.update_progress_bar(0)
        self.status_label.config(text="Ready to download", fg=self.text_secondary)
        self.download_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.downloading = False
    
    def download_sftp_file(self, source, destination, filename, current, total):
        """Download single file via SFTP"""
        if not self._ensure_sftp_connected():
            return 0

        self.status_label.config(text=f"[{current}/{total}] Starting SFTP download...", fg=self.text_primary)
        self.status_label.update()
        self.root.update()

        try:
            attr = self.sftp_client.stat(source)
            file_size = attr.st_size
            bytes_downloaded = 0
            start_time = time.time()
            last_update = 0
            
            with self.sftp_client.file(source, 'r') as src, open(destination, 'wb') as dst:
                chunk_size = 512 * 1024
                while not self.cancel_download_flag:
                    chunk = src.read(chunk_size)
                    if not chunk:
                        break
                    dst.write(chunk)
                    bytes_downloaded += len(chunk)
                    
                    current_time = time.time()
                    if current_time - last_update >= 0.1:
                        progress = (bytes_downloaded / file_size) * 100 if file_size > 0 else 0
                        self.update_progress_bar(progress)
                        
                        elapsed = time.time() - start_time
                        speed_mbps = (bytes_downloaded / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                        speed_bytes = bytes_downloaded / elapsed if elapsed > 0 else 0
                        bytes_remaining = file_size - bytes_downloaded
                        eta = self.calculate_eta(bytes_remaining, speed_bytes)
                        
                        status = f"[{current}/{total}] {progress:.0f}% | {speed_mbps:.1f} MB/s | ETA: {eta}"
                        self.status_label.config(text=status, fg=self.text_primary)
                        self.status_label.update()
                        last_update = current_time
                    
                    time.sleep(0.001)
            
            self.update_progress_bar(100)
            self.status_label.config(text=f"[{current}/{total}] 100% | Complete", fg=self.text_primary)
            self.status_label.update()
            
            return file_size
        
        except Exception as e:
            if not self.cancel_download_flag:
                messagebox.showerror("Error", f"SFTP download failed: {str(e)}")
            return 0
    
    def download_sftp_folder(self, source, destination, folder_name, current, total):
        """Download entire folder via SFTP"""
        if not self._ensure_sftp_connected():
            return 0

        total_bytes = 0
        start_time = time.time()

        self.status_label.config(text=f"[{current}/{total}] Preparing {folder_name}...", fg=self.text_primary)
        self.status_label.update()
        self.root.update()
        
        try:
            # Count files recursively
            def count_files(path):
                count = 0
                try:
                    for item in self.sftp_client.listdir_attr(path):
                        import stat
                        if stat.S_ISDIR(item.st_mode):
                            count += count_files(path.rstrip('/') + '/' + item.filename)
                        else:
                            count += 1
                except:
                    pass
                return count
            
            total_files = count_files(source)
            files_copied = 0
            
            self.status_label.config(text=f"[{current}/{total}] {folder_name}: Starting {total_files} files...")
            self.status_label.update()
            self.root.update()
            
            os.makedirs(destination, exist_ok=True)
            
            def download_recursive(remote_dir, local_dir):
                nonlocal total_bytes, files_copied
                
                for item in self.sftp_client.listdir_attr(remote_dir):
                    if self.cancel_download_flag:
                        return
                    
                    remote_path = remote_dir.rstrip('/') + '/' + item.filename
                    local_path = os.path.join(local_dir, item.filename)
                    
                    import stat
                    if stat.S_ISDIR(item.st_mode):
                        os.makedirs(local_path, exist_ok=True)
                        download_recursive(remote_path, local_path)
                    else:
                        try:
                            self.sftp_client.get(remote_path, local_path)
                            total_bytes += item.st_size
                            files_copied += 1
                            
                            elapsed = time.time() - start_time
                            speed_mbps = (total_bytes / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                            
                            if total_files > 0:
                                progress = (files_copied / total_files) * 100
                                self.update_progress_bar(progress)
                            
                            status = f"[{current}/{total}] {folder_name}: {files_copied}/{total_files} files | {speed_mbps:.1f} MB/s"
                            self.status_label.config(text=status, fg=self.text_primary)
                            self.status_label.update()
                            self.progress_canvas.update()
                            self.root.update()
                            time.sleep(0.05)
                        except Exception as e:
                            if not self.cancel_download_flag:
                                print(f"Error downloading {item.filename}: {str(e)}")
            
            download_recursive(source, destination)
            
        except Exception as e:
            if not self.cancel_download_flag:
                messagebox.showerror("Error", f"SFTP folder download failed: {str(e)}")
        
        return total_bytes
    
    def download_folder_with_progress(self, source, destination, folder_name, current, total):
        """Download entire folder"""
        total_bytes = 0
        start_time = time.time()
        
        self.status_label.config(text=f"[{current}/{total}] Preparing {folder_name}...", fg=self.text_primary)
        self.status_label.update()
        self.root.update()
        
        try:
            total_files = sum([len(files) for _, _, files in os.walk(source)])
            files_copied = 0
            
            self.status_label.config(text=f"[{current}/{total}] {folder_name}: Starting {total_files} files...")
            self.status_label.update()
            self.root.update()
            
            os.makedirs(destination, exist_ok=True)
            
            for dirpath, dirnames, filenames in os.walk(source):
                if self.cancel_download_flag:
                    return total_bytes
                
                rel_path = os.path.relpath(dirpath, source)
                dest_dir = os.path.join(destination, rel_path) if rel_path != '.' else destination
                os.makedirs(dest_dir, exist_ok=True)
                
                for filename in filenames:
                    if self.cancel_download_flag:
                        return total_bytes
                    
                    src_file = os.path.join(dirpath, filename)
                    dest_file = os.path.join(dest_dir, filename)
                    
                    try:
                        file_size = os.path.getsize(src_file)
                        shutil.copy2(src_file, dest_file)
                        total_bytes += file_size
                        files_copied += 1
                        
                        elapsed = time.time() - start_time
                        speed_mbps = (total_bytes / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                        
                        if total_files > 0:
                            progress = (files_copied / total_files) * 100
                            self.update_progress_bar(progress)
                        
                        status = f"[{current}/{total}] {folder_name}: {files_copied}/{total_files} files | {speed_mbps:.1f} MB/s"
                        self.status_label.config(text=status, fg=self.text_primary)
                        self.status_label.update()
                        self.progress_canvas.update()
                        self.root.update()
                        time.sleep(0.05)
                    except Exception as e:
                        if not self.cancel_download_flag:
                            print(f"Error copying {filename}: {str(e)}")
        
        except Exception as e:
            if not self.cancel_download_flag:
                messagebox.showerror("Error", f"Folder download failed: {str(e)}")
        
        return total_bytes
    
    def download_with_progress(self, source, destination, filename, current, total):
        self.status_label.config(text=f"[{current}/{total}] Starting download...", fg=self.text_primary)
        self.status_label.update()
        self.root.update()
        
        try:
            file_size = os.path.getsize(source)
            chunk_size = 128 * 1024
            bytes_downloaded = 0
            start_time = time.time()
            last_update = 0
            
            with open(source, 'rb') as src, open(destination, 'wb') as dst:
                while not self.cancel_download_flag:
                    chunk = src.read(chunk_size)
                    if not chunk:
                        break
                    dst.write(chunk)
                    bytes_downloaded += len(chunk)
                    
                    current_time = time.time()
                    if current_time - last_update >= 0.1:
                        progress = (bytes_downloaded / file_size) * 100
                        self.update_progress_bar(progress)
                        
                        elapsed = time.time() - start_time
                        speed_mbps = (bytes_downloaded / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                        speed_bytes = bytes_downloaded / elapsed if elapsed > 0 else 0
                        bytes_remaining = file_size - bytes_downloaded
                        eta = self.calculate_eta(bytes_remaining, speed_bytes)
                        
                        status = f"[{current}/{total}] {progress:.0f}% | {speed_mbps:.1f} MB/s | ETA: {eta}"
                        self.status_label.config(text=status, fg=self.text_primary)
                        self.status_label.update()
                        last_update = current_time
                    
                    time.sleep(0.001)
            
            self.update_progress_bar(100)
            self.status_label.config(text=f"[{current}/{total}] 100% | Complete", fg=self.text_primary)
            self.status_label.update()
            
            return file_size
        
        except Exception as e:
            if not self.cancel_download_flag:
                messagebox.showerror("Error", f"Download failed: {str(e)}")
            return 0
    
    def cancel_download(self):
        """Cancel download"""
        self.cancel_download_flag = True
        self.status_label.config(text="⊘ Download cancelled", fg="#f85149")
        self.download_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)


def _get_ssl_context():
    """Get an SSL context that works in PyInstaller bundles."""
    import ssl
    # Try certifi first (bundled with PyInstaller build)
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    # Try system certs at common Linux paths
    for cert_path in ['/etc/ssl/certs/ca-certificates.crt',
                      '/etc/pki/tls/certs/ca-bundle.crt']:
        if os.path.exists(cert_path):
            return ssl.create_default_context(cafile=cert_path)
    # Last resort: unverified (still better than no updates)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def auto_update():
    """Check GitHub for a newer binary and self-update if running as a PyInstaller bundle."""
    import urllib.request

    # Only self-update when running as a frozen binary (PyInstaller)
    if not getattr(sys, 'frozen', False):
        return

    RELEASE_API = "https://api.github.com/repos/anichols28/Rom-Deck/releases/tags/latest"
    binary_path = Path(sys.executable)
    version_file = binary_path.parent / ".binary_version"
    ssl_ctx = _get_ssl_context()

    try:
        # Get release info from GitHub API
        req = urllib.request.Request(RELEASE_API, headers={
            'User-Agent': 'ROMDownloader',
            'Accept': 'application/vnd.github.v3+json',
        })
        with urllib.request.urlopen(req, timeout=10, context=ssl_ctx) as resp:
            release = json.loads(resp.read().decode())

        # Find the binary asset download URL
        asset_url = None
        remote_updated = release.get("published_at", "")
        for asset in release.get("assets", []):
            if asset["name"] == "romdownloader":
                asset_url = asset["browser_download_url"]
                break

        if not asset_url:
            return

        # Compare against stored version timestamp
        stored_version = ""
        if version_file.exists():
            stored_version = version_file.read_text().strip()

        if stored_version == remote_updated:
            return  # Already up to date

        # Download new binary to a temp file
        temp_path = binary_path.parent / "romdownloader.update"
        req = urllib.request.Request(asset_url, headers={'User-Agent': 'ROMDownloader'})
        with urllib.request.urlopen(req, timeout=120, context=ssl_ctx) as resp:
            with open(temp_path, 'wb') as f:
                f.write(resp.read())

        # Replace current binary with the new one
        os.chmod(str(temp_path), 0o755)
        os.replace(str(temp_path), str(binary_path))

        # Save the version marker
        version_file.write_text(remote_updated)

        # Restart with the new binary
        os.execv(str(binary_path), sys.argv)

    except Exception:
        # Any failure — just continue with current version
        pass


if __name__ == "__main__":
    auto_update()
    root = tk.Tk()
    app = ROMDownloader(root)
    root.mainloop()
