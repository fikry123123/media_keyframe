# Complete Portable AppImage - Setup Instructions

## 📦 File
`kenae_media_player_complete-x86_64.AppImage` (290 KB)

## ⚡ Quick Start

### 1. Make it executable
```bash
chmod +x kenae_media_player_complete-x86_64.AppImage
```

### 2. Run it!
```bash
./kenae_media_player_complete-x86_64.AppImage
```

That's it! 🎉

## ✅ What's Included in ONE File

- ✅ Media Player Application
- ✅ 5 Setup Scripts
- ✅ 6+ Documentation Files
- ✅ All Source Code (main.py + modules)
- ✅ Helper Launcher Commands

## 🔧 System Requirements

The AppImage needs:
- **Linux x86_64** (Ubuntu, Debian, Fedora, etc)
- **Python 3.x** (Usually pre-installed)
- **PyQt5** (For GUI)
- **OpenCV** (For video processing)
- **VLC Python** (For audio)

## 💻 Installation (Choose One)

### Option 1: System Packages (RECOMMENDED)

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install python3 python3-pyqt5 python3-opencv python3-vlc
```

**Fedora/RHEL:**
```bash
sudo dnf install python3 python3-PyQt5 python3-opencv vlc-python
```

**Arch:**
```bash
sudo pacman -S python python-pyqt5 opencv python-vlc
```

**macOS (Homebrew):**
```bash
brew install python3 pyqt5 opencv vlc
pip3 install PyQt5 opencv-python python-vlc
```

### Option 2: Using pip

```bash
# Install Python first (from your distro or python.org)
python3 --version

# Install dependencies
pip install PyQt5 opencv-python python-vlc
```

### Option 3: Using AppImage Setup Script

```bash
# Extract setup tools from AppImage
./kenae_media_player_complete-x86_64.AppImage --install

# Choose option to install everything automatically
```

## 🚀 Usage Commands

### Play Videos
```bash
./kenae_media_player_complete-x86_64.AppImage                      # Open GUI
./kenae_media_player_complete-x86_64.AppImage ~/video.mp4          # Open file
./kenae_media_player_complete-x86_64.AppImage ~/picture.png        # View image
```

### Get Help
```bash
./kenae_media_player_complete-x86_64.AppImage --help               # Show help
./kenae_media_player_complete-x86_64.AppImage --docs               # View docs
./kenae_media_player_complete-x86_64.AppImage --scripts            # List scripts
```

### Setup & Installation
```bash
# Interactive menu (recommended for first-time)
./kenae_media_player_complete-x86_64.AppImage --install

# Quick install (auto-detect)
./kenae_media_player_complete-x86_64.AppImage --quick-install

# Full setup from source
./kenae_media_player_complete-x86_64.AppImage --setup

# Build AppImage from source
./kenae_media_player_complete-x86_64.AppImage --build
```

## 🐛 Troubleshooting

### "python3: can't open file 'main.py': No such file"
**Problem:** AppImage ran from wrong location  
**Solution:** Make sure you have Python 3 installed:
```bash
python3 --version
sudo apt-get install python3  # Or your distro's package manager
```

### "ModuleNotFoundError: No module named 'PyQt5'"
**Problem:** PyQt5 is not installed  
**Solution:** Install it:
```bash
# Option 1: System package (recommended)
sudo apt-get install python3-pyqt5           # Ubuntu/Debian
sudo dnf install python3-PyQt5               # Fedora

# Option 2: pip
pip install PyQt5
```

### "No module named 'cv2' (OpenCV)"
**Problem:** OpenCV is not installed  
**Solution:**
```bash
sudo apt-get install python3-opencv          # Ubuntu/Debian
pip install opencv-python                    # Or via pip
```

### "No module named 'vlc'"
**Problem:** VLC Python bindings not installed  
**Solution:**
```bash
sudo apt-get install python3-vlc             # Ubuntu/Debian
pip install python-vlc                       # Or via pip
```

### AppImage won't run
**Problem:** Permission denied  
**Solution:** Make it executable:
```bash
chmod +x kenae_media_player_complete-x86_64.AppImage
./kenae_media_player_complete-x86_64.AppImage
```

### GUI doesn't appear
**Problem:** Display server issue  
**Solution:** Try with debug output:
```bash
QT_DEBUG_PLUGINS=1 ./kenae_media_player_complete-x86_64.AppImage 2>&1 | head -20
```

## 📝 Installation Verification

Check if everything works:

```bash
# 1. Make executable
chmod +x kenae_media_player_complete-x86_64.AppImage

# 2. Check Python
python3 --version

# 3. Check dependencies
python3 << 'EOF'
try:
    import PyQt5
    print("✓ PyQt5 installed")
except:
    print("✗ PyQt5 missing - install it!")

try:
    import cv2
    print("✓ OpenCV installed")
except:
    print("✗ OpenCV missing - install it!")

try:
    import vlc
    print("✓ VLC installed")
except:
    print("✗ VLC missing - install it!")
EOF

# 4. Try help
./kenae_media_player_complete-x86_64.AppImage --help
```

## 🎯 One-Liner Installation

**All-in-one installation command for your system:**

### Ubuntu/Debian
```bash
sudo apt-get install -y python3 python3-pyqt5 python3-opencv python3-vlc && \
chmod +x kenae_media_player_complete-x86_64.AppImage && \
./kenae_media_player_complete-x86_64.AppImage
```

### Fedora/RHEL
```bash
sudo dnf install -y python3 python3-PyQt5 python3-opencv vlc-python && \
chmod +x kenae_media_player_complete-x86_64.AppImage && \
./kenae_media_player_complete-x86_64.AppImage
```

### macOS
```bash
brew install python3 pyqt5 opencv vlc && \
chmod +x kenae_media_player_complete-x86_64.AppImage && \
./kenae_media_player_complete-x86_64.AppImage
```

## 📊 What's Different from Regular Installation

| Feature | AppImage | Installation |
|---------|----------|--------------|
| Download | ONE file (290 KB) | Full project |
| Setup | Immediate | Multiple steps |
| Portability | 100% portable | Tied to path |
| Space | 290 KB | ~500 MB+ |
| Distribution | Easy (1 file) | Complex |
| Updates | Replace 1 file | Re-clone |

## 🔗 Getting Help

If you encounter issues:

1. **Check embedded help:**
   ```bash
   ./kenae_media_player_complete-x86_64.AppImage --help
   ```

2. **View embedded docs:**
   ```bash
   ./kenae_media_player_complete-x86_64.AppImage --docs
   ```

3. **Extract and read files:**
   ```bash
   ./kenae_media_player_complete-x86_64.AppImage --appimage-extract
   cat squashfs-root/opt/kenae-player/docs/QUICK-START.md
   ```

4. **Run setup menu:**
   ```bash
   ./kenae_media_player_complete-x86_64.AppImage --install
   ```

## 📌 Summary

```
┌─────────────────────────────────────────────────────┐
│ 1. chmod +x kenae_media_player_complete-x86_64.AppImage
│ 2. Install system dependencies (if needed)
│ 3. ./kenae_media_player_complete-x86_64.AppImage
│                                                      │
│ That's all! Enjoy! 🎉                               │
└─────────────────────────────────────────────────────┘
```

---

**Questions?** Run: `./kenae_media_player_complete-x86_64.AppImage --help`
