# Keyframe Player for Linux

## AppImage Compilation Instructions

1. Install the necessary dependencies:
   ```bash
   sudo apt-get install build-essential git cmake
   ```
2. Clone the repository:
   ```bash
   git clone https://github.com/Envyana/media_keyframe.git
   cd media_keyframe
   ```
3. Compile the project:
   ```bash
   mkdir build && cd build
   cmake ..
   make
   ```
4. Create an AppImage:
   ```bash
   ./appimagetool-x86_64.AppImage .
   ```
5. Your AppImage will be created in the current directory.
