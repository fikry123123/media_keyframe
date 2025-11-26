#!/bin/bash

################################################################################
#        CREATE SELF-CONTAINED APPIMAGE WITH ALL SCRIPTS & DOCS              #
#        Single AppImage - No need for separate project files                 #
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║   CREATE SELF-CONTAINED APPIMAGE                               ║"
    echo "║   All Scripts & Docs in ONE AppImage File                       ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${YELLOW}➜ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

main() {
    print_header
    
    # Check requirements
    print_step "Checking requirements..."
    
    if [ ! -f "main.py" ]; then
        print_error "Not in repository directory (main.py not found)"
        exit 1
    fi
    
    print_success "All requirements met"
    
    # Create new AppDir for self-contained version
    print_step "Creating self-contained AppImage structure..."
    
    rm -rf AppDir-Complete
    mkdir -p AppDir-Complete/usr/bin
    mkdir -p AppDir-Complete/usr/share/applications
    mkdir -p AppDir-Complete/usr/share/doc/kenae-player
    mkdir -p AppDir-Complete/opt/kenae-player/scripts
    mkdir -p AppDir-Complete/opt/kenae-player/docs
    mkdir -p AppDir-Complete/opt/kenae-player/src
    
    # Copy PyInstaller binary (if it exists - has all deps bundled!)
    if [ -f "dist/kenae_player" ]; then
        print_step "Using PyInstaller binary with bundled dependencies..."
        cp dist/kenae_player AppDir-Complete/usr/bin/kenae_player
        chmod +x AppDir-Complete/usr/bin/kenae_player
    else
        # Create portable launcher script if binary not available
        print_step "Creating portable Python launcher..."
        cat > AppDir-Complete/usr/bin/kenae_player << 'LAUNCHER'
#!/bin/bash
# Portable launcher for kenae media player

APPDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export APPDIR

# Strategy: Use system Python with embedded source
PYTHON=""
if command -v python3 &> /dev/null; then
    PYTHON="python3"
elif command -v python &> /dev/null; then
    PYTHON="python"
elif [ -f "$APPDIR/venv_app/bin/python" ]; then
    PYTHON="$APPDIR/venv_app/bin/python"
else
    echo "Error: Python not found. Please install Python 3:"
    echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pyqt5 python3-opencv python3-vlc"
    echo "  Fedora: sudo dnf install python3 python3-PyQt5 python3-opencv vlc-python"
    exit 1
fi

# Check for required packages
"$PYTHON" -c "import PyQt5, cv2, vlc" 2>/dev/null || {
    echo "Error: Required packages not found. Please install:"
    echo "  pip install PyQt5 opencv-python python-vlc"
    exit 1
}

# Run main.py from AppImage directory
exec "$PYTHON" "$APPDIR/opt/kenae-player/main.py" "$@"
LAUNCHER
        chmod +x AppDir-Complete/usr/bin/kenae_player
    fi
    
    print_success "AppImage structure created"
    
    # Copy all scripts to /opt/kenae-player/scripts
    print_step "Adding setup scripts..."
    
    cp setup-menu.sh AppDir-Complete/opt/kenae-player/scripts/
    cp setup.sh AppDir-Complete/opt/kenae-player/scripts/
    cp quick-install.sh AppDir-Complete/opt/kenae-player/scripts/
    cp build-appimage.sh AppDir-Complete/opt/kenae-player/scripts/
    cp install.sh AppDir-Complete/opt/kenae-player/scripts/
    
    chmod +x AppDir-Complete/opt/kenae-player/scripts/*.sh
    
    print_success "Scripts added (setup-menu.sh, setup.sh, quick-install.sh, etc.)"
    
    # Copy application source code
    print_step "Adding application source code..."
    cp main.py AppDir-Complete/opt/kenae-player/
    cp main_window.py AppDir-Complete/opt/kenae-player/
    cp media_player.py AppDir-Complete/opt/kenae-player/
    cp media_controls.py AppDir-Complete/opt/kenae-player/
    cp timeline_widget.py AppDir-Complete/opt/kenae-player/
    cp drawing_toolbar.py AppDir-Complete/opt/kenae-player/
    cp sequence_capture.py AppDir-Complete/opt/kenae-player/
    
    # Copy src directory
    cp -r src/* AppDir-Complete/opt/kenae-player/src/ 2>/dev/null || true
    
    print_success "Application source code added"
    
    # Copy all documentation
    print_step "Adding documentation..."
    
    cp QUICK-START.md AppDir-Complete/opt/kenae-player/docs/
    cp SCRIPTS.md AppDir-Complete/opt/kenae-player/docs/
    cp INSTALL.md AppDir-Complete/opt/kenae-player/docs/
    cp RELEASE.md AppDir-Complete/opt/kenae-player/docs/
    cp README.md AppDir-Complete/opt/kenae-player/docs/
    cp FILES_SUMMARY.txt AppDir-Complete/opt/kenae-player/docs/
    cp DEVELOPMENT.md AppDir-Complete/opt/kenae-player/docs/
    cp kenaeplayer.desktop AppDir-Complete/opt/kenae-player/docs/
    
    print_success "Documentation added (all .md files included)"
    
    # Create a helper script to access resources inside AppImage
    print_step "Creating helper launcher script..."
    
    cat > AppDir-Complete/usr/bin/kenae-launcher << 'EOF'
#!/bin/bash
# Kenae Media Player - Launcher with embedded resources

APPDIR="${APPDIR:-.}"

# Show help if requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    cat << 'HELP'
╔══════════════════════════════════════════════════════════════════════╗
║              KENAE MEDIA PLAYER - SELF-CONTAINED                    ║
║                  All Scripts & Docs Included                        ║
╚══════════════════════════════════════════════════════════════════════╝

USAGE: kenae-launcher [OPTION]

OPTIONS:
  (no args)              Launch media player GUI
  --help, -h            Show this help
  --scripts             Show available scripts
  --docs               Show available documentation
  --install             Run setup-menu.sh (interactive installation)
  --quick-install       Run quick-install.sh (fast install)
  --build               Run build-appimage.sh (build from source)
  --setup               Run setup.sh (complete setup)
  video.mp4             Open video file in media player

EXAMPLES:
  kenae-launcher                    # Launch GUI
  kenae-launcher video.mp4          # Open video
  kenae-launcher --install          # Interactive setup
  kenae-launcher --quick-install    # Fast install
  kenae-launcher --scripts          # List available scripts
  kenae-launcher --docs             # List documentation

HELP
    exit 0
fi

# Show scripts
if [ "$1" = "--scripts" ]; then
    echo "Available scripts:"
    ls -1 "$APPDIR/opt/kenae-player/scripts/" | sed 's/^/  /'
    exit 0
fi

# Show documentation
if [ "$1" = "--docs" ]; then
    echo "Available documentation:"
    ls -1 "$APPDIR/opt/kenae-player/docs/" | sed 's/^/  /'
    exit 0
fi

# Run scripts
if [ "$1" = "--install" ]; then
    exec bash "$APPDIR/opt/kenae-player/scripts/setup-menu.sh"
fi

if [ "$1" = "--quick-install" ]; then
    exec bash "$APPDIR/opt/kenae-player/scripts/quick-install.sh"
fi

if [ "$1" = "--build" ]; then
    exec bash "$APPDIR/opt/kenae-player/scripts/build-appimage.sh"
fi

if [ "$1" = "--setup" ]; then
    exec bash "$APPDIR/opt/kenae-player/scripts/setup.sh"
fi

# Launch media player (with optional file)
export LD_LIBRARY_PATH="$APPDIR/usr/lib:$LD_LIBRARY_PATH"
export PATH="$APPDIR/usr/bin:$PATH"
exec "$APPDIR/usr/bin/kenae_player" "$@"
EOF
    
    chmod +x AppDir-Complete/usr/bin/kenae-launcher
    
    print_success "Helper launcher created"
    
    # Create AppRun
    print_step "Creating AppRun entry point..."
    
    cat > AppDir-Complete/AppRun << 'EOF'
#!/bin/bash
APPDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export APPDIR

# Fix library loading for PyInstaller bundle
export LD_LIBRARY_PATH="$APPDIR/usr/lib:$APPDIR/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
export PATH="$APPDIR/usr/bin:$PATH"

# Disable CV2 Qt to avoid conflicts with PyQt5
export QT_QPA_PLATFORM_PLUGIN_PATH=""

# Use default Qt plugin loader (will find xcb automatically)
unset QT_PLUGIN_PATH

# Check if help/scripts/docs requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ] || [ "$1" = "--scripts" ] || [ "$1" = "--docs" ]; then
    exec "$APPDIR/usr/bin/kenae-launcher" "$@"
fi

# Check if running script
if [ "$1" = "--install" ] || [ "$1" = "--quick-install" ] || [ "$1" = "--build" ] || [ "$1" = "--setup" ]; then
    exec "$APPDIR/usr/bin/kenae-launcher" "$@"
fi

# Launch media player
exec "$APPDIR/usr/bin/kenae_player" "$@"
EOF
    
    chmod +x AppDir-Complete/AppRun
    
    print_success "AppRun created"
    
    # Create desktop entry (both in standard location and AppDir root)
    mkdir -p AppDir-Complete/usr/share/applications
    cat > AppDir-Complete/kenae-player.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Kenae Media Player
Comment=Video and Image Frame Player with Timeline Editing
Exec=kenae_player %F
Icon=media-player
Terminal=false
Categories=AudioVideo;Video;Player;
Keywords=media;video;player;frame;sequence;
MimeType=video/mp4;video/x-matroska;video/quicktime;image/jpeg;image/png;
EOF
    
    # Also copy to standard location
    cp AppDir-Complete/kenae-player.desktop AppDir-Complete/usr/share/applications/
    
    print_success "Desktop entry created"
    
    # Create comprehensive README inside AppImage
    print_step "Creating embedded README..."
    
    cat > AppDir-Complete/usr/share/doc/kenae-player/README.txt << 'EOF'
╔══════════════════════════════════════════════════════════════════════╗
║           KENAE MEDIA PLAYER - SELF-CONTAINED APPIMAGE              ║
║                    All You Need In One File!                        ║
╚══════════════════════════════════════════════════════════════════════╝

QUICK START:

1. LAUNCH APPLICATION:
   ./kenae_media_player-x86_64.AppImage [video_file]

2. INTERACTIVE SETUP (First time users):
   ./kenae_media_player-x86_64.AppImage --install

3. QUICK INSTALL (If you want system integration):
   ./kenae_media_player-x86_64.AppImage --quick-install

4. VIEW DOCUMENTATION:
   ./kenae_media_player-x86_64.AppImage --docs

5. VIEW AVAILABLE SCRIPTS:
   ./kenae_media_player-x86_64.AppImage --scripts

═══════════════════════════════════════════════════════════════════════

USAGE:

Direct Usage (no installation needed):
  chmod +x kenae_media_player-x86_64.AppImage
  ./kenae_media_player-x86_64.AppImage              # Launch GUI
  ./kenae_media_player-x86_64.AppImage video.mp4   # Open video file
  ./kenae_media_player-x86_64.AppImage --help       # Show help

Install to System (optional):
  ./kenae_media_player-x86_64.AppImage --install    # Interactive menu
  # Then search "Kenae Media Player" in app launcher

Available Commands:
  --install        Interactive setup menu
  --quick-install  Fast installation
  --build          Build AppImage from source
  --setup          Complete setup from scratch
  --docs           List included documentation
  --scripts        List available scripts
  --help           Show this help

═══════════════════════════════════════════════════════════════════════

WHAT'S INCLUDED:

✓ Media Player Application
  - Video playback (mp4, mkv, mov, etc.)
  - Image/frame sequence viewer
  - Timeline editing
  - Drawing tools
  - VLC audio support

✓ Setup Scripts (ready to use):
  - setup-menu.sh       - Interactive menu
  - setup.sh            - Complete setup
  - quick-install.sh    - Fast installation
  - build-appimage.sh   - Build from source
  - install.sh          - Alternative installer

✓ Full Documentation:
  - QUICK-START.md      - Quick reference
  - SCRIPTS.md          - Scripts guide
  - INSTALL.md          - Installation guide
  - RELEASE.md          - Release procedures
  - README.md           - Full documentation
  - FILES_SUMMARY.txt   - File organization

═══════════════════════════════════════════════════════════════════════

SYSTEM INTEGRATION (OPTIONAL):

After running --install or --quick-install, you can:

1. Search "Kenae Media Player" in application menu
2. Launch from command line: kenaeplayer video.mp4
3. Right-click video in file manager → Open With
4. Use desktop shortcut (if created)

═══════════════════════════════════════════════════════════════════════

FEATURES:

✓ Completely portable (no installation needed)
✓ Run from anywhere (USB, network, home folder)
✓ Optional system integration
✓ Desktop launcher support
✓ File type associations
✓ Multiple launch methods
✓ Complete documentation included
✓ Setup scripts included

═══════════════════════════════════════════════════════════════════════

REQUIREMENTS:

✓ Linux x86_64
✓ GLIBC 2.29 or newer (Ubuntu 20.04+, Debian 10+)
✓ Qt5 libraries (usually pre-installed)
✓ 2GB RAM (recommended)

═══════════════════════════════════════════════════════════════════════

EXAMPLES:

Play video:
  ./kenae_media_player-x86_64.AppImage ~/Videos/movie.mp4

Interactive setup:
  ./kenae_media_player-x86_64.AppImage --install

Quick install (2-3 minutes):
  ./kenae_media_player-x86_64.AppImage --quick-install

Complete setup (15-20 minutes):
  ./kenae_media_player-x86_64.AppImage --setup

View help:
  ./kenae_media_player-x86_64.AppImage --help

═══════════════════════════════════════════════════════════════════════

SUPPORT:

For issues, suggestions, or more information:
  GitHub: https://github.com/fikry123123/media_keyframe
  Issues: https://github.com/fikry123123/media_keyframe/issues

═══════════════════════════════════════════════════════════════════════

Enjoy using Kenae Media Player! 🎬

EOF
    
    print_success "README created"
    
    # Download appimagetool if needed
    print_step "Checking appimagetool..."
    
    if [ ! -f "appimagetool.AppImage" ]; then
        print_step "Downloading appimagetool..."
        wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" -O appimagetool.AppImage
        chmod +x appimagetool.AppImage
        print_success "appimagetool downloaded"
    else
        print_success "appimagetool found"
    fi
    
    # Build AppImage
    print_step "Building self-contained AppImage..."
    echo "This may take a minute..."
    
    rm -f kenae_player-x86_64.AppImage
    ARCH=x86_64 ./appimagetool.AppImage AppDir-Complete kenae_player-x86_64.AppImage
    
    if [ -f "kenae_player-x86_64.AppImage" ]; then
        chmod +x kenae_player-x86_64.AppImage
        print_success "Self-contained AppImage built successfully!"
        echo ""
        ls -lh kenae_player-x86_64.AppImage
        echo ""
    else
        print_error "Failed to build AppImage"
        exit 1
    fi
    
    # Summary
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    print_success "Complete!"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Self-contained AppImage created!"
    echo ""
    echo "Usage:"
    echo "  chmod +x kenae_media_player_complete-x86_64.AppImage"
    echo "  ./kenae_media_player_complete-x86_64.AppImage              # Launch"
    echo "  ./kenae_media_player_complete-x86_64.AppImage --help       # Show help"
    echo "  ./kenae_media_player_complete-x86_64.AppImage --install    # Setup"
    echo "  ./kenae_media_player_complete-x86_64.AppImage video.mp4    # Open file"
    echo ""
    echo "Features:"
    echo "  ✓ Single file - no dependencies"
    echo "  ✓ All scripts included"
    echo "  ✓ All documentation included"
    echo "  ✓ Completely portable"
    echo "  ✓ Ready to distribute"
    echo ""
    echo "That's it! Just give this ONE AppImage file to users!"
    echo ""
}

main "$@"
