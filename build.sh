#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# build.sh – Build StudyPoint into a standalone Linux executable
# Usage:  bash build.sh
# Output: dist/StudyPoint/StudyPoint  (+ dist/StudyPoint/_internal/)
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV=".venv"
PYTHON="$VENV/bin/python"
PIP="$VENV/bin/pip"
PYINSTALLER="$VENV/bin/pyinstaller"

# ── 1. Ensure venv exists ────────────────────────────────────────────────────
if [ ! -f "$PYTHON" ]; then
    echo "[build] Creating virtual environment…"
    python3 -m venv "$VENV"
fi

# ── 2. Install / upgrade dependencies ───────────────────────────────────────
echo "[build] Installing dependencies…"
"$PIP" install --quiet --upgrade pip
"$PIP" install --quiet -r requirements.txt
"$PIP" install --quiet pyinstaller

# ── 3. Clean previous build artefacts ───────────────────────────────────────
echo "[build] Cleaning old build artefacts…"
rm -rf build/ dist/

# ── 4. Run PyInstaller ───────────────────────────────────────────────────────
echo "[build] Running PyInstaller…"
"$PYINSTALLER" StudyPoint.spec --noconfirm

# ── 5. Confirm output ────────────────────────────────────────────────────────
EXE="dist/StudyPoint/StudyPoint"
if [ -f "$EXE" ]; then
    SIZE=$(du -sh dist/StudyPoint | cut -f1)
    echo ""
    echo "✅ Build complete!"
    echo "   Executable : $SCRIPT_DIR/$EXE"
    echo "   Bundle size: $SIZE"
    echo ""
    echo "To run:  ./dist/StudyPoint/StudyPoint"
else
    echo "❌ Build FAILED – executable not found at $EXE"
    exit 1
fi
