# Studio Media Player

Media player yang dioptimalkan untuk melihat image sequence dan file video dengan antarmuka yang mudah digunakan.

## Fitur Utama

- **Image Sequence Viewer**: Pilih folder berisi banyak foto dan putar sebagai sequence
- **Frame Counter Persisten**: Tampilan frame counter yang selalu terlihat
- **Legibilitas Optimal**: Kontras warna dan ukuran font yang telah dioptimalkan
- **Kontrol Kecepatan**: Atur kecepatan playback untuk image sequence (1-30 FPS)
- **Keyboard Shortcuts**: Navigasi cepat menggunakan keyboard
- **Dark Theme**: Antarmuka gelap yang nyaman untuk mata

## Instalasi

1. **Pastikan Python 3.7+ terinstall**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Jalankan aplikasi:**
   ```bash
   python main.py
   ```

## Cara Penggunaan

### Membuka File
- **File → Open File** (Ctrl+O): Buka single file (video/image)
- **File → Open Image Sequence** (Ctrl+Shift+O): Pilih folder berisi image sequence

### Kontrol Playback
- **Play/Pause**: Tombol ▶/⏸ atau Space
- **Stop**: Tombol ⏹
- **Previous Frame**: Tombol ⏮ atau Left Arrow
- **Next Frame**: Tombol ⏭ atau Right Arrow
- **Speed Control**: Slider untuk mengatur FPS (1-30)

### Keyboard Shortcuts
- `Space`: Play/Pause
- `←` / `→`: Previous/Next frame
- `Home`: Go to first frame
- `End`: Go to last frame
- `Page Up`: Jump backward 10 frames
- `Page Down`: Jump forward 10 frames

### Timeline Navigation
- Klik dan drag timeline slider untuk navigasi cepat
- Lihat frame counter untuk posisi saat ini

## Format File Didukung

### Image Formats
- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- TIFF (.tiff, .tif)
- GIF (.gif)

### Video Formats
- MP4 (.mp4)
- AVI (.avi)
- MOV (.mov)
- MKV (.mkv)

## Fitur Image Sequence

Ketika memilih folder dengan image sequence:
- File diurutkan secara natural (menangani penomoran dengan benar)
- Playback speed dapat diatur 1-30 FPS
- Frame counter menampilkan posisi frame saat ini
- Timeline menampilkan total frame dalam sequence

## Tips Penggunaan

1. **Untuk Image Sequence**: Pastikan file dalam folder memiliki format penamaan yang konsisten (contoh: frame_001.jpg, frame_002.jpg, dst.)

2. **Performance**: Untuk folder dengan ribuan gambar, loading mungkin membutuhkan waktu sejenak

3. **Navigation**: Gunakan keyboard shortcuts untuk navigasi yang lebih cepat

## Troubleshooting

### Aplikasi tidak bisa dibuka
- Pastikan Python 3.7+ terinstall
- Install ulang dependencies: `pip install -r requirements.txt`

### Video tidak bisa diputar (MP4/MOV)
1. **Test video compatibility:**
   ```bash
   python test_video.py
   ```
   
2. **Install codec tambahan:**
   ```bash
   # Windows - install K-Lite Codec Pack
   # atau install opencv dengan codec lengkap:
   pip uninstall opencv-python
   pip install opencv-python-headless
   ```

3. **Cek format video:**
   - Pastikan codec didukung (H.264, MPEG-4)
   - Coba convert video ke format standar
   - Test dengan file video lain

### Image tidak muncul
- Pastikan format file didukung
- Cek apakah file tidak corrupt

### Playback tidak smooth
- Kurangi FPS menggunakan speed control
- Pastikan sistem memiliki RAM yang cukup
- Close aplikasi lain yang menggunakan banyak memory

## Requirements

- Python 3.7+
- PyQt5 5.15+
- OpenCV 4.5+
- NumPy 1.20+
