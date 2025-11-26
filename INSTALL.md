# Installation Guide

## Quick Install - Desktop Integration

### Method 1: Automatic Desktop Integration (Linux Desktop Environments)

```bash
# Clone the repository
git clone https://github.com/fikry123123/media_keyframe.git
cd media_keyframe

# Download latest AppImage from Releases
wget https://github.com/fikry123123/media_keyframe/releases/download/v1.0.0/kenae_media_player-x86_64.AppImage
chmod +x kenae_media_player-x86_64.AppImage

# Install to applications menu
mkdir -p ~/.local/share/applications
cp kenaeplayer.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications/

# Optional: Add to Desktop
cp kenaeplayer.desktop ~/Desktop/
chmod +x ~/Desktop/kenaeplayer.desktop
```

### Method 2: Install to System-wide Applications (requires sudo)

```bash
sudo mkdir -p /usr/local/share/applications
sudo cp kenaeplayer.desktop /usr/local/share/applications/
sudo update-desktop-database /usr/local/share/applications/

# Copy AppImage to system bin
sudo cp kenae_media_player-x86_64.AppImage /usr/local/bin/kenaeplayer
sudo chmod +x /usr/local/bin/kenaeplayer
```

### Method 3: AppImage Direct Run (No Installation)

```bash
# Just make it executable and run
chmod +x kenae_media_player-x86_64.AppImage
./kenae_media_player-x86_64.AppImage
```

## Launch Application

After installation, you can launch in several ways:

1. **Application Menu/Grid**
   - Click "Activities" or application menu
   - Search "Kenae Media Player"
   - Click to launch

2. **Command Line**
   ```bash
   # If copied to /usr/local/bin
   kenaeplayer
   
   # Or run AppImage directly
   /home/fikry/keyframe_player_linux/kenae_media_player-x86_64.AppImage
   ```

3. **Desktop Shortcut**
   - Double-click on desktop shortcut if installed

4. **File Manager**
   - Right-click video/image file → Open With → Kenae Media Player

## Desktop Integration Details

The `kenaeplayer.desktop` file enables:

- ✅ **Application Launcher Integration** - Shows in app menu/grid
- ✅ **Keyboard Search** - Search from app drawer
- ✅ **File Type Association** - Open media files with Kenae Player
- ✅ **System Menu** - Proper categorization (AudioVideo/Player)
- ✅ **Desktop Shortcut** - Double-click to launch

## Supported File Types

After installation, you can open these file types directly:

- **Video**: MP4, MKV, MOV, WebM, AVI, FLV
- **Images**: JPG, PNG, GIF, BMP
- **Sequences**: Frame sequences (frame_001.jpg, frame_002.jpg, etc.)

## Uninstall

```bash
# Remove from user applications menu
rm ~/.local/share/applications/kenaeplayer.desktop
update-desktop-database ~/.local/share/applications/

# Remove from Desktop
rm ~/Desktop/kenaeplayer.desktop

# Remove AppImage
rm ~/keyframe_player_linux/kenae_media_player-x86_64.AppImage

# If installed to system
sudo rm /usr/local/bin/kenaeplayer
sudo rm /usr/local/share/applications/kenaeplayer.desktop
sudo update-desktop-database /usr/local/share/applications/
```

## Troubleshooting

### Application doesn't appear in launcher
```bash
# Rebuild desktop database
update-desktop-database ~/.local/share/applications/

# Restart desktop environment or logout/login
```

### Can't open video files
```bash
# Make sure file permissions are correct
chmod +x kenae_media_player-x86_64.AppImage

# Run from terminal to see error messages
./kenae_media_player-x86_64.AppImage /path/to/file.mp4
```

### Desktop file is invalid
```bash
# Validate desktop file
desktop-file-validate kenaeplayer.desktop

# If errors, check format:
# - Every field must end with newline
# - No extra spaces
# - Proper key=value format
```

## Development Installation

To install from source for development:

```bash
git clone https://github.com/fikry123123/media_keyframe.git
cd media_keyframe

# Create virtual environment
python3 -m venv venv_app
source venv_app/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run directly
python main.py

# Create .desktop file for development
cp kenaeplayer.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications/
```

## System Requirements

- **OS**: Linux (Ubuntu 20.04+, Debian 10+, Fedora 32+, etc.)
- **Architecture**: x86_64
- **GLIBC**: 2.29 or newer
- **Display Server**: X11 or Wayland
- **RAM**: 2GB minimum (4GB recommended)
- **Disk**: 500MB for installation

## Performance Notes

- AppImage is self-contained (266KB)
- No additional installation needed
- Fast startup time
- Can run from USB drive
- Works in sandboxed environments

## See Also

- [README.md](README.md) - Main project documentation
- [RELEASE.md](RELEASE.md) - Release notes and version history
- [GitHub Releases](https://github.com/fikry123123/media_keyframe/releases) - Download latest version
