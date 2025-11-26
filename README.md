# Keyframe Player for Linux

Aplikasi media player untuk pemutaran video, frame sequences, dan image dengan fitur timeline editing yang powerful.

## 🚀 Quick Start - Download AppImage

### Cara Tercepat (Download Pre-built)

1. **Download AppImage** dari [GitHub Releases](https://github.com/fikry123123/media_keyframe/releases)

2. **Buat executable dan jalankan:**
   ```bash
   chmod +x kenae_media_player-x86_64.AppImage
   ./kenae_media_player-x86_64.AppImage
   ```

3. **Atau copy ke bin folder:**
   ```bash
   chmod +x kenae_media_player-x86_64.AppImage
   sudo cp kenae_media_player-x86_64.AppImage /usr/local/bin/kenaeplayer
   
   # Jalankan dari mana saja
   kenaeplayer
   ```

## 📦 Installasi Desktop Shortcut

Buat file shortcut di desktop:
```bash
cat > ~/.local/share/applications/kenaeplayer.desktop << 'DESKTOP'
[Desktop Entry]
Version=1.0
Type=Application
Name=Kenae Media Player
Comment=Video and Image Frame Player
Exec=/path/to/kenae_media_player-x86_64.AppImage
Terminal=false
Categories=AudioVideo;Player;
Icon=media-player
DESKTOP

# Update desktop database
update-desktop-database ~/.local/share/applications/
```

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

## 📋 Project Structure

```
.
├── main.py                 # Entry point aplikasi
├── main_window.py          # Main UI window
├── media_player.py         # Media playback widget
├── media_controls.py       # Playback controls
├── drawing_toolbar.py      # Drawing tools
├── timeline_widget.py      # Timeline widget
├── requirements.txt        # Python dependencies
├── src/
│   ├── media/             # Media handling modules
│   ├── ui/                # UI components
│   └── utils/             # Utility functions
└── demo_files/            # Demo media files
```

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
