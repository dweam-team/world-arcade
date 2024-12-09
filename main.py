import multiprocessing
import os
import sys
import time
import webview
from pathlib import Path
import uvicorn
import logging
import requests
import ctypes
from fastapi.staticfiles import StaticFiles
from dweam.server import app

def setup_logging():
    """Set up logging to both file and debug console"""
    # Create logs directory in user's documents folder
    if sys.platform == 'win32':
        documents = os.path.join(os.path.expanduser('~'), 'Documents')
    else:
        documents = os.path.expanduser('~')
    
    log_dir = os.path.join(documents, 'Dweam', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Create a log file with timestamp
    log_file = os.path.join(log_dir, f'dweam_{time.strftime("%Y%m%d_%H%M%S")}.log')
    
    # Set up logging format
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(log_format)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Create a "Latest log location" file for easy access
    latest_log_file = os.path.join(log_dir, 'latest_log_location.txt')
    with open(latest_log_file, 'w') as f:
        f.write(f'Latest log file: {log_file}')
    
    return log_file

def create_debug_console():
    """Create a separate console window for debug output on Windows"""
    if sys.platform == 'win32':
        try:
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            user32 = ctypes.WinDLL('user32', use_last_error=True)
            
            # Allocate console
            kernel32.AllocConsole()
            
            # Set console title
            user32.SetWindowTextW(kernel32.GetConsoleWindow(), "Dweam Debug Console")
            
            # Redirect stdout and stderr to console
            sys.stdout = open('CONOUT$', 'w')
            sys.stderr = open('CONOUT$', 'w')
            
            # Print something immediately to verify console is working
            print("Debug console initialized...")
            sys.stdout.flush()
        except Exception as e:
            # If we can't create the console, at least write to a file
            with open(os.path.join(os.path.expanduser('~'), 'dweam_console_error.log'), 'w') as f:
                f.write(f"Failed to create debug console: {str(e)}")

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def wait_for_server(url, timeout=30, interval=0.5):
    """Wait for a server to become available"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url)
            # Consider both 200 and 404 as valid responses - they both indicate the server is running
            if response.status_code in [200, 404]:
                return True
        except requests.RequestException:
            pass
        time.sleep(interval)
    return False

def run_backend(host="127.0.0.1", port=8080):
    """Run the backend server"""
    # Ensure each process has its own console output
    create_debug_console()
    
    logger = logging.getLogger('backend')
    logger.info(f"Starting backend server on {host}:{port}")
    print(f"Backend server starting on {host}:{port}")  # Direct console output
    sys.stdout.flush()
    
    # Mount the frontend static files
    static_files_dir = resource_path(os.path.join('frontend', 'client'))
    if os.path.exists(static_files_dir):
        logger.info(f"Mounting frontend files from: {static_files_dir}")
        app.mount("/", StaticFiles(directory=static_files_dir, html=True), name="frontend")
    else:
        logger.error(f"Frontend files not found at {static_files_dir}")
        logger.info(f"Current directory: {os.getcwd()}")
        logger.info(f"Directory contents: {os.listdir('.')}")
    
    # Configure uvicorn logging for non-TTY environments
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["default"]["use_colors"] = False
    log_config["formatters"]["access"]["use_colors"] = False
    
    try:
        uvicorn.run(app, host=host, port=port, log_config=log_config)
    except Exception as e:
        logger.error(f"Error starting backend server: {str(e)}", exc_info=True)
        print(f"Backend error: {str(e)}")  # Direct console output
        sys.stdout.flush()

def run_frontend(host="127.0.0.1", port=4321):
    """Run the frontend SSR server"""
    # Ensure each process has its own console output
    create_debug_console()
    
    logger = logging.getLogger('frontend')
    logger.info(f"Starting frontend server on {host}:{port}")
    print(f"Frontend server starting on {host}:{port}")  # Direct console output
    sys.stdout.flush()
    
    # Set required Astro environment variables
    os.environ['HOST'] = host
    os.environ['PORT'] = str(port)
    os.environ['ASTRO_NODE_AUTOSTART'] = 'true'  # Required for Node adapter
    os.environ['INTERNAL_BACKEND_URL'] = f'http://{host}:8080'
    
    # Get the path to the bundled node.exe and set up environment
    if hasattr(sys, '_MEIPASS'):
        base_dir = sys._MEIPASS
        node_exe = os.path.normpath(os.path.join(base_dir, 'node.exe'))
        node_path = os.path.normpath(os.path.join(base_dir, 'node_modules'))
        
        # Set NODE_PATH to help Node.js find modules
        os.environ['NODE_PATH'] = node_path
        
        # Add node_modules to PATH
        if 'PATH' in os.environ:
            os.environ['PATH'] = f"{node_path};{os.environ['PATH']}"
        else:
            os.environ['PATH'] = node_path
            
        # Log the environment setup
        logger.info(f"Node executable path: {node_exe}")
        logger.info(f"Node modules path: {node_path}")
        logger.info(f"PATH: {os.environ['PATH']}")
    else:
        node_exe = 'node'
        logger.info("Using system node installation")
    
    # The entry point should be dist/server/entry.mjs
    server_path = os.path.normpath(resource_path(os.path.join('frontend', 'server', 'entry.mjs')))
    
    if not os.path.exists(server_path):
        logger.error(f"Server entry point not found at: {server_path}")
        print(f"Error: Server entry point not found at: {server_path}")
        return
        
    logger.info(f"Starting frontend server from: {server_path}")
    
    # Verify node executable exists
    if not os.path.exists(node_exe):
        logger.error(f"Node executable not found at: {node_exe}")
        print(f"Error: Node executable not found at: {node_exe}")
        return
        
    try:
        # Change to the server directory to help with module resolution
        server_dir = os.path.dirname(server_path)
        os.chdir(server_dir)
        logger.info(f"Changed working directory to: {server_dir}")
        
        # List directory contents for debugging
        logger.info(f"Server directory contents: {os.listdir(server_dir)}")
        
        import subprocess
        
        # Set production environment for Astro
        env = os.environ.copy()
        env['NODE_ENV'] = 'production'
        
        # Run node process with real-time output
        process = subprocess.Popen(
            [node_exe, os.path.basename(server_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=server_dir,
            env=env
        )
        
        # Log output in real-time
        def log_output(stream, prefix):
            for line in stream:
                line = line.strip()
                if line:
                    logger.info(f"{prefix}: {line}")
                    print(f"{prefix}: {line}")
                    sys.stdout.flush()
        
        import threading
        stdout_thread = threading.Thread(target=log_output, args=(process.stdout, "Frontend stdout"))
        stderr_thread = threading.Thread(target=log_output, args=(process.stderr, "Frontend stderr"))
        
        stdout_thread.daemon = True
        stderr_thread.daemon = True
        
        stdout_thread.start()
        stderr_thread.start()
        
        # Don't wait for process to complete - Astro server should keep running
        # Just check if it started successfully
        time.sleep(2)  # Give it a moment to start
        
        if process.poll() is not None:
            # Process ended too quickly - that's an error
            logger.error(f"Frontend server failed to start (exited with code {process.returncode})")
            print(f"Frontend server failed to start (exited with code {process.returncode})")
            return
            
        # Keep the process reference so it can be terminated later
        return process
            
    except Exception as e:
        logger.error(f"Error starting frontend server: {str(e)}", exc_info=True)
        print(f"Frontend error: {str(e)}")
        sys.stdout.flush()
        return None

def main():
    # Set up logging and debug console first thing
    log_file = setup_logging()
    create_debug_console()
    
    print("\n=== Dweam Debug Console ===")
    print(f"Logs are being written to: {log_file}")
    print("Starting application...\n")
    sys.stdout.flush()
    
    logger = logging.getLogger('main')
    logger.info("Starting Dweam application...")
    
    host = "127.0.0.1"
    backend_port = 8080
    frontend_port = 4321
    
    # Start the backend server in a separate process
    backend_process = multiprocessing.Process(target=run_backend, args=(host, backend_port))
    backend_process.daemon = True
    backend_process.start()
    
    # Start the frontend SSR server
    frontend_process = run_frontend(host=host, port=frontend_port)
    if frontend_process is None:
        logger.error("Failed to start frontend server")
        print("Error: Failed to start frontend server!")
        sys.stdout.flush()
        return
    
    # Wait for both servers to be ready
    backend_url = f"http://{host}:{backend_port}"
    frontend_url = f"http://{host}:{frontend_port}"
    
    print("Waiting for servers to start...")
    sys.stdout.flush()
    
    logger.info("Waiting for backend server to start...")
    if not wait_for_server(backend_url):
        logger.error("Backend server failed to start within timeout")
        print("Error: Backend server failed to start!")
        sys.stdout.flush()
        return
    
    logger.info("Waiting for frontend server to start...")
    if not wait_for_server(frontend_url):
        logger.error("Frontend server failed to start within timeout")
        print("Error: Frontend server failed to start!")
        sys.stdout.flush()
        return
    
    logger.info("Both servers are ready!")
    print("Both servers are ready!")
    sys.stdout.flush()
    
    # Create a window with webview instead of opening browser
    logger.info(f"Opening webview window at {frontend_url}")
    window = webview.create_window(
        title="Dweam", 
        url=frontend_url,
        width=1280,
        height=800,
        resizable=True,
    )
    
    # Start webview and wait for it to close
    webview.start()
    
    # Clean up when window closes
    logger.info("Cleaning up processes...")
    print("\nCleaning up processes...")
    sys.stdout.flush()
    
    backend_process.terminate()
    if frontend_process.poll() is None:  # If process is still running
        frontend_process.terminate()
        try:
            frontend_process.wait(timeout=5)  # Wait up to 5 seconds for graceful shutdown
        except subprocess.TimeoutExpired:
            frontend_process.kill()  # Force kill if it doesn't shut down gracefully
    
    # Make sure processes are fully terminated
    backend_process.join(timeout=5)
    if backend_process.is_alive():
        backend_process.kill()
    
    logger.info("Application shutdown complete")
    print("Application shutdown complete")
    sys.stdout.flush()

if __name__ == "__main__":
    try:
        multiprocessing.freeze_support()
        main()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        logging.error("Fatal error in main", exc_info=True)
        sys.stdout.flush()
        time.sleep(5)