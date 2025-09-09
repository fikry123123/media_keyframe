# Studio Media Player

Aplikasi pemutar media profesional untuk kebutuhan studio yang mendukung berbagai format media dengan kemampuan playback normal dan frame-by-frame.

## 🎬 Fitur Utama

- ✅ **Multi-format Support**: JPG, PNG, EXR, MOV, MP4, MP3
- ✅ **Frame-by-frame Navigation**: Kontrol presisi untuk video editing
- ✅ **Professional UI**: Interface yang dioptimalkan untuk workflow studio
- ✅ **Keyboard Shortcuts**: Navigasi cepat dengan hotkeys
- ✅ **Timeline Scrubbing**: Navigasi timeline yang responsif
- ✅ **PyAV Backend**: Engine pemrosesan media yang powerful

## 🚀 Instalasi Cepat

1. **Clone atau download repository ini**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Jalankan aplikasi:**
   ```bash
   python main.py
   ```

## 📋 Persyaratan Sistem

- **Python**: 3.8 atau lebih tinggi
- **OS**: Windows, macOS, Linux
- **RAM**: Minimum 4GB (8GB recommended untuk video besar)
- **Storage**: 100MB space kosong

### Dependencies
- `PyQt5`: GUI framework
- `PyAV`: Media processing engine
- `OpenCV`: Image processing (termasuk support EXR)
- `Pillow`: Additional image format support
- `NumPy`: Array operations

## 📁 Struktur Proyek

```
media_keyframe/
├── main.py                 # Entry point aplikasi
├── requirements.txt        # Dependencies Python
├── create_demo_files.py    # Script untuk membuat file demo
├── demo_files/             # File demo untuk testing
├── src/
│   ├── ui/                 # User Interface components
│   │   ├── main_window.py  # Window utama aplikasi
│   │   ├── media_controls.py # Kontrol playback
│   │   └── timeline.py     # Timeline dan scrubber
│   ├── media/              # Media processing engine
│   │   ├── player.py       # Core media player (PyAV)
│   │   ├── formats.py      # Handler format yang didukung
│   │   └── frame_manager.py # Frame caching system
│   └── utils/              # Utility functions
│       └── helpers.py      # Helper functions
├── assets/icons/           # UI assets dan icons
└── .vscode/               # VS Code configuration
    ├── tasks.json         # Build tasks
    └── launch.json        # Debug configuration
```

## 🎮 Penggunaan

### Menjalankan Aplikasi
1. **Via Command Line:**
   ```bash
   python main.py
   ```

2. **Via VS Code:**
   - Buka VS Code di folder proyek
   - Tekan `F5` atau pilih "Run > Start Debugging"
   - Pilih "Studio Media Player" configuration

3. **Via Task:**
   - Tekan `Ctrl+Shift+P`
   - Ketik "Tasks: Run Task"
   - Pilih "Run Studio Media Player"

### Testing dengan File Demo
```bash
# Buat file demo untuk testing
python create_demo_files.py

# File demo akan dibuat di folder demo_files/
```

### Controls dan Shortcuts

| Action | Shortcut | Button |
|--------|----------|--------|
| Play/Pause | `Space` | ▶/⏸ |
| Stop | - | ⏹ |
| Previous Frame | `Left Arrow` | ⏮ |
| Next Frame | `Right Arrow` | ⏭ |
| Go to Start | `Home` | - |
| Go to End | `End` | - |
| Open File | `Ctrl+O` | File > Open |
| Fullscreen | `F11` | View > Fullscreen |

## 🎯 Fitur Lanjutan

### Frame-by-Frame Navigation
- Navigasi frame demi frame untuk video editing
- Timeline scrubbing yang presisi
- Frame counter dan FPS display
- Cache system untuk smooth playback

### Format Support
| Format | Type | Support Level |
|--------|------|---------------|
| JPG/JPEG | Image | ✅ Full |
| PNG | Image | ✅ Full |
| EXR | Image | ✅ OpenCV |
| MOV | Video | ✅ PyAV |
| MP4 | Video | ✅ PyAV |
| MP3 | Audio | ✅ Visualization |

### Professional Features
- **Timeline scrubbing** untuk navigasi cepat
- **Volume control** untuk audio
- **Frame caching** untuk performa optimal
- **Keyboard shortcuts** untuk workflow cepat
- **Fullscreen mode** untuk review

## 🔧 Development

### Debug Mode
Untuk development dan troubleshooting:
```bash
# Set debug environment
export QT_LOGGING_RULES="*.debug=true"
python main.py
```

Atau gunakan debug configuration di VS Code.

### Menambah Format Baru
1. Update `MediaFormats` class di `src/media/formats.py`
2. Implement loader di `MediaPlayer` class
3. Test dengan file sample

### Architecture
- **PyQt5**: UI framework dengan signal/slot system
- **PyAV**: Media decoding dan processing
- **OpenCV**: Image processing (terutama EXR)
- **PIL/Pillow**: Additional image format support

## 🚨 Troubleshooting

### Common Issues
1. **"Import could not be resolved"**
   - Pastikan PYTHONPATH di-set ke workspace folder
   - Install semua dependencies: `pip install -r requirements.txt`

2. **"Failed to load video"**
   - Install ffmpeg untuk codec tambahan
   - Check format video didukung

3. **"Application crashes on startup"**
   - Check Python version (3.8+)
   - Pastikan PyQt5 ter-install dengan benar

4. **"Slow performance"**
   - Kurangi cache size di FrameManager
   - Close aplikasi lain yang memory-intensive

### System Requirements Check
```bash
# Check Python version
python --version

# Check installed packages
pip list | grep -E "(PyQt5|av|opencv|Pillow|numpy)"

# Test PyQt5
python -c "from PyQt5.QtWidgets import QApplication; print('PyQt5 OK')"

# Test PyAV
python -c "import av; print('PyAV OK')"
```

## 📈 Roadmap

### Planned Features
- [ ] Timeline thumbnails
- [ ] Multi-format export
- [ ] Batch processing
- [ ] Plugin system
- [ ] Color correction tools
- [ ] Audio waveform display
- [ ] Markers dan annotations

### Performance Improvements
- [ ] GPU acceleration
- [ ] Multi-threading untuk decode
- [ ] Adaptive quality untuk large files
- [ ] Background preloading

## 🤝 Contributing

1. Fork repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push ke branch: `git push origin feature/amazing-feature`
5. Submit Pull Request

## 📄 License

Proyek ini dibuat untuk kebutuhan studio profesional. Silakan gunakan dan modifikasi sesuai kebutuhan.

## 📞 Support

Untuk bug reports dan feature requests, silakan gunakan GitHub Issues atau hubungi tim development.

---

**Studio Media Player** - Professional media playback untuk studio workflow yang efisien.
