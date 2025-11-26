#!/bin/bash
# Launcher untuk Kenae Media Player AppImage
# Mengatasi masalah Qt/Wayland/CV2 conflict

# Tentukan lokasi AppImage
APPIMAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPIMAGE="$APPIMAGE_DIR/kenae_player-x86_64.AppImage"

# Perbaikan 1: Force XCB (X11) alih-alih Wayland
export QT_QPA_PLATFORM=xcb

# Perbaikan 2: Hapus XDG_SESSION_TYPE agar Qt tidak coba Wayland
unset XDG_SESSION_TYPE

# Perbaikan 3: Disable CV2 built-in Qt untuk hindari double-loading
export QT_QPA_PLATFORM_PLUGIN_PATH=""

# Perbaikan 4: Prioritaskan system libraries daripada bundled ones
export LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu/qt5/plugins:$LD_LIBRARY_PATH"

# VLC Configuration
export VLC_PLUGIN_PATH="/usr/lib/x86_64-linux-gnu/vlc/plugins"
export VLC_DATA_PATH="/usr/share/vlc"

# Perbaikan 5: Jalankan AppImage
exec "$APPIMAGE" "$@"
