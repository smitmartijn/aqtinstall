import argparse
import os
import sys
import PyInstaller.__main__
import subprocess


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("arch", nargs="?")
    args = parser.parse_args()

    # Get version from git describe (similar to setuptools_scm but we'll sanitize it)
    try:
        git_version = subprocess.check_output(['git', 'describe', '--tags', '--abbrev=7']).decode().strip()
        # Remove the 'v' prefix if present
        if git_version.startswith('v'):
            git_version = git_version[1:]

        # If we have a dash (indicating we're not exactly on a tag), convert to PEP 440 format
        if '-' in git_version:
            parts = git_version.split('-')
            if len(parts) >= 3:
                # Format like 2.1.0-5-g3d5982c becomes 2.1.0.dev5+g3d5982c
                base_version, commits, commit_hash = parts[0], parts[1], parts[2]
                pep440_version = f"{base_version}.dev{commits}+{commit_hash}"
            else:
                # Simpler format like 2.1.0-whatpulse becomes 2.1.0.dev0+whatpulse
                base_version, suffix = parts
                pep440_version = f"{base_version}.dev0+{suffix}"
            print(f"Converted version from {git_version} to {pep440_version}")
            version = pep440_version
        else:
            version = git_version

        print(f"Using version: {version}")

        # Create a temporary version.py file that we can use during build
        with open('aqt/version.py', 'w') as f:
            f.write(f'__version__ = "{version}"\n')
    except Exception as e:
        print(f"Warning: Could not determine version: {e}")
        version = "0.0.0"

    # Now we're sure there's a version.py file with a PEP 440 compliant version

    # build PyInstaller arguments
    tools_dir = os.path.dirname(__file__)
    name = "aqt" if args.arch is None else "aqt_" + args.arch
    pyinstaller_args = [
        '--noconfirm',
        '--onefile',
        '--name', name,
        '--paths', ".",
        '--hidden-import', "aqt",
        # Add all potentially missing modules
        '--hidden-import', "defusedxml",
        '--hidden-import', "defusedxml.ElementTree",
        '--hidden-import', "beautifulsoup4",
        '--hidden-import', "bs4",
        '--hidden-import', "py7zr",
        '--hidden-import', "semantic_version",
        '--hidden-import', "texttable",
    ]

    # Add data files
    if os.name == 'nt':
        adddata_arg = "{src:s};aqt"
    else:
        adddata_arg = "{src:s}:aqt"
    for data in ["aqt/logging.ini", "aqt/settings.ini"]:
        pyinstaller_args.append('--add-data')
        pyinstaller_args.append(adddata_arg.format(src=data))
    pyinstaller_args.append(os.path.join(tools_dir, "launch_aqt.py"))

    # launch PyInstaller
    PyInstaller.__main__.run(pyinstaller_args)
