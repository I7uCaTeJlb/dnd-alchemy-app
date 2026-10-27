#!/bin/bash
set -e

APP_PATH="${1:-dist/Alchemy-macOS.app}"
CERT_NAME="Alchemy Developer"
KEYCHAIN_PATH="$RUNNER_TEMP/build.keychain"
P12_PASSWORD="${MACOS_P12_PASSWORD:-Alchemy2026!}"

echo "=== macOS Code Signing ==="
echo "Signing: $APP_PATH"

security create-keychain -p "$P12_PASSWORD" "$KEYCHAIN_PATH"
security default-keychain -s "$KEYCHAIN_PATH"
security unlock-keychain -p "$P12_PASSWORD" "$KEYCHAIN_PATH"
security set-keychain-settings "$KEYCHAIN_PATH"

if [ -n "$MACOS_P12_BASE64" ]; then
    echo "Importing certificate from secrets..."
    echo "$MACOS_P12_BASE64" | base64 --decode > "$RUNNER_TEMP/cert.p12"
    security import "$RUNNER_TEMP/cert.p12" \
        -k "$KEYCHAIN_PATH" \
        -P "$P12_PASSWORD" \
        -T /usr/bin/codesign
    rm "$RUNNER_TEMP/cert.p12"
else
    echo "Generating self-signed certificate in CI..."
    security create-certificate -k "$KEYCHAIN_PATH" \
        -s "$CERT_NAME" \
        -r sign \
        -e "dev@alchemy.app" \
        -p "$P12_PASSWORD"
fi

security set-key-partition-list -S apple-tool:,apple:,codesign: \
    -s -k "$P12_PASSWORD" "$KEYCHAIN_PATH"

echo "Signing with codesign..."
codesign --force --deep --options runtime \
    --sign "$CERT_NAME" \
    --timestamp \
    "$APP_PATH"


echo "Verifying signature..."
codesign --verify --verbose=2 "$APP_PATH"

echo "=== macOS signing completed successfully! ==="