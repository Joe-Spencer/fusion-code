"""
Package Manager for Fusion 360

This script helps install Python packages for Fusion 360's Python environment.
It reads packages to install from a requirements.txt file.
It attempts to locate all Fusion 360 Python executables and install the packages for each one.
Supports both Windows and macOS.
"""

import os
import sys
import subprocess
import glob
import platform
from pathlib import Path

# Only import Windows-specific modules on Windows
if platform.system() == "Windows":
    import winreg
    import ctypes

def is_admin():
    """Check if the script is running with admin/root privileges"""
    if platform.system() == "Windows":
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    else:  # macOS/Linux
        return os.geteuid() == 0  # Root has euid 0

def find_fusion_python_paths():
    """Find potential Fusion 360 Python paths based on OS"""
    paths = []
    system = platform.system()
    
    if system == "Windows":
        # Windows-specific search
        # Try to find Fusion 360 install location from Windows registry
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkey = winreg.OpenKey(key, subkey_name)
                    try:
                        display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                        if "Fusion 360" in display_name:
                            install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                            paths.append(install_location)
                    except:
                        pass
                    winreg.CloseKey(subkey)
                except:
                    continue
            winreg.CloseKey(key)
        except:
            pass
        
        # Common Fusion 360 install locations for Windows
        common_locations = [
            os.path.expanduser("~\\AppData\\Local\\Autodesk\\webdeploy"),
            "C:\\Program Files\\Autodesk\\webdeploy",
            "C:\\Program Files (x86)\\Autodesk\\webdeploy",
            os.path.expanduser("~\\AppData\\Local\\Autodesk\\Fusion 360")
        ]
        
        # Add common locations to search paths
        paths.extend(common_locations)
        
        # Python executable name on Windows
        python_exe = "python.exe"
        
    elif system == "Darwin":  # macOS
        # Common Fusion 360 install locations for macOS
        common_locations = [
            "/Applications/Autodesk Fusion 360.app/Contents",
            os.path.expanduser("~/Library/Application Support/Autodesk/webdeploy"),
            "/Library/Application Support/Autodesk/webdeploy",
            os.path.expanduser("~/Library/Caches/Autodesk/webdeploy")
        ]
        
        paths.extend(common_locations)
        
        # Python executable name on macOS
        python_exe = "python"
        
    else:
        print(f"Unsupported operating system: {system}")
        return []
    
    # Look for Python executable in Fusion paths
    python_paths = []
    
    for base_path in paths:
        if os.path.exists(base_path):
            # Convert to Path object to handle cross-platform path operations
            base_path_obj = Path(base_path)
            
            # Search for Python executable in production directories
            for prod_dir in glob.glob(str(base_path_obj / "production" / "*")):
                python_path = Path(prod_dir) / "Python" / python_exe
                if python_path.exists() and str(python_path) not in python_paths:
                    python_paths.append(str(python_path))
            
            # Try common subdirectory patterns using Path for cross-platform compatibility
            pattern_parts = [
                ["*", "*", "Python", python_exe],
                ["*", "Python", python_exe],
                ["Python", python_exe]
            ]
            
            for parts in pattern_parts:
                pattern = base_path_obj
                for part in parts:
                    pattern = pattern / part
                
                # Convert Path to string for glob
                for path in glob.glob(str(pattern)):
                    if os.path.exists(path) and path not in python_paths:
                        python_paths.append(path)
    
    return python_paths

