#!/bin/bash
set -e

echo "=== CBRE Break APK Build Script ==="
echo "Dieses Skript baut die APK auf einem Rechner mit >=8 GB RAM."
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' || echo "unknown")
echo "Python Version: $PYTHON_VERSION"

# Check if flet is installed
if ! python3 -c "import flet" 2>/dev/null; then
    echo "Installing flet==0.86.5..."
    pip install --break-system-packages flet==0.86.5 flet-cli==0.86.5
else
    echo "flet bereits installiert: $(python3 -c 'import flet; print(flet.__version__)')"
fi

# Check Flutter
if ! command -v flutter &> /dev/null; then
    echo "Flutter nicht gefunden. Bitte Flutter SDK installieren: https://docs.flutter.dev/get-started/install"
    echo "Empfohlene Version: 3.44.8"
    exit 1
else
    echo "Flutter gefunden: $(flutter --version | head -1)"
fi

# Check Java
if ! command -v java &> /dev/null; then
    echo "Java JDK 17 nicht gefunden. Bitte installieren."
    exit 1
else
    echo "Java gefunden: $(java -version 2>&1 | head -1)"
fi

# Check Android SDK
ANDROID_HOME="${ANDROID_HOME:-$HOME/Android/sdk}"
if [ ! -d "$ANDROID_HOME" ]; then
    echo "Android SDK nicht gefunden unter $ANDROID_HOME"
    echo "Bitte Android Studio oder Command-line Tools installieren."
    exit 1
else
    echo "Android SDK gefunden: $ANDROID_HOME"
fi

# Accept Android licenses
echo ""
echo "Akzeptiere Android Lizenzen..."
export ANDROID_HOME="$ANDROID_HOME"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
yes | flutter doctor --android-licenses 2>/dev/null || true

# Ensure required SDK components
echo ""
echo "Installiere erforderliche SDK-Komponenten..."
yes | sdkmanager "platforms;android-36" "build-tools;36.0.0" "ndk;28.2.13676358" "platform-tools" 2>/dev/null || true

# Build APK
echo ""
echo "=== Starte APK Build ==="
echo "Build-Befehl:"
echo "flet build apk --yes --bundle-id de.cbre.breakapp --product 'CBRE Break' --build-version 1.0 --build-number 1 --org de.cbre --project CBRE_BREAK ."
echo ""

export GRADLE_OPTS="-Xmx2G -XX:MaxMetaspaceSize=512m -XX:ReservedCodeCacheSize=256m -Dorg.gradle.daemon=false"
export ANDROID_HOME="$ANDROID_HOME"
export ANDROID_SDK_ROOT="$ANDROID_HOME"

flet build apk --yes \
  --bundle-id de.cbre.breakapp \
  --product "CBRE Break" \
  --build-version 1.0 \
  --build-number 1 \
  --org de.cbre \
  --project CBRE_BREAK .

echo ""
echo "=== Build abgeschlossen ==="
APK_PATH="build/flutter/android/app/release/app-release.apk"
if [ -f "$APK_PATH" ]; then
    echo "APK erfolgreich erstellt: $APK_PATH"
    echo "Größe: $(du -h "$APK_PATH" | cut -f1)"
else
    echo "FEHLER: APK wurde nicht erstellt. Siehe Logs oben."
    exit 1
fi
