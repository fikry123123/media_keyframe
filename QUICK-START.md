# QUICK REFERENCE GUIDE

## 🎯 CHOOSE YOUR PATH

### 👤 I want to install quickly (I have AppImage)
```bash
./quick-install.sh
```
✓ 2-3 minutes | ✓ No build needed | ✓ Desktop integration

### 🔧 I want to build from scratch
```bash
./setup.sh
```
✓ Complete setup | ✓ 15-20 minutes | ✓ Everything included

### 📋 I want to choose what to do
```bash
./setup-menu.sh
```
✓ Interactive menu | ✓ Guided steps | ✓ Multiple options

### 🛠️ I'm a developer (rebuild AppImage)
```bash
./build-appimage.sh
```
✓ Build only | ✓ 10-15 minutes | ✓ No repo clone needed

---

## 📥 DOWNLOAD APPIMAGE

```bash
# From releases
wget https://github.com/fikry123123/media_keyframe/releases/download/v1.0.0/kenae_media_player-x86_64.AppImage
chmod +x kenae_media_player-x86_64.AppImage

# Then install
./quick-install.sh
```

---

## 🚀 LAUNCH APPLICATION

```bash
# Command line
kenaeplayer
kenaeplayer video.mp4

# App menu
Search "Kenae Media Player"

# File manager
Right-click video → Open With → Kenae Media Player

# Desktop
Double-click shortcut (if created)
```

---

## 🔄 WORKFLOW

### First Time Users
```
1. Download scripts from GitHub
2. Run: ./setup-menu.sh
3. Choose option 1 (Complete Setup)
4. Wait for build
5. Launch from app menu
```

### Download Pre-built
```
1. Download AppImage from Releases
2. Run: ./quick-install.sh
3. Choose installation type
4. Done! Search in app menu
```

### Developers/Rebuild
```
1. Clone repo: git clone ...
2. Run: ./build-appimage.sh
3. Executable at: ./kenae_media_player-x86_64.AppImage
4. Distribute or install with: ./quick-install.sh
```

---

## ✅ VERIFICATION

Check if everything works:

```bash
# Find AppImage
ls -l kenae_media_player-x86_64.AppImage

# Run directly
./kenae_media_player-x86_64.AppImage

# Check if registered
ls ~/.local/share/applications/kenaeplayer.desktop

# Check command available
which kenaeplayer
```

---

## 🐛 QUICK FIXES

### App not in menu
```bash
update-desktop-database ~/.local/share/applications/
```

### Can't run scripts
```bash
chmod +x *.sh
```

### Python not found
```bash
sudo apt-get install python3.12 python3.12-venv
```

### Build failed
```bash
rm -rf build/ dist/ AppDir/
./build-appimage.sh
```

---

## 📍 FILE LOCATIONS

```
Repository:
  ./kenae_media_player-x86_64.AppImage

User (recommended):
  ~/.local/bin/kenaeplayer
  ~/.local/share/applications/kenaeplayer.desktop

System:
  /usr/local/bin/kenaeplayer
  /usr/local/share/applications/kenaeplayer.desktop

Desktop (optional):
  ~/Desktop/kenaeplayer.desktop
```

---

## 🔗 LINKS

- **GitHub**: https://github.com/fikry123123/media_keyframe
- **Releases**: https://github.com/fikry123123/media_keyframe/releases
- **Full Docs**: See SCRIPTS.md, INSTALL.md, README.md

---

## 💡 TIPS

✓ Use `setup-menu.sh` if unsure  
✓ AppImage is portable - copy anywhere  
✓ All scripts have built-in help  
✓ Desktop database updates automatically  
✓ Can install multiple times (overwrites OK)

---

## ⏱️ TIME ESTIMATES

| Script | Time | Best For |
|--------|------|----------|
| setup.sh | 15-20 min | First-time |
| quick-install.sh | 2-3 min | Pre-built |
| build-appimage.sh | 10-15 min | Dev/rebuild |
| setup-menu.sh | Varies | Guided |

---

Enjoy using Kenae Media Player! 🎬
