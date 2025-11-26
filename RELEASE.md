# Release Guide

## Cara Manual Upload AppImage ke GitHub Releases

### Prerequisites
- GitHub CLI (`gh`) installed
- Authenticated dengan GitHub

### Setup GitHub CLI (jika belum)
```bash
# Install gh
sudo apt-get install gh

# Login ke GitHub
gh auth login
```

### Upload AppImage

#### Cara 1: Menggunakan GitHub CLI (Recommended)

1. **Create release tag:**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **Create release dan upload AppImage:**
   ```bash
   gh release create v1.0.0 \
     --title "Kenae Media Player v1.0.0" \
     --notes "## Release Notes

   ### New Features
   - Feature 1
   - Feature 2
   
   ### Bug Fixes
   - Fix 1
   
   ### Download
   Download \`kenae_media_player-x86_64.AppImage\` for Linux" \
     kenae_media_player-x86_64.AppImage
   ```

3. **Or upload to existing release:**
   ```bash
   gh release upload v1.0.0 kenae_media_player-x86_64.AppImage
   ```

#### Cara 2: Menggunakan GitHub Web UI

1. Go to [Releases page](https://github.com/fikry123123/media_keyframe/releases)
2. Click "Create a new release"
3. Set version tag (e.g., `v1.0.0`)
4. Add release title and description
5. Drag & drop `kenae_media_player-x86_64.AppImage` file
6. Click "Publish release"

## Automatic Release dengan GitHub Actions

### Cara Kerja

Setelah setup, setiap kali Anda membuat git tag, GitHub Actions akan:

1. ✅ Build AppImage otomatis
2. ✅ Upload ke GitHub Releases
3. ✅ Publish release notes otomatis

### Bagaimana caranya:

1. **Create tag:**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **GitHub Actions akan:**
   - Build AppImage
   - Create release dengan file AppImage
   - Selesai! Users bisa download

## Version Scheme

Gunakan semantic versioning:
- `v1.0.0` - Major release
- `v1.0.1` - Bug fix
- `v1.1.0` - Minor feature
- `v2.0.0` - Breaking changes

## Checklist Release

Sebelum create release:
- [ ] Test aplikasi berjalan dengan baik
- [ ] Update version di files (jika ada)
- [ ] Commit semua changes
- [ ] Create git tag
- [ ] Push tag ke GitHub
- [ ] GitHub Actions akan handle build & release

## Troubleshooting

### GitHub Actions Failed
- Check workflow logs di GitHub Actions tab
- Lihat error message di build log
- Common issues:
  - Missing dependencies di requirements.txt
  - Python version mismatch
  - Missing appimagetool

### Manual Build jika Automated Failed

```bash
# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build executable
pyinstaller main.py \
  --collect-all=PyQt5 \
  --collect-all=cv2 \
  --collect-all=numpy \
  --collect-all=vlc \
  --onefile \
  -n kenae_player \
  --windowed

# Create AppImage manually
# See build-appimage.yml untuk script lengkap
```
