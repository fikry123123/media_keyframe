#!/bin/bash

################################################################################
#            KENAE MEDIA PLAYER - COMPLETE SETUP MENU                         #
#            Download • Build • Install • Launch                               #
################################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

print_menu() {
    clear
    echo -e "${MAGENTA}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║        KENAE MEDIA PLAYER - SETUP MENU                         ║"
    echo "║     Download • Build AppImage • Install • Register              ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_menu

while true; do
    echo ""
    echo -e "${CYAN}What would you like to do?${NC}"
    echo ""
    echo -e "${GREEN}1)${NC} ${YELLOW}Complete Setup${NC} (Clone repo → Build → Install → Register)"
    echo -e "${GREEN}2)${NC} ${YELLOW}Quick Install${NC} (Install from existing AppImage)"
    echo -e "${GREEN}3)${NC} ${YELLOW}Build AppImage${NC} (Build from source only)"
    echo -e "${GREEN}4)${NC} ${YELLOW}Download AppImage${NC} (Download from GitHub Releases)"
    echo -e "${GREEN}5)${NC} ${YELLOW}View Instructions${NC} (Show detailed guide)"
    echo -e "${GREEN}6)${NC} ${YELLOW}Exit${NC}"
    echo ""
    read -p "Choose (1-6): " choice
    
    case $choice in
        1)
            echo ""
            echo -e "${BLUE}Running complete setup...${NC}"
            sleep 2
            if [ -f "setup.sh" ]; then
                bash setup.sh
            else
                echo -e "${RED}setup.sh not found${NC}"
            fi
            ;;
        2)
            echo ""
            echo -e "${BLUE}Running quick install...${NC}"
            sleep 2
            if [ -f "quick-install.sh" ]; then
                bash quick-install.sh
            else
                echo -e "${RED}quick-install.sh not found${NC}"
            fi
            ;;
        3)
            echo ""
            echo -e "${BLUE}Building AppImage...${NC}"
            sleep 2
            if [ -f "build-appimage.sh" ]; then
                bash build-appimage.sh
            else
                echo -e "${RED}build-appimage.sh not found${NC}"
            fi
            ;;
        4)
            echo ""
            echo -e "${BLUE}Downloading AppImage from GitHub...${NC}"
            echo ""
            echo "Select version to download:"
            echo "1) Latest release"
            echo "2) Enter custom version URL"
            read -p "Choose (1-2): " dl_choice
            
            case $dl_choice in
                1)
                    echo -e "${YELLOW}Downloading latest AppImage...${NC}"
                    # Get latest release download URL
                    DOWNLOAD_URL=$(curl -s https://api.github.com/repos/fikry123123/media_keyframe/releases/latest | grep "browser_download_url.*AppImage" | cut -d'"' -f4)
                    
                    if [ -z "$DOWNLOAD_URL" ]; then
                        echo -e "${RED}Could not find AppImage in latest release${NC}"
                        echo "Visit: https://github.com/fikry123123/media_keyframe/releases"
                    else
                        echo "URL: $DOWNLOAD_URL"
                        wget -O "kenae_media_player-x86_64.AppImage" "$DOWNLOAD_URL"
                        chmod +x "kenae_media_player-x86_64.AppImage"
                        echo -e "${GREEN}✓ Downloaded successfully!${NC}"
                    fi
                    ;;
                2)
                    read -p "Enter AppImage URL: " custom_url
                    wget -O "kenae_media_player-x86_64.AppImage" "$custom_url"
                    chmod +x "kenae_media_player-x86_64.AppImage"
                    echo -e "${GREEN}✓ Downloaded successfully!${NC}"
                    ;;
                *)
                    echo -e "${RED}Invalid choice${NC}"
                    ;;
            esac
            ;;
        5)
            print_menu
            echo -e "${CYAN}SETUP OPTIONS GUIDE${NC}"
            echo ""
            echo -e "${YELLOW}1. COMPLETE SETUP (Recommended for first-time users)${NC}"
            echo "   • Clones repository from GitHub"
            echo "   • Creates Python virtual environment"
            echo "   • Installs all dependencies"
            echo "   • Builds AppImage from source"
            echo "   • Registers app in system launcher"
            echo "   • Optional: Creates desktop shortcut"
            echo "   Time: ~10-15 minutes"
            echo ""
            
            echo -e "${YELLOW}2. QUICK INSTALL (For existing AppImage)${NC}"
            echo "   • Installs pre-built AppImage"
            echo "   • Registers in app launcher"
            echo "   • Creates desktop shortcut"
            echo "   • No compilation needed"
            echo "   Time: ~2 minutes"
            echo ""
            
            echo -e "${YELLOW}3. BUILD APPIMAGE (For developers)${NC}"
            echo "   • Builds AppImage from current directory"
            echo "   • Requires: Repository cloned"
            echo "   • Creates portable executable"
            echo "   • Ready for distribution"
            echo "   Time: ~5-10 minutes"
            echo ""
            
            echo -e "${YELLOW}4. DOWNLOAD AppImage (Easy method)${NC}"
            echo "   • Downloads pre-built AppImage from GitHub"
            echo "   • No building required"
            echo "   • Latest version available"
            echo "   Time: ~1 minute (depends on internet)"
            echo ""
            
            echo -e "${CYAN}FILE LOCATIONS${NC}"
            echo ""
            echo "After setup, files will be at:"
            echo "  • AppImage: ./kenae_media_player-x86_64.AppImage"
            echo "  • Installed: ~/.local/bin/kenaeplayer (user)"
            echo "  • System: /usr/local/bin/kenaeplayer (if system-wide)"
            echo "  • Desktop: ~/.local/share/applications/kenaeplayer.desktop"
            echo ""
            
            echo -e "${CYAN}LAUNCH OPTIONS${NC}"
            echo ""
            echo "  • Application Menu: Search 'Kenae Media Player'"
            echo "  • Command: kenaeplayer [file]"
            echo "  • File Manager: Right-click video → Open With"
            echo "  • Desktop Shortcut: Double-click (if created)"
            echo ""
            
            read -p "Press Enter to return to menu..."
            ;;
        6)
            echo -e "${BLUE}Exiting...${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice. Please try again.${NC}"
            sleep 1
            ;;
    esac
    
    read -p "Press Enter to continue..."
done
