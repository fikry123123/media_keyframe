#!/bin/bash
# Kenae Media Player - Easy Installation Script

set -e

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║       Kenae Media Player - Installation Script                 ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo -e "${RED}✗ Error: This script only works on Linux${NC}"
    exit 1
fi

# Get installation type
echo "Select installation type:"
echo "1) User-local (recommended, no sudo needed)"
echo "2) System-wide (requires sudo)"
echo "3) Custom path"
read -p "Choose (1-3): " install_type

case $install_type in
    1)
        echo -e "${YELLOW}Installing for current user...${NC}"
        INSTALL_DIR="$HOME/.local/bin"
        DESKTOP_DIR="$HOME/.local/share/applications"
        NEED_SUDO=false
        ;;
    2)
        echo -e "${YELLOW}Installing system-wide (requires sudo)...${NC}"
        INSTALL_DIR="/usr/local/bin"
        DESKTOP_DIR="/usr/local/share/applications"
        NEED_SUDO=true
        ;;
    3)
        read -p "Enter installation directory: " INSTALL_DIR
        DESKTOP_DIR="$INSTALL_DIR/../share/applications"
        NEED_SUDO=false
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# Find AppImage file
APPIMAGE_FILE=""
if [ -f "./kenae_media_player-x86_64.AppImage" ]; then
    APPIMAGE_FILE="./kenae_media_player-x86_64.AppImage"
elif [ -f "kenae_media_player-x86_64.AppImage" ]; then
    APPIMAGE_FILE="kenae_media_player-x86_64.AppImage"
else
    echo -e "${YELLOW}AppImage not found in current directory.${NC}"
    read -p "Enter path to AppImage file: " APPIMAGE_FILE
    if [ ! -f "$APPIMAGE_FILE" ]; then
        echo -e "${RED}✗ File not found: $APPIMAGE_FILE${NC}"
        exit 1
    fi
fi

# Convert to absolute path
APPIMAGE_FILE="$(cd "$(dirname "$APPIMAGE_FILE")" && pwd)/$(basename "$APPIMAGE_FILE")"

echo ""
echo "Installation settings:"
echo "  AppImage: $APPIMAGE_FILE"
echo "  Install to: $INSTALL_DIR"
echo "  Desktop file: $DESKTOP_DIR"
echo ""

# Create directories
if [ "$NEED_SUDO" = true ]; then
    sudo mkdir -p "$INSTALL_DIR" "$DESKTOP_DIR"
    sudo cp "$APPIMAGE_FILE" "$INSTALL_DIR/kenaeplayer"
    sudo chmod +x "$INSTALL_DIR/kenaeplayer"
else
    mkdir -p "$INSTALL_DIR" "$DESKTOP_DIR"
    cp "$APPIMAGE_FILE" "$INSTALL_DIR/kenaeplayer"
    chmod +x "$INSTALL_DIR/kenaeplayer"
fi

# Create or update desktop file
DESKTOP_CONTENT="[Desktop Entry]
Version=1.0
Type=Application
Name=Kenae Media Player
Comment=Video and Image Frame Player with Timeline Editing
Exec=$INSTALL_DIR/kenaeplayer %F
Icon=/home/fikry/keyframe_player_linux/70e4bfea-516b-416c-9595-c1ba494bdaf6.jpeg
Terminal=false
Categories=AudioVideo;Video;Player;
Keywords=media;video;player;frame;sequence;
StartupNotify=true
MimeType=video/mp4;video/x-matroska;video/quicktime;image/jpeg;image/png;"

if [ "$NEED_SUDO" = true ]; then
    echo "$DESKTOP_CONTENT" | sudo tee "$DESKTOP_DIR/kenaeplayer.desktop" > /dev/null
    sudo update-desktop-database "$DESKTOP_DIR"
else
    echo "$DESKTOP_CONTENT" > "$DESKTOP_DIR/kenaeplayer.desktop"
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

# Add to PATH if custom or user
if [ "$install_type" = "1" ]; then
    export PATH="$INSTALL_DIR:$PATH"
fi

echo ""
echo -e "${GREEN}✓ Installation complete!${NC}"
echo ""
echo "You can now launch Kenae Media Player by:"
echo "  • Searching 'Kenae Media Player' in your application menu"
echo "  • Running: kenaeplayer"
echo "  • Running: $INSTALL_DIR/kenaeplayer"
echo ""

# Optional: Add to Desktop
read -p "Add desktop shortcut? (y/n): " add_desktop
if [ "$add_desktop" = "y" ] || [ "$add_desktop" = "Y" ]; then
    cp "$DESKTOP_DIR/kenaeplayer.desktop" "$HOME/Desktop/kenaeplayer.desktop"
    chmod +x "$HOME/Desktop/kenaeplayer.desktop"
    echo -e "${GREEN}✓ Desktop shortcut created at ~/Desktop/kenaeplayer.desktop${NC}"
fi

echo ""
echo -e "${GREEN}Setup finished! Enjoy using Kenae Media Player 🎬${NC}"
