# Studio Media Player - Development Guide

## Arsitektur Aplikasi

### Struktur Proyek
```
media_keyframe/
├── main.py                 # Entry point aplikasi
├── requirements.txt        # Dependencies
├── src/
│   ├── ui/                 # User Interface components
│   │   ├── main_window.py  # Window utama
│   │   ├── media_controls.py # Kontrol playback
│   │   └── timeline.py     # Timeline dan scrubber
│   ├── media/              # Media processing
│   │   ├── player.py       # Core media player
│   │   ├── formats.py      # Format handlers
│   │   └── frame_manager.py # Frame caching
│   └── utils/              # Utilities
│       └── helpers.py      # Helper functions
└── assets/icons/           # UI assets
```

### Komponen Utama

#### 1. MediaPlayer (src/media/player.py)
- Core engine menggunakan PyAV
- Menangani loading dan decoding media
- Frame-by-frame navigation
- Signal emission untuk UI updates

#### 2. MainWindow (src/ui/main_window.py)
- Window utama aplikasi
- Layout management
- Menu dan keyboard shortcuts
- Koordinasi antar komponen

#### 3. MediaControls (src/ui/media_controls.py)
- Play/pause/stop controls
- Frame navigation buttons
- Volume control
- Time display

#### 4. Timeline (src/ui/timeline.py)
- Scrubbing interface
- Position indicator
- Frame information display

## Menambahkan Format Baru

### 1. Update MediaFormats class:
```python
# src/media/formats.py
SUPPORTED_NEW_FORMATS = {'.new_ext'}
ALL_SUPPORTED_FORMATS = ... | SUPPORTED_NEW_FORMATS
```

### 2. Implement loader di MediaPlayer:
```python
# src/media/player.py
def loadNewFormat(self, file_path):
    # Implementation for new format
    pass
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Space` | Play/Pause |
| `Left Arrow` | Previous Frame |
| `Right Arrow` | Next Frame |
| `Home` | Go to Start |
| `End` | Go to End |
| `Ctrl+O` | Open File |
| `F11` | Fullscreen |

## Signal Flow

```
MediaPlayer → MainWindow → UI Components
     ↓             ↓           ↓
frameReady → updateDisplay → Display
positionChanged → updateTimeline → Timeline
durationChanged → setDuration → Controls
```

## Frame Management

- Cache sistem untuk smooth playback
- LRU eviction untuk memory management
- Background preloading untuk adjacent frames

## Troubleshooting

### Common Issues:
1. **ImportError**: Pastikan semua dependencies ter-install
2. **Codec Error**: Install ffmpeg untuk format video tambahan
3. **Memory Issues**: Kurangi cache size di FrameManager

### Debug Mode:
Set environment variable untuk debug:
```bash
export QT_LOGGING_RULES="*.debug=true"
python main.py
```

## Contributing

1. Fork repository
2. Create feature branch
3. Implement changes dengan tests
4. Submit pull request

## Performance Optimization

- Frame caching untuk smooth scrubbing
- Lazy loading untuk large files
- GPU acceleration (future enhancement)
- Multi-threading untuk background operations
