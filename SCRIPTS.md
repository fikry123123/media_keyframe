# Setup & Installation Scripts

Panduan lengkap untuk download, build, install, dan menjalankan Kenae Media Player.

## 🚀 Quick Start

### Option 1: Interactive Menu (Recommended)
```bash
chmod +x setup-menu.sh
./setup-menu.sh
```

Pilih dari menu yang muncul sesuai kebutuhan Anda.

### Option 2: Complete Setup (Clone + Build + Install)
```bash
chmod +x setup.sh
./setup.sh
```

### Option 3: Quick Install (Dari AppImage yang sudah ada)
```bash
chmod +x quick-install.sh
./quick-install.sh
```

---

## 📝 Daftar Script

### 1. **setup-menu.sh** - Interactive Setup Menu
Menu interaktif untuk memilih setup yang diinginkan.

**Features:**
- 🎯 Guided menu interface
- 📋 Multiple installation options
- 📚 Built-in help & instructions
- 🔄 Easy navigation

**Kapan digunakan:** Untuk user yang ingin menu interaktif

**Cara jalankan:**
```bash
./setup-menu.sh
```

### 2. **setup.sh** - Complete Setup
Setup lengkap dari awal: clone repo → install dependencies → build AppImage → register

**Features:**
- ⬇️ Clone repository dari GitHub
- 🐍 Setup Python virtual environment
- 📦 Install semua dependencies
- 🔨 Build AppImage dengan PyInstaller
- ✅ Register di app launcher
- 🧪 Optional: Test launch aplikasi

**Kapan digunakan:** First-time installation, development setup

**Requirements:**
- Git
- Python 3.12+
- wget (untuk download appimagetool)
- Koneksi internet

**Cara jalankan:**
```bash
./setup.sh
```

**What it does:**
```
1. Check dependencies (git, python3, pip, wget)
2. Download repository
3. Create virtual environment
4. Install Python packages
5. Build AppImage
6. Register in system launcher
7. Test application (optional)
```

**Estimasi waktu:** 15-20 menit (tergantung koneksi internet & kecepatan komputer)

### 3. **quick-install.sh** - Quick Install
Install AppImage yang sudah ada ke system dan register di app launcher.

**Features:**
- 🚀 Cepat tanpa build
- 👤 User-local atau system-wide
- 🖥️ Desktop shortcut optional
- ✨ App launcher integration

**Kapan digunakan:** 
- Download AppImage sudah ada
- Ingin cepat tanpa build

**Requirements:**
- AppImage file (`kenae_media_player-x86_64.AppImage`)
- `update-desktop-database` (biasanya sudah ada)

**Cara jalankan:**
```bash
# Download dulu dari GitHub Releases
wget https://github.com/fikry123123/media_keyframe/releases/download/vX.X.X/kenae_media_player-x86_64.AppImage

# Kemudian install
./quick-install.sh
```

**Installation Options:**
1. User-local: `~/.local/bin/` (recommended)
2. System-wide: `/usr/local/bin/` (needs sudo)
3. Desktop shortcut only

**Estimasi waktu:** 2-3 menit

### 4. **build-appimage.sh** - Build AppImage Only
Build AppImage dari source code yang sudah ada di repository.

**Features:**
- 🔨 PyInstaller compilation
- 📦 AppImage creation
- 🧪 Test launch optional
- 📊 Build status output

**Kapan digunakan:**
- Sudah clone repository
- Ingin rebuild AppImage
- Untuk developers

**Requirements:**
- Sudah di directory repository
- Python 3.12+
- pip
- Koneksi internet (download appimagetool)

**Cara jalankan:**
```bash
# Harus di repo directory
cd media_keyframe

# Build
./build-appimage.sh
```

**What it does:**
```
1. Check repository structure
2. Setup/activate virtual environment
3. Install Python dependencies
4. Download appimagetool
5. Clean previous builds
6. Build executable with PyInstaller
7. Create AppImage structure
8. Build AppImage
9. Test run (optional)
```

**Estimasi waktu:** 10-15 menit

### 5. **install.sh** - Original Install Script
Script instalasi original yang interaktif.

**Features:**
- 🔧 Setup wizard
- 📍 Multiple installation paths
- 🎯 Smart path detection

**Cara jalankan:**
```bash
./install.sh
```

---

## 🎯 Usage Scenarios

### Scenario 1: Fresh Installation dari GitHub

```bash
# Download & setup lengkap
git clone https://github.com/fikry123123/media_keyframe.git
cd media_keyframe
./setup.sh
```

### Scenario 2: Download AppImage + Install

```bash
# Download AppImage dari releases
wget https://github.com/fikry123123/media_keyframe/releases/download/v1.0.0/kenae_media_player-x86_64.AppImage
chmod +x kenae_media_player-x86_64.AppImage

# Install
./quick-install.sh
```

### Scenario 3: Menu Interaktif

