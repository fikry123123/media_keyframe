# Complete Self-Contained AppImage

## 📦 What is This?

`kenae_media_player_complete-x86_64.AppImage` adalah **ONE FILE** yang berisi:
- ✅ Media player application
- ✅ Semua setup scripts (5 files)
- ✅ Semua dokumentasi (6+ files)
- ✅ Helper launcher untuk akses resource

**Total: 214 KB** - Cukup untuk dibagikan ke siapa saja!

## 🚀 Quick Start

### 1. **Jalankan Media Player**
```bash
./kenae_media_player_complete-x86_64.AppImage
```

### 2. **Lihat Help**
```bash
./kenae_media_player_complete-x86_64.AppImage --help
```

### 3. **Buka File Video**
```bash
./kenae_media_player_complete-x86_64.AppImage ~/video.mp4
```

## 📚 Embedded Commands

### Help & Documentation
```bash
./kenae_media_player_complete-x86_64.AppImage --help      # Tampilkan help
./kenae_media_player_complete-x86_64.AppImage --docs      # Daftar dokumentasi
./kenae_media_player_complete-x86_64.AppImage --scripts   # Daftar scripts
```

### Setup & Installation (Extract to ~/.kenae-player)
```bash
./kenae_media_player_complete-x86_64.AppImage --install       # Menu interaktif
./kenae_media_player_complete-x86_64.AppImage --quick-install # Install cepat
./kenae_media_player_complete-x86_64.AppImage --setup         # Setup lengkap
./kenae_media_player_complete-x86_64.AppImage --build         # Build dari source
```

## 📂 What's Included

### Media Player
- PyQt5 GUI
- Video playback dengan OpenCV
- VLC audio support
- Timeline editor
- Drawing tools
- Drag & drop support

### Setup Scripts (5 files)
1. **setup-menu.sh** - Interactive menu
2. **setup.sh** - Complete setup (clone, venv, build)
3. **quick-install.sh** - Fast install
4. **build-appimage.sh** - Build AppImage
5. **install.sh** - Alternative installer

### Documentation (6+ files)
1. **QUICK-START.md** - One-page reference
2. **SCRIPTS.md** - Scripts documentation
3. **INSTALL.md** - Installation guide
4. **RELEASE.md** - Release procedures
5. **README.md** - Project overview
6. **kenaeplayer.desktop** - Desktop entry
7. **FILES_SUMMARY.txt** - File reference

## 🎯 Usage Scenarios

### Scenario 1: Just Want to Watch Videos
```bash
# Jalankan saja
./kenae_media_player_complete-x86_64.AppImage

# Atau buka file langsung
./kenae_media_player_complete-x86_64.AppImage /path/to/video.mp4
```

### Scenario 2: Install to Desktop & System
```bash
# Run installer
./kenae_media_player_complete-x86_64.AppImage --install

# Pilih option:
# 1. User installation (~/.kenae-player)
# 2. System installation (/opt/kenae-player)
```

### Scenario 3: Want Full Source Code
```bash
# Extract all scripts and build from source
./kenae_media_player_complete-x86_64.AppImage --setup

# Ini akan:
# 1. Extract scripts
# 2. Clone repository
# 3. Create virtual environment
# 4. Install dependencies
# 5. Build AppImage
```

### Scenario 4: Share With Others
```bash
# Just give them ONE file!
# kenae_media_player_complete-x86_64.AppImage

# Mereka bisa langsung jalankan:
./kenae_media_player_complete-x86_64.AppImage
```

## 💻 System Requirements

- **OS**: Linux x86_64 (Ubuntu 20.04+, Debian 10+, Fedora 32+)
- **Glibc**: 2.29 or newer (biasanya sudah ada)
- **GTK3**: Usually pre-installed
- **RAM**: 256 MB minimum
- **Disk**: 300 MB for installation (media player only), more for source

## 🔧 Advanced Usage

### View Included Documentation
```bash
# List all docs
./kenae_media_player_complete-x86_64.AppImage --docs

# View specific doc (extract first)
./kenae_media_player_complete-x86_64.AppImage --extract
cat squashfs-root/opt/kenae-player/docs/QUICK-START.md
```

### Extract All Files
```bash
./kenae_media_player_complete-x86_64.AppImage --appimage-extract
```

This creates `squashfs-root/` directory with all files.

### Run Setup Script Directly
```bash
# Extract first
./kenae_media_player_complete-x86_64.AppImage --appimage-extract

# Run script
bash squashfs-root/opt/kenae-player/scripts/setup.sh
```

## 📊 File Size Comparison

| Version | Size | Contains |
|---------|------|----------|
| `kenae_media_player-x86_64.AppImage` | 271 KB | Media player only |
| `kenae_media_player_complete-x86_64.AppImage` | 214 KB | Player + scripts + docs |

**Catatan:** Complete version lebih kecil karena tidak semua file perlu di-include!

## 🤝 Distribution

### Share on GitHub Releases
```bash
# Upload to: https://github.com/<user>/media_keyframe/releases
# File: kenae_media_player_complete-x86_64.AppImage
```

### Share Direct Download Link
```bash
# Anyone can download dan jalankan:
wget https://example.com/kenae_media_player_complete-x86_64.AppImage
chmod +x kenae_media_player_complete-x86_64.AppImage
./kenae_media_player_complete-x86_64.AppImage
```

### Email or File Sharing
```bash
# Just attach ONE file!
# Users bisa langsung jalankan:
# 1. chmod +x file.AppImage
# 2. ./file.AppImage
```

## 🐛 Troubleshooting

### AppImage tidak berjalan
```bash
# Make it executable
chmod +x kenae_media_player_complete-x86_64.AppImage

# Check dependencies
ldd ./kenae_media_player_complete-x86_64.AppImage

# Run with debug
./kenae_media_player_complete-x86_64.AppImage --verbose
```

### Extract if needed
```bash
./kenae_media_player_complete-x86_64.AppImage --appimage-extract
cd squashfs-root
./AppRun  # Launch from extracted
```

## 📝 Summary

| Aspek | Detail |
|-------|--------|
| **Format** | AppImage (single executable) |
| **Size** | 214 KB |
| **Portability** | 100% portable, no installation needed |
| **Contents** | Media player + 5 scripts + 6 docs |
| **Setup** | Minimal system requirements |
| **Distribution** | Easy - just ONE file |
| **Updates** | Can extract scripts and rebuild |

---

**Sekarang tinggal berikan 1 file ke users! 🎉**
