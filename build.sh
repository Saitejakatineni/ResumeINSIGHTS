#!/bin/bash
# build.sh — sync source files into the .app bundle and rebuild the DMG.
# Run this after any code change: bash build.sh
set -e

cd "$(dirname "$0")"

echo "==> Syncing source files into app bundle..."
cp main.py     resumeINSIGHTS.app/Contents/Resources/main.py
cp launcher.py resumeINSIGHTS.app/Contents/Resources/launcher.py
cp static/index.html resumeINSIGHTS.app/Contents/Resources/static/index.html

echo "==> Staging DMG contents..."
rm -rf /tmp/dmg-staging
mkdir  /tmp/dmg-staging
cp -R resumeINSIGHTS.app /tmp/dmg-staging/
ln -s /Applications      /tmp/dmg-staging/Applications

echo "==> Building DMG..."
rm -f resumeINSIGHTS.dmg
hdiutil create \
    -volname "resumeINSIGHTS" \
    -srcfolder /tmp/dmg-staging \
    -ov -format UDZO \
    resumeINSIGHTS.dmg

echo ""
echo "Done. resumeINSIGHTS.dmg is ready."
echo "To install: open the DMG and drag resumeINSIGHTS to Applications."
