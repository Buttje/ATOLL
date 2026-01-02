#!/usr/bin/env python3
"""Build standalone executables for ATOLL using PyInstaller.

This script builds single-file executables for Windows and Linux/macOS
that include the Python runtime and all dependencies.

Usage:
    python scripts/build_executable.py [--platform windows|linux|macos]

Requirements:
    pip install pyinstaller
"""

import argparse
import os
import platform
import shutil
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import PyInstaller.__main__
except ImportError:
    print("Error: PyInstaller not installed. Install with: pip install pyinstaller")
    sys.exit(1)


def get_project_root() -> Path:
    """Get project root directory."""
    return Path(__file__).parent.parent


def create_spec_file(target_platform: str, output_dir: Path) -> Path:
    """Create PyInstaller spec file.

    Args:
        target_platform: Target platform (windows, linux, macos)
        output_dir: Output directory for spec file

    Returns:
        Path to created spec file
    """
    project_root = get_project_root()
    src_dir = project_root / "src"

    # Determine extension
    ext = ".exe" if target_platform == "windows" else ""

    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

# Add source directory
src_dir = Path(r'{src_dir}').absolute()

a = Analysis(
    [str(src_dir / 'atoll' / '__main__.py')],
    pathex=[str(src_dir)],
    binaries=[],
    datas=[
        # Include package data
        (str(src_dir / 'atoll' / 'py.typed'), 'atoll'),
    ],
    hiddenimports=[
        'atoll',
        'atoll.agent',
        'atoll.config',
        'atoll.deployment',
        'atoll.mcp',
        'atoll.ui',
        'atoll.utils',
        'langchain',
        'langchain_core',
        'langchain_community',
        'langchain_ollama',
        'ollama',
        'fastapi',
        'uvicorn',
        'pydantic',
        'aiohttp',
        'colorama',
        'jsonschema',
        'prompt_toolkit',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'black',
        'ruff',
        'mypy',
        'pre_commit',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='atoll{ext}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""

    spec_file = output_dir / f"atoll-{target_platform}.spec"
    spec_file.write_text(spec_content)
    print(f"✓ Created spec file: {spec_file}")
    return spec_file


def build_executable(target_platform: str, clean: bool = True) -> Path:
    """Build executable using PyInstaller.

    Args:
        target_platform: Target platform (windows, linux, macos)
        clean: Whether to clean build directories first

    Returns:
        Path to built executable
    """
    project_root = get_project_root()
    build_dir = project_root / "build"
    dist_dir = project_root / "dist"

    print(f"\n{'='*60}")
    print(f"Building ATOLL executable for {target_platform}")
    print(f"{'='*60}\n")

    # Clean build directories if requested
    if clean:
        print("🧹 Cleaning build directories...")
        for dir_path in [build_dir, dist_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"  ✓ Removed {dir_path}")

    # Create output directories
    build_dir.mkdir(exist_ok=True)
    dist_dir.mkdir(exist_ok=True)

    # Create spec file
    print("\n📝 Creating PyInstaller spec file...")
    spec_file = create_spec_file(target_platform, build_dir)

    # Run PyInstaller
    print("\n🔨 Building executable (this may take several minutes)...")
    print(f"  → Platform: {target_platform}")
    print(f"  → Python: {sys.version_info.major}.{sys.version_info.minor}")
    print(f"  → Spec: {spec_file}")

    try:
        PyInstaller.__main__.run([
            str(spec_file),
            '--clean',
            '--noconfirm',
            f'--distpath={dist_dir}',
            f'--workpath={build_dir}/temp',
            f'--specpath={build_dir}',
        ])
    except Exception as e:
        print(f"\n✗ Build failed: {e}")
        sys.exit(1)

    # Find executable
    ext = ".exe" if target_platform == "windows" else ""
    exe_path = dist_dir / f"atoll{ext}"

    if not exe_path.exists():
        print(f"\n✗ Executable not found at {exe_path}")
        sys.exit(1)

    # Get size
    size_mb = exe_path.stat().st_size / (1024 * 1024)

    print(f"\n{'='*60}")
    print(f"✓ Build successful!")
    print(f"{'='*60}")
    print(f"  Executable: {exe_path}")
    print(f"  Size: {size_mb:.1f} MB")

    if size_mb > 100:
        print(f"  ⚠️  Warning: Executable is larger than 100 MB target")

    print(f"\nTest the executable with:")
    print(f"  {exe_path} --version")
    print(f"  {exe_path} --help")

    return exe_path


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build standalone ATOLL executables",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build for current platform
  python scripts/build_executable.py

  # Build for Windows
  python scripts/build_executable.py --platform windows

  # Build without cleaning first
  python scripts/build_executable.py --no-clean
        """,
    )

    # Detect current platform
    current_system = platform.system().lower()
    if current_system == "darwin":
        default_platform = "macos"
    elif current_system == "windows":
        default_platform = "windows"
    else:
        default_platform = "linux"

    parser.add_argument(
        "--platform",
        choices=["windows", "linux", "macos"],
        default=default_platform,
        help=f"Target platform (default: {default_platform})",
    )

    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Don't clean build directories before building",
    )

    args = parser.parse_args()

    # Warn if cross-compiling
    if args.platform != default_platform:
        print(f"⚠️  Warning: Building for {args.platform} from {current_system}")
        print("   Cross-platform builds may not work correctly.")
        print("   Build on the target platform for best results.\n")

    try:
        exe_path = build_executable(args.platform, clean=not args.no_clean)
        print(f"\n✓ Executable ready at: {exe_path}")
        return 0
    except Exception as e:
        print(f"\n✗ Build failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
