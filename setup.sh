#!/bin/bash

################################################################################
#                   KENAE MEDIA PLAYER - COMPLETE SETUP                       #
#            Download, Build, Install, dan Register ke App Launcher           #
################################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
REPO_URL="https://github.com/fikry123123/media_keyframe.git"
REPO_DIR="media_keyframe"
PYTHON_VERSION="3.12"

# Functions
print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║   KENAE MEDIA PLAYER - COMPLETE SETUP SCRIPT                   ║"
    echo "║   Download • Build • Install • Register                          ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}➜ $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_dependencies() {
    print_step "Checking dependencies..."
    
    local missing_deps=()
    
    # Check required commands
    for cmd in git python3 pip wget; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done
    
    # Check PyInstaller (pip package)
    if ! python3 -c "import PyInstaller" 2>/dev/null; then
        print_info "PyInstaller not installed (will install later)"
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        echo ""
        echo "Install with:"
        echo "  Ubuntu/Debian:"
        echo "    sudo apt-get update"
        echo "    sudo apt-get install -y git python3 python3-pip python3-venv"
        echo ""
        echo "  Fedora/RHEL:"
        echo "    sudo dnf install -y git python3 python3-pip"
        echo ""
        echo "  Arch:"
        echo "    sudo pacman -S git python pip"
        exit 1
    fi
    
    print_success "All dependencies found"
}

download_repo() {
    print_step "Downloading repository..."
    
    if [ -d "$REPO_DIR" ]; then
        print_info "Repository already exists at $REPO_DIR"
        read -p "Update existing repository? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cd "$REPO_DIR"
            git pull origin main
            cd ..
        fi
    else
        git clone "$REPO_URL" "$REPO_DIR"
        print_success "Repository cloned"
    fi
}

setup_venv() {
    print_step "Setting up Python virtual environment..."
    
    cd "$REPO_DIR"
    
    if [ ! -d "venv_app" ]; then
        python3 -m venv venv_app
        print_success "Virtual environment created"
    else
        print_info "Virtual environment already exists"
    fi
    
    # Activate venv
    source venv_app/bin/activate
    
    # Install dependencies
    print_info "Installing Python dependencies..."
    pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt
    print_success "Python dependencies installed"
    
    # Install build tools
    print_info "Installing build tools..."
    pip install pyinstaller
    
    cd ..
}