def read_requirements(requirements_path):
    """Read requirements from a requirements.txt file"""
    if not os.path.exists(requirements_path):
        return []
    
    with open(requirements_path, 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    return requirements

def install_packages(python_path, requirements):
    """Install packages from requirements list using the specified Python executable"""
    if not requirements:
        print("No packages specified in requirements.txt. Nothing to install.")
        return True
        
    try:
        print(f"\nAttempting to install packages using: {python_path}")
        
        # Check if pip is available
        try:
            subprocess.run([python_path, "-m", "pip", "--version"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("Pip not available. Attempting to install pip first...")
            subprocess.run([python_path, "-m", "ensurepip", "--upgrade"], check=True)
        
        # Install each package from the requirements list
        success = True
        for requirement in requirements:
            print(f"Installing {requirement}...")
            result = subprocess.run(
                [python_path, "-m", "pip", "install", requirement],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"Successfully installed {requirement}")
            else:
                print(f"Failed to install {requirement}")
                print("Error:")
                print(result.stderr)
                success = False
        
        return success
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    print(f"=== Package Manager for Fusion 360 (Running on {platform.system()}) ===")
    print("This script will install packages from requirements.txt for ALL detected Fusion 360 Python environments.")
    
    # Get the requirements.txt file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_requirements_path = os.path.join(script_dir, "requirements.txt")
    
    requirements_path = default_requirements_path
    if not os.path.exists(requirements_path):
        print(f"Could not find requirements.txt at: {requirements_path}")
        custom_path = input("Enter path to requirements.txt (or press Enter to exit): ")
        if custom_path and os.path.exists(custom_path):
            requirements_path = custom_path
        else:
            if custom_path:
                print(f"Path does not exist: {custom_path}")
            print("\nExiting without installation.")
            return
    
    # Read requirements
    requirements = read_requirements(requirements_path)
    if not requirements:
        print(f"No packages specified in {requirements_path}. Please add packages to install.")
        input("\nPress Enter to exit... ")
        return
    
    # Check if we need admin privileges
    system = platform.system()
    if not is_admin():
        if system == "Windows":
            print("Note: Some installation paths may require administrator privileges.")
            print("If installation fails, try running this script as administrator.")
        else:
            print("Note: Some installation paths may require root privileges.")
            print("If installation fails, try running this script with sudo.")
    
    # Find Python paths
    print("\nSearching for Fusion 360 Python installations...")
    python_paths = find_fusion_python_paths()
    
    if not python_paths:
        print("No Fusion 360 Python installations found automatically.")
        
        # Get the appropriate Python executable name based on OS
        python_exe = "python.exe" if system == "Windows" else "python"
        
        custom_path = input(f"\nEnter the full path to Fusion 360's {python_exe} (or press Enter to exit): ")
        if custom_path and os.path.exists(custom_path):
            python_paths = [custom_path]
        else:
            if custom_path:
                print(f"Path does not exist: {custom_path}")
            print("\nExiting without installation.")
            return
    
    # Display found paths
    print(f"\nFound {len(python_paths)} potential Fusion 360 Python installation(s):")
    for i, path in enumerate(python_paths):
        print(f"{i+1}. {path}")
    
    # Display packages to install
    print("\nPackages to install:")
    for req in requirements:
        print(f"- {req}")
    
    # Ask for confirmation to install for all instances
    print(f"\nThis will install the above packages for ALL {len(python_paths)} Python installations.")
    confirm = input("Proceed with installation for all installations? (y/n): ")
    
    if confirm.lower() != 'y':
        print("Installation cancelled.")
        return
    
    # Install packages for all found Python installations
    successful_installs = 0
    failed_installs = 0
    
    for python_path in python_paths:
        success = install_packages(python_path, requirements)
        if success:
            successful_installs += 1
            print(f"\n✓ Successfully installed packages for: {python_path}")
        else:
            failed_installs += 1
            print(f"\n✗ Failed to install some packages for: {python_path}")
    
    # Final summary
    print("\n=== Installation Summary ===")
    print(f"Total Fusion 360 Python installations found: {len(python_paths)}")
    print(f"Successful installations: {successful_installs}")
    print(f"Failed installations: {failed_installs}")
    
    if failed_installs > 0:
        if system == "Windows":
            print("\nFor failed installations, you may need to try manually:")
            print("  1. Run this script as administrator")
        else:
            print("\nFor failed installations, you may need to try manually:")
            print("  1. Run this script with sudo")
        
        print(f"  2. Or install manually with: '[Python Path]' -m pip install -r {requirements_path}")
    
    input("\nPress Enter to exit... ")

if __name__ == "__main__":
    main() 