#!/bin/bash

################################################################################
#           KENAE MEDIA PLAYER - BUILD APPIMAGE                               #
#           Build AppImage dari repository yang sudah ada                      #
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
    echo "║   KENAE MEDIA PLAYER - BUILD APPIMAGE                          ║"
    echo "║   PyInstaller • AppImage • Ready to Distribute                   ║"
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

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

main() {
    print_header
    
    # Check dependencies
    print_step "Checking dependencies..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 not found"
        exit 1
    fi
    
    if ! command -v git &> /dev/null; then
        print_error "Git not found"
        exit 1
    fi
    
    print_success "Dependencies found"
    
    # Check if in repo directory
    if [ ! -f "main.py" ] || [ ! -f "requirements.txt" ]; then
        print_error "Not in media_keyframe directory"
        echo "Please run this script from the repository root directory"
        exit 1
    fi
    
    print_success "Repository detected"
    
    # Setup virtual environment if needed
    print_step "Setting up Python environment..."
    
    if [ ! -d "venv_app" ]; then
        python3 -m venv venv_app
        print_success "Virtual environment created"
    else
        print_info "Using existing virtual environment"
    fi
    
    source venv_app/bin/activate
    
    # Install dependencies
    print_step "Installing Python dependencies..."
    pip install --upgrade pip setuptools wheel > /dev/null 2>&1
    pip install -r requirements.txt > /dev/null 2>&1
    pip install pyinstaller > /dev/null 2>&1
    print_success "Dependencies installed"
    
    # Download appimagetool
    print_step "Checking appimagetool..."
    
    if [ ! -f "appimagetool.AppImage" ]; then
        print_info "Downloading appimagetool..."
        wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" -O appimagetool.AppImage
        chmod +x appimagetool.AppImage
        print_success "appimagetool downloaded"
    else
        print_info "appimagetool found"
    fi
    
    # Clean previous builds
    print_step "Cleaning previous builds..."
    rm -rf build/ dist/ *.spec AppDir/ 2>/dev/null || true
    print_success "Cleaned"
    
    # Build with PyInstaller
    print_step "Building executable with PyInstaller..."
    echo "This may take several minutes..."
    echo ""
    
    pyinstaller main.py \
        --collect-all=PyQt5 \
        --collect-all=cv2 \
        --collect-all=numpy \
        --collect-all=vlc \
        --onefile \
        -n kenae_player \
        --windowed \
        --hidden-import=cv2 \
        --hidden-import=numpy
    
    if [ ! -f "dist/kenae_player" ]; then
        print_error "PyInstaller build failed"
        exit 1
    fi
    
    print_success "Executable built"
    ls -lh dist/kenae_player
    
    # Create AppImage directory structure
    print_step "Creating AppImage structure..."
    
    mkdir -p AppDir/usr/bin
    cp dist/kenae_player AppDir/usr/bin/
    
    # Create AppRun script
    cat > AppDir/AppRun << 'EOF'
#!/bin/bash
APPDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export LD_LIBRARY_PATH="$APPDIR/usr/lib:$LD_LIBRARY_PATH"
export PATH="$APPDIR/usr/bin:$PATH"
exec "$APPDIR/usr/bin/kenae_player" "$@"
EOF
    chmod +x AppDir/AppRun
    
    # Create desktop entry
    mkdir -p AppDir/usr/share/applications
    cat > AppDir/usr/share/applications/kenae-player.desktop << 'EOF'
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
    
    print_success "AppImage structure created"
    
    # Build AppImage
    print_step "Building AppImage..."
    echo "This creates a portable executable..."
    echo ""
    
    ARCH=x86_64 ./appimagetool.AppImage AppDir kenae_media_player-x86_64.AppImage
    
    if [ -f "kenae_media_player-x86_64.AppImage" ]; then
        chmod +x kenae_media_player-x86_64.AppImage
        print_success "AppImage built successfully!"
        echo ""
        ls -lh kenae_media_player-x86_64.AppImage
        echo ""
        print_success "Ready to distribute!"
    else
        print_error "Failed to build AppImage"
        exit 1
    fi
    
    # Test run
    echo ""
    read -p "Test run AppImage? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_step "Launching AppImage..."
        if ./kenae_media_player-x86_64.AppImage > /tmp/appimage_test.log 2>&1 &
            PID=$!
            sleep 3
            if ps -p $PID > /dev/null; then
                print_success "Application started successfully!"
                print_info "Close the application to continue..."
                wait $PID 2>/dev/null || true
            else
                print_error "Application failed to start"
                print_info "Check log: cat /tmp/appimage_test.log"
            fi
        fi
    fi
    
    # Summary
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    print_success "Build complete!"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "AppImage location:"
    echo "  $(pwd)/kenae_media_player-x86_64.AppImage"
    echo ""
    echo "Next steps:"
    echo "  1. Share or upload the AppImage"
    echo "  2. Users can download and run it directly"
    echo "  3. Or use quick-install.sh for system integration"
    echo ""
    echo "Run: ./quick-install.sh   (to install and register)"
    echo ""
}

main "$@"