build_appimage() {
    print_step "Building AppImage..."
    
    cd "$REPO_DIR"
    
    # Activate venv
    source venv_app/bin/activate
    
    # Check if appimagetool exists
    if [ ! -f "appimagetool.AppImage" ]; then
        print_info "Downloading appimagetool..."
        wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" -O appimagetool.AppImage
        chmod +x appimagetool.AppImage
        print_success "appimagetool downloaded"
    fi
    
    # Build with PyInstaller
    print_info "Building executable with PyInstaller..."
    pyinstaller main.py \
        --collect-all=PyQt5 \
        --collect-all=cv2 \
        --collect-all=numpy \
        --collect-all=vlc \
        --onefile \
        -n kenae_player \
        --windowed
    
    print_success "Executable built"
    
    # Create AppDir structure
    print_info "Creating AppImage structure..."
    mkdir -p AppDir/usr/bin
    
    cp dist/kenae_player AppDir/usr/bin/
    
    # Create wrapper script
    cat > AppDir/usr/bin/kenae_player_launcher.py << 'LAUNCHER_EOF'
#!/usr/bin/env python3
import os
import sys
import subprocess

def find_main_py():
    possible_paths = [
        os.path.expanduser("~/media_keyframe/main.py"),
        "/home/*/media_keyframe/main.py",
        os.path.join(os.getcwd(), "main.py"),
        os.path.join(os.path.dirname(__file__), "../../../main.py"),
    ]
    for path in possible_paths:
        if os.path.isfile(path):
            return path
    return None

def find_python():
    possible_paths = [
        os.path.expanduser("~/media_keyframe/venv_app/bin/python"),
        "/usr/bin/python3",
        "python3",
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

if __name__ == "__main__":
    main_py = find_main_py()
    python_exe = find_python()
    
    if not main_py or not python_exe:
        sys.exit(1)
    
    os.execv(python_exe, [python_exe, main_py] + sys.argv[1:])
LAUNCHER_EOF
    chmod +x AppDir/usr/bin/kenae_player_launcher.py
    
    # Create AppRun
    cat > AppDir/AppRun << 'APPRUN_EOF'
#!/bin/bash
APPDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export LD_LIBRARY_PATH="$APPDIR/usr/lib:$LD_LIBRARY_PATH"
export PATH="$APPDIR/usr/bin:$PATH"
exec "$APPDIR/usr/bin/kenae_player" "$@"
APPRUN_EOF
    chmod +x AppDir/AppRun
    
    # Create desktop entry
    mkdir -p AppDir/usr/share/applications
    cat > AppDir/usr/share/applications/kenae-player.desktop << 'DESKTOP_EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Kenae Media Player
Comment=Video and Image Frame Player
Exec=kenae_player %F
Icon=/home/fikry/keyframe_player_linux/70e4bfea-516b-416c-9595-c1ba494bdaf6.jpeg
Terminal=false
Categories=AudioVideo;Video;Player;
MimeType=video/mp4;video/x-matroska;video/quicktime;image/jpeg;image/png;
DESKTOP_EOF
    
    print_success "AppImage structure created"
    
    # Build AppImage
    print_info "Building AppImage..."
    ARCH=x86_64 ./appimagetool.AppImage AppDir kenae_media_player-x86_64.AppImage
    
    if [ -f "kenae_media_player-x86_64.AppImage" ]; then
        chmod +x kenae_media_player-x86_64.AppImage
        print_success "AppImage built successfully!"
        ls -lh kenae_media_player-x86_64.AppImage
    else
        print_error "Failed to build AppImage"
        exit 1
    fi
    
    cd ..
}

register_app() {
    print_step "Registering application..."
    
    cd "$REPO_DIR"
    
    # Create desktop file
    cat > kenaeplayer.desktop << 'DESKTOP_EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Kenae Media Player
Comment=Video and Image Frame Player with Timeline Editing
Exec=APPIMAGE_PATH %F
Icon=media-player-core
Terminal=false
Categories=AudioVideo;Video;Player;
Keywords=media;video;player;frame;sequence;
StartupNotify=true
MimeType=video/mp4;video/x-matroska;video/quicktime;image/jpeg;image/png;
DESKTOP_EOF
    
    # Update Exec path in desktop file
    APPIMAGE_FULL_PATH="$(pwd)/kenae_media_player-x86_64.AppImage"
    sed -i "s|APPIMAGE_PATH|$APPIMAGE_FULL_PATH|g" kenaeplayer.desktop
    
    # Install to user applications
    mkdir -p ~/.local/share/applications
    cp kenaeplayer.desktop ~/.local/share/applications/
    update-desktop-database ~/.local/share/applications/ 2>/dev/null || true
    
    print_success "Application registered in app launcher"
    
    # Optional: Add to Desktop
    read -p "Add desktop shortcut? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp kenaeplayer.desktop ~/Desktop/
        chmod +x ~/Desktop/kenaeplayer.desktop
        print_success "Desktop shortcut created"
    fi
    
    cd ..
}

test_launch() {
    print_step "Testing application..."
    
    cd "$REPO_DIR"
    
    print_info "Launching Kenae Media Player..."
    if ./kenae_media_player-x86_64.AppImage &
        APPID=$!
        sleep 3
        if ps -p $APPID > /dev/null; then
            print_success "Application started successfully (PID: $APPID)"
            print_info "Close the application window to continue..."
            wait $APPID 2>/dev/null || true
        else
            print_error "Application failed to start"
        fi
    fi
    
    cd ..
}

main() {
    print_header
    
    # Check system
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        print_error "This script only works on Linux"
        exit 1
    fi
    
    print_step "Setup Configuration"
    echo "Repository: $REPO_URL"
    echo "Directory: $REPO_DIR"
    echo "Python: $PYTHON_VERSION"
    echo ""
    
    read -p "Continue with setup? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    
    # Execute setup steps
    check_dependencies
    download_repo
    setup_venv
    build_appimage
    register_app
    
    # Optional: Test launch
    read -p "Test launch application now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        test_launch
    fi
    
    print_header
    print_success "Setup complete!"
    echo ""
    echo "Kenae Media Player is ready to use!"
    echo ""
    echo "Launch options:"
    echo "  • Search 'Kenae Media Player' in application menu"
    echo "  • Run: $REPO_DIR/kenae_media_player-x86_64.AppImage"
    echo "  • Double-click desktop shortcut (if created)"
    echo ""
    echo "Open files with:"
    echo "  • Right-click video/image in file manager"
    echo "  • Select 'Open With' → 'Kenae Media Player'"
    echo ""
}

main "$@"
