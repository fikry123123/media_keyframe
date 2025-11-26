#!/bin/bash
# Wrapper untuk Kenae Media Player - Mengatasi masalah Qt/wayland dan VLC

# Tentukan direktori script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Perbaikan 1: Force XCB (X11) alih-alih Wayland yang bermasalah
export QT_QPA_PLATFORM=xcb

# Perbaikan 2: Unset XDG_SESSION_TYPE agar Qt tidak mencoba Wayland
unset XDG_SESSION_TYPE

# Perbaikan 3: Disable CV2 built-in Qt untuk hindari konflik
export QT_QPA_PLATFORM_PLUGIN_PATH=""

# Perbaikan 4: Set library path ke system Qt libraries (bukan PyInstaller's cv2 Qt)
export LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"

# VLC Configuration
export VLC_PLUGIN_PATH="/usr/lib/x86_64-linux-gnu/vlc/plugins"
export VLC_DATA_PATH="/usr/share/vlc"

# Perbaikan 5: Jalankan aplikasi
exec python3 "$SCRIPT_DIR/main.py" "$@"
