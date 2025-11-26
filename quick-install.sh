#!/bin/bash

################################################################################
#              KENAE MEDIA PLAYER - QUICK INSTALL                             #
#              Install dari AppImage yang sudah ada                            #
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
    echo "║   KENAE MEDIA PLAYER - QUICK INSTALL                           ║"
    echo "║   AppImage • Desktop Integration • App Launcher                  ║"
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
    
    # Check Linux
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        print_error "This script only works on Linux"
        exit 1
    fi
    
    # Find AppImage
    print_step "Looking for AppImage..."
    
    APPIMAGE=""
    if [ -f "./kenae_media_player-x86_64.AppImage" ]; then
        APPIMAGE="./kenae_media_player-x86_64.AppImage"
    elif [ -f "kenae_media_player-x86_64.AppImage" ]; then
        APPIMAGE="kenae_media_player-x86_64.AppImage"
    else
        print_error "AppImage not found in current directory"
        echo ""
        echo "Download from: https://github.com/fikry123123/media_keyframe/releases"
        exit 1
    fi
    
    APPIMAGE="$(cd "$(dirname "$APPIMAGE")" && pwd)/$(basename "$APPIMAGE")"
    chmod +x "$APPIMAGE"
    print_success "AppImage found: $APPIMAGE"
    
    # Installation type
    echo ""
    echo "Select installation type:"
    echo "1) User-local (recommended, no sudo needed)"
    echo "2) System-wide (requires sudo)"
    echo "3) Just desktop shortcut"
    read -p "Choose (1-3): " install_type
    
    case $install_type in
        1)
            print_step "Installing to user applications..."
            INSTALL_DIR="$HOME/.local/bin"
            DESKTOP_DIR="$HOME/.local/share/applications"
            mkdir -p "$INSTALL_DIR" "$DESKTOP_DIR"
            cp "$APPIMAGE" "$INSTALL_DIR/kenaeplayer"
            chmod +x "$INSTALL_DIR/kenaeplayer"
            print_success "Installed to $INSTALL_DIR/kenaeplayer"
            EXEC_PATH="$INSTALL_DIR/kenaeplayer"
            ;;
        2)
            print_step "Installing system-wide..."
            sudo mkdir -p /usr/local/bin /usr/local/share/applications
            sudo cp "$APPIMAGE" /usr/local/bin/kenaeplayer
            sudo chmod +x /usr/local/bin/kenaeplayer
            print_success "Installed to /usr/local/bin/kenaeplayer"
            EXEC_PATH="/usr/local/bin/kenaeplayer"
            DESKTOP_DIR="/usr/local/share/applications"
            ;;
        3)
            print_step "Setting up desktop shortcut only..."
            EXEC_PATH="$APPIMAGE"
            DESKTOP_DIR="$HOME/.local/share/applications"
            mkdir -p "$DESKTOP_DIR"
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
    
    # Create desktop file
    print_step "Creating desktop entry..."
    
    mkdir -p "$DESKTOP_DIR"
    
    cat > "/tmp/kenaeplayer.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Kenae Media Player
Comment=Video and Image Frame Player with Timeline Editing
Exec=$EXEC_PATH %F
Icon=media-player-core
Terminal=false
Categories=AudioVideo;Video;Player;
Keywords=media;video;player;frame;sequence;
StartupNotify=true
MimeType=video/mp4;video/x-matroska;video/quicktime;image/jpeg;image/png;
EOF
    
    if [ "$install_type" = "2" ]; then
        sudo cp "/tmp/kenaeplayer.desktop" "$DESKTOP_DIR/kenaeplayer.desktop"
        sudo update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
    else
        cp "/tmp/kenaeplayer.desktop" "$DESKTOP_DIR/kenaeplayer.desktop"
        update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
    fi
    
    print_success "Desktop entry created"
    
    # Desktop shortcut
    echo ""
    read -p "Create desktop shortcut? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp "$DESKTOP_DIR/kenaeplayer.desktop" ~/Desktop/
        chmod +x ~/Desktop/kenaeplayer.desktop
        print_success "Desktop shortcut created at ~/Desktop/kenaeplayer.desktop"
    fi
    
    # Summary
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    print_success "Installation complete!"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Launch Kenae Media Player:"
    echo "  • Search 'Kenae' in application menu"
    echo "  • Run: kenaeplayer [file.mp4]"
    echo "  • Right-click video in file manager → Open With"
    if [ "$install_type" = "3" ]; then
        echo "  • Run: $EXEC_PATH"
    fi
    echo ""
}

main "$@"
