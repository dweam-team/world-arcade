import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path
from structlog.stdlib import BoundLogger
from importlib.resources import files


class PyInstallerEnvBuilder(venv.EnvBuilder):
    """Custom EnvBuilder that uses the bundled python.exe when running from PyInstaller"""

    def __init__(self, log: BoundLogger, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = log
    
    def ensure_directories(self, env_dir):
        context = super().ensure_directories(env_dir)
        if getattr(sys, 'frozen', False):
            # Use the copied Python directory, not the PyInstaller one
            base_dir = Path(sys._MEIPASS) / 'python'
            if not base_dir.exists():
                raise RuntimeError(f"Python directory not found at {base_dir}")
            if not (base_dir / "python.exe").exists():
                raise RuntimeError(f"python.exe not found in {base_dir}")
                
            # Point to our copied Python
            context.executable = str(base_dir / "python.exe")
            context.python_dir = str(base_dir)
            context.python_exe = "python.exe"
            
            # Set up paths
            context.bin_path = str(Path(env_dir) / "Scripts")
            
            # Add better error reporting
            self.log.debug(f"Prepared python venv creation context", base_dir=base_dir, executable=context.executable, python_dir=context.python_dir)
        return context
    
    def symlink_or_copy(self, src, dst, relative_symlinks_ok=False):
        """Override symlink_or_copy to handle Windows venv creation"""
        if not (getattr(sys, 'frozen', False) and sys.platform == "win32"):
            super().symlink_or_copy(src, dst, relative_symlinks_ok)
            return
            
        basename = os.path.basename(src).lower()
        base_dir = Path(sys._MEIPASS) / 'python'
        
        if basename in ('python.exe', 'pythonw.exe'):
            src_path = base_dir / basename
            if not src_path.exists():
                raise RuntimeError(f"Required Python executable not found: {src_path}")
            shutil.copyfile(src_path, dst)
        else:
            # Copy DLLs and other files from our bundle
            src_path = base_dir / basename
            if src_path.exists():
                shutil.copyfile(src_path, dst)


def get_venv_path(log: BoundLogger) -> Path:
    """Get and setup the virtual environment path"""
    home_dir = os.environ.get("CACHE_DIR")
    if home_dir is not None:
        home_dir = Path(home_dir)
    else:
        home_dir = Path.home() / ".dweam"
    
    venv_path = home_dir / "dweam-venv"
    
    # If venv exists but is corrupted/incomplete, try to remove it
    if venv_path.exists():
        pip_path = venv_path / "Scripts" / "pip.exe" if sys.platform == "win32" else venv_path / "bin" / "pip"
        if pip_path.exists():
            return venv_path
        log.warning("Pip not found; cleaning up corrupted venv")
        try:
            # On Windows, we need to ensure no processes are using the directory
            if sys.platform == "win32":
                import ctypes
                kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
                MOVEFILE_DELAY_UNTIL_REBOOT = 0x4
                for item in venv_path.rglob("*"):
                    if item.is_file():
                        try:
                            kernel32.MoveFileExW(str(item), None, MOVEFILE_DELAY_UNTIL_REBOOT)
                        except:
                            pass
                kernel32.MoveFileExW(str(venv_path), None, MOVEFILE_DELAY_UNTIL_REBOOT)
            
            # Remove the entire venv directory
            shutil.rmtree(venv_path, ignore_errors=True)
        except Exception as e:
            log.error("Error cleaning up corrupted venv", error=str(e), path=venv_path)
            # Continue anyway - we'll try to create a new venv
    
    # Create new venv if it doesn't exist
    if not venv_path.exists():
        log.info("Creating virtual environment", venv_path=venv_path)
        try:
            venv_path.parent.mkdir(parents=True, exist_ok=True)
            create_and_setup_venv(log, venv_path)
            log.info("Virtual environment created", venv_path=venv_path)
        except Exception as e:
            log.error("Failed to create virtual environment", error=str(e))
            raise RuntimeError(f"Failed to create virtual environment: {e}")
    else:
        log.info("Found existing virtual environment", venv_path=venv_path)

    return venv_path

def create_and_setup_venv(log, path: Path) -> Path:
    """Create a new virtual environment and return its path"""
    try:
        builder = PyInstallerEnvBuilder(
            log,
            with_pip=True,
            upgrade_deps=True,
            clear=True,
            symlinks=False
        )
        builder.create(path)
        
        # Verify pip installation
        pip_path = path / "Scripts" / "pip.exe" if sys.platform == "win32" else path / "bin" / "pip"
        if not pip_path.exists():
            raise RuntimeError("pip not found after venv creation")
            
        return path

    except Exception as e:
        raise RuntimeError(f"Failed to create virtual environment: {str(e)}") from e

def ensure_correct_dweam_version(log: BoundLogger, pip_path: Path) -> None:
    """Ensure the correct version of dweam is installed in the venv"""
    import dweam
    
    if getattr(sys, 'frozen', False):
        # In PyInstaller bundle
        dweam_path = Path(sys._MEIPASS) / 'dweam'
    else:
        # In development - get the package root directory
        try:
            # Try newer importlib.resources API first (Python 3.9+)
            from importlib.resources.abc import Traversable
            dweam_root: Traversable = files('dweam')
            dweam_path = Path(str(dweam_root)).parent
        except (ImportError, AttributeError):
            # Fallback for older Python versions
            import dweam
            dweam_path = Path(dweam.__file__).parent.parent
    
    # Get installed version using pip show
    result = subprocess.run(
        [str(pip_path), "show", "dweam"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        log.warning("dweam not installed, installing", stdout=result.stdout, stderr=result.stderr)
        result = subprocess.run(
            [str(pip_path), "install", "-e", str(dweam_path)],
            text=True
        )
        if result.returncode != 0:
            log.error("Failed to install dweam")
            return
        return

    # Parse location from pip show output
    install_location = None
    for line in result.stdout.splitlines():
        if line.startswith("Location: "):
            install_location = line.split(": ")[1].strip()
            break
    
    # If dweam isn't installed from our path, reinstall it
    # TODO this wrongly detects incorrect install methinks
    if not install_location or not Path(install_location).samefile(dweam_path):
        log.warning("dweam is not installed from the correct location, reinstalling")
        result = subprocess.run(
            [str(pip_path), "install", "-e", str(dweam_path)],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            log.error("Failed to reinstall dweam", stdout=result.stdout, stderr=result.stderr)
            return
        log.debug("dweam reinstall output", stdout=result.stdout, stderr=result.stderr)
