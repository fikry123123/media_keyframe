# Keyframe Player for Linux

Aplikasi media player untuk pemutaran video, frame sequences, dan image dengan fitur timeline editing yang powerful.

## 🚀 Quick Start

### ⚡ Fastest Way (Use Setup Scripts)

**Choose your method:**

```bash
# Option 1: Interactive Menu (Recommended)
./setup-menu.sh

# Option 2: Complete Setup (Clone + Build + Install)
./setup.sh

# Option 3: Quick Install (Download + Install)
./quick-install.sh

# Option 4: Build Only (For Developers)
./build-appimage.sh
```

**See [QUICK-START.md](QUICK-START.md) for detailed guide!**

### 📥 Manual Installation

1. **Download AppImage** dari [GitHub Releases](https://github.com/fikry123123/media_keyframe/releases)

2. **Buat executable dan jalankan:**
   ```bash
   chmod +x kenae_media_player-x86_64.AppImage
   ./kenae_media_player-x86_64.AppImage
   ```

3. **Atau gunakan quick-install script:**
   ```bash
   chmod +x quick-install.sh
   ./quick-install.sh
   ```

## 📦 Installasi Desktop & App Launcher

Desktop integration dilakukan otomatis oleh setup scripts! Lihat [SCRIPTS.md](SCRIPTS.md) untuk detail.

## 💻 Development - Build from Source

### Requirements
- Python 3.12+
- PyQt5
- OpenCV
- VLC
- PyInstaller

### Installation

1. Clone repository:
   ```bash
   git clone https://github.com/fikry123123/media_keyframe.git
   cd media_keyframe
   ```

2. Create virtual environment:
   ```bash
   python3 -m venv venv_app
   source venv_app/bin/activate
   pip install -r requirements.txt
   ```

3. Run aplikasi:
   ```bash
   python main.py
   ```

### Build AppImage

1. Install build tools:
   ```bash
   pip install pyinstaller
   ```

2. Build AppImage (Linux only):
   ```bash
   # Run the build script or use PyInstaller directly
   pyinstaller main.py \
     --collect-all=PyQt5 \
     --collect-all=cv2 \
     --collect-all=numpy \
     --collect-all=vlc \
     --onefile \
     -n kenae_player \
     --windowed
   ```

## ✨ Features

- ▶️ Video playback dengan berbagai format
- 📽️ Frame sequence viewer (JPG, PNG, etc.)
- 🎬 Timeline editing dan navigation
- 🎨 Drawing tools pada frame
- 🔊 VLC audio support
- ⌨️ Keyboard shortcuts untuk playback control
- 🖱️ Drag & drop file support

## 🛠️ Requirements

### Runtime
- Linux x86_64
- GLIBC 2.29 atau lebih baru (Ubuntu 20.04+, Debian 10+)
- GTK3 libraries (biasanya sudah terinstall)

### Development
- Python 3.12
- Qt 5.15+
- OpenCV 4.5+
- VLC 3.0+

## 📚 Documentation

- **[QUICK-START.md](QUICK-START.md)** - One-page quick reference
- **[SCRIPTS.md](SCRIPTS.md)** - All setup scripts documentation  
- **[INSTALL.md](INSTALL.md)** - Detailed installation guide
- **[RELEASE.md](RELEASE.md)** - Release notes and versions

## 🐛 Troubleshooting

### AppImage tidak berjalan
```bash
# Cek permissions
chmod +x kenae_media_player-x86_64.AppImage

# Run dengan debug
./kenae_media_player-x86_64.AppImage --verbose
```

### Missing dependencies
```bash
# Install required system libraries
sudo apt-get install libgtk-3-0 libxkbcommon0 libdbus-1-3
```

## 📝 License

Lihat file [LICENSE](LICENSE)

## 🔗 Links

- [GitHub Repository](https://github.com/fikry123123/media_keyframe)
- [Releases](https://github.com/fikry123123/media_keyframe/releases)
- [Issues](https://github.com/fikry123123/media_keyframe/issues)