```bash
./setup-menu.sh
# Pilih option dari menu
```

### Scenario 4: Development - Rebuild AppImage

```bash
cd media_keyframe
./build-appimage.sh
./quick-install.sh  # Re-install jika sudah ada
```

---

## 💻 System Requirements

### Minimum
- Linux x86_64
- Python 3.12+
- 2GB RAM
- 500MB disk space
- GLIBC 2.29+

### Recommended
- Ubuntu 20.04+ / Debian 10+ / Fedora 32+
- Python 3.12+
- 4GB RAM
- 1GB disk space
- Koneksi internet (untuk download)

---

## ⚙️ Installation Methods Comparison

| Method | Time | Setup | Complexity | Best For |
|--------|------|-------|-----------|----------|
| setup.sh | 15-20 min | Full | Medium | First-time, Development |
| quick-install.sh | 2-3 min | Minimal | Low | Quick, Pre-built |
| build-appimage.sh | 10-15 min | Build only | Medium | Rebuild, Distribution |
| setup-menu.sh | Varies | Guided | Low | Menu users |

---

## 🔍 Troubleshooting

### Script tidak bisa dijalankan
```bash
# Make executable
chmod +x *.sh

# Jalankan dengan bash
bash setup.sh
```

### Python tidak ditemukan
```bash
# Install Python 3.12
sudo apt-get install python3.12 python3.12-venv

# Verify
python3 --version
```

### Dependencies missing
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    git python3 python3-pip python3-venv \
    libgtk-3-0 libxkbcommon0 libdbus-1-3

# Fedora
sudo dnf install -y \
    git python3 python3-pip \
    gtk3 libxkbcommon dbus-libs
```

### AppImage build failed
```bash
# Check logs
cat /tmp/appimage_test.log

# Clean and retry
rm -rf build/ dist/ AppDir/
./build-appimage.sh
```

### App tidak muncul di launcher
```bash
# Update desktop database
update-desktop-database ~/.local/share/applications/

# Atau
sudo update-desktop-database /usr/local/share/applications/
```

---

## 📦 File Locations

Setelah installation, files akan berada di:

```
Repository root:
  kenae_media_player-x86_64.AppImage  (built AppImage)
  venv_app/                           (Python environment)
  AppDir/                             (AppImage structure)

User local (user installation):
  ~/.local/bin/kenaeplayer            (executable)
  ~/.local/share/applications/        (desktop file)
  ~/Desktop/kenaeplayer.desktop       (shortcut - optional)

System wide (system installation):
  /usr/local/bin/kenaeplayer          (executable)
  /usr/local/share/applications/      (desktop file)
```

---

## 🚀 Launch Application

Setelah installation, launch dengan:

```bash
# Command line
kenaeplayer
kenaeplayer /path/to/video.mp4

# Application menu
# Search "Kenae Media Player"

# File manager
# Right-click video → Open With → Kenae Media Player

# Desktop shortcut
# Double-click (if created)
```

---

## 📚 Additional Scripts

### For Distribution

**Create package untuk distro:**

```bash
# Debian package
./build-appimage.sh  # Build AppImage dulu
# Kemudian gunakan checkinstall atau fpm

# AppImage (already built)
./kenae_media_player-x86_64.AppImage

# Flatpak
# Bisa dibuat dari AppImage

# Snap
# Bisa dibuat dari AppImage
```

---

## 🔗 Useful Links

- [GitHub Repository](https://github.com/fikry123123/media_keyframe)
- [GitHub Releases](https://github.com/fikry123123/media_keyframe/releases)
- [Issues](https://github.com/fikry123123/media_keyframe/issues)
- [Main README](README.md)
- [Installation Guide](INSTALL.md)
- [Release Notes](RELEASE.md)

---

## ✨ Tips & Tricks

### Tip 1: Make AppImage Portable
```bash
# Copy AppImage ke USB drive
cp kenae_media_player-x86_64.AppImage /mnt/usb/
# Run dari USB
/mnt/usb/kenae_media_player-x86_64.AppImage
```

### Tip 2: Create Custom Shortcut
```bash
# Edit desktop file
nano ~/.local/share/applications/kenaeplayer.desktop

# Add custom icon path
Icon=/path/to/custom/icon.png
```

### Tip 3: Batch Process Videos
```bash
# Convert videos with Kenae
for file in *.mp4; do
    kenaeplayer "$file" &
done
```

### Tip 4: Update AppImage
```bash
# Download latest from releases
wget https://github.com/fikry123123/media_keyframe/releases/download/vX.X.X/kenae_media_player-x86_64.AppImage
chmod +x kenae_media_player-x86_64.AppImage
```

---

## 🐛 Report Issues

Jika ada masalah, lapor di:
https://github.com/fikry123123/media_keyframe/issues

Sertakan:
- Error message
- Output dari script
- System info (`uname -a`)
- Script yang digunakan
