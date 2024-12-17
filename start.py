#!/usr/bin/env python3

import os
import subprocess
import argparse
from pathlib import Path
from dotenv import load_dotenv
import json

class ProjectController:
    def __init__(self):

        self.project_dir = Path(__file__).resolve().parent
        env_path = self.project_dir / '.env'
        if not env_path.exists():
            raise FileNotFoundError(f"Environment file not found: {env_path}")


        # Load the project's environment variables
        load_dotenv(env_path, override=True)

        self.backend_dir = self.project_dir / "backend"
        self.frontend_dir = self.project_dir  / "frontend"

        self.api_port = os.getenv("API_PORT")
        self.frontend_port = os.getenv("FRONTEND_PORT")

        # Use the parent virtual environment if it exists, otherwise look for local one
        parent_venv = Path(os.environ.get('VIRTUAL_ENV', '')).resolve()
        local_venv = self.project_dir.parent / ".venv"
        self.venv_dir = parent_venv if parent_venv.exists() else local_venv
        
        self.gunicorn = self.venv_dir / "bin" / "gunicorn"
        self.uvicorn = self.venv_dir / "bin" / "uvicorn"
        self.log_file = self.project_dir / "daemon.log"

    def stop_service(self, service):
        """Stop specified service(s)"""
        try:
            if service in ['back', 'both']:
                subprocess.run(f"pkill -f ':{self.api_port}|\-p {self.api_port}'", shell=True, check=False)
                print(f"✓ Stopped any process on port {self.api_port} (API)")
            
            if service in ['front', 'both']:
                subprocess.run(f"pkill -f ':{self.frontend_port}|\-p {self.frontend_port}'", shell=True, check=False)
                print(f"✓ Stopped any process on port {self.frontend_port} (Frontend)")
        except Exception as e:
            print(f"Error stopping {service}:", e)

    def start_service(self, service, daemon=False):
        """Start specified service(s)"""

        if service == 'both' and not daemon:
            print("Error: Cannot start both services in non-daemon mode.")
            print("Please either:")
            print("1. Use --daemon flag to run both services")
            print("2. Or start services separately in different terminals:")
            print(f"   python start.py start back")
            print(f"   python start.py start front")
            return
            
        try:
            if service in ['back', 'both']:
                self._start_backend(daemon)
            
            if service in ['front', 'both']:
                self._start_frontend(daemon)
        except Exception as e:
            print(f"Error starting {service}:", e)

    def _start_backend(self, daemon):
        """Start the backend service"""
        if not self.backend_dir.exists():
            raise FileNotFoundError(f"Backend directory not found: {self.backend_dir}")

        # Activate virtual environment in the environment
        activate_script = self.venv_dir / "bin" / "activate"
        activate_cmd = f"source {activate_script}"
        
        if daemon:
            # Daemon mode uses gunicorn
            backend_command = [
                "nohup", str(self.gunicorn),
                "-k", "uvicorn.workers.UvicornWorker",
                "app.main:app",  # Changed to use the correct module path
                "--bind", f"0.0.0.0:{self.api_port}",
                "--timeout", "600",
                "--workers", "4",
            ]
            with open(self.log_file, "a") as log:
                process = subprocess.Popen(
                    backend_command,
                    cwd=self.backend_dir,
                    stdout=log,
                    stderr=log,
                    env={**os.environ, "PYTHONPATH": str(self.backend_dir)}
                )
                print(f"✓ Backend started on port {self.api_port} (daemonized)")
        else:
            # Non-daemon mode uses uvicorn directly
            backend_command = [
                str(self.uvicorn),
                "app.main:app",  # Changed to use the correct module path
                "--host", "0.0.0.0",
                "--port", str(self.api_port),
                "--reload",
                "--workers", "4",
            ]
            subprocess.run(
                backend_command,
                cwd=self.backend_dir,
                env={**os.environ, "PYTHONPATH": str(self.backend_dir)},
                check=True
            )

    def _start_frontend(self, daemon):
        """Start the frontend service with improved npm handling"""
        if not self.frontend_dir.exists():
            raise FileNotFoundError(f"Frontend directory not found: {self.frontend_dir}")
        
        # Improved npm installation process
        try:
            print("Setting up frontend dependencies...")
            
            # Update npm itself first
            subprocess.run(["npm", "install", "npm@latest"], 
                        check=True, 
                        capture_output=True,
                        text=True)
            
            # Install dependencies with specific flags to reduce warnings
            install_result = subprocess.run(
                ["npm", "install", 
                "--no-fund", # Disable funding messages
                "--no-audit", # Disable audit warnings
                "--loglevel=error" # Only show errors
                ], 
                cwd=self.frontend_dir,
                capture_output=True,
                text=True
            )
            
            if install_result.returncode == 0:
                print("✓ Frontend dependencies installed")
            else:
                print("! Warning: npm install completed with issues:")
                print(install_result.stderr)
            
            # Run security audit and fix
            print("Checking for security vulnerabilities...")
            audit_result = subprocess.run(
                ["npm", "audit", "fix", "--force"],
                cwd=self.frontend_dir,
                capture_output=True,
                text=True
            )
            
            if audit_result.returncode == 0:
                print("✓ Security vulnerabilities fixed")
            else:
                print("! Warning: Some security issues couldn't be automatically fixed")
                print("  Run 'npm audit' manually in the frontend directory for details")
            
            # Start the frontend
            if daemon:
                frontend_command = ["nohup", "npm", "run", "dev"]

                with open(self.log_file, "a") as log:
                    subprocess.Popen(
                        frontend_command,
                        cwd=self.frontend_dir,
                        stdout=log,
                        stderr=log,
                        env={**os.environ, 
                            "NODE_ENV": "development",
                            "DISABLE_ESLINT_PLUGIN": "true",
                            "PORT": str(self.frontend_port)
                        }
                    )
                    print(f"✓ Frontend started on port {self.frontend_port} (daemonized)")
            else:
                frontend_command = ["npm", "run", "dev"]
                subprocess.run(
                    frontend_command, 
                    cwd=self.frontend_dir, 
                    check=True,
                    env={**os.environ, 
                        "NODE_ENV": "development",
                        "DISABLE_ESLINT_PLUGIN": "true",
                        "PORT": str(self.frontend_port)
                    }
                )


        except subprocess.CalledProcessError as e:
            print(f"Error starting frontend: {e}")
            if e.output:
                print(f"Output: {e.output}")
            raise

    # Update package.json creation to use newer versions and configurations
    def create_frontend_files(self):
        """Create frontend configuration and files with updated dependencies"""
        package_json = {
            "name": self.config['APP_NAME'],
            "version": "0.1.0",
            "private": True,
            "scripts": {
                "dev": f"next dev -p {self.config['FRONTEND_PORT']}",
                "build": "next build",
                "start": f"next start -p {self.config['FRONTEND_PORT']}",
                "lint": "next lint"
            },
            "dependencies": {
                "next": "^14.1.0",
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "@tanstack/react-query": "^5.17.9",
                "axios": "^1.6.7"
            },
            "devDependencies": {
                "typescript": "^5.3.3",
                "@types/node": "^20.11.0",
                "@types/react": "^18.2.48",
                "@types/react-dom": "^18.2.18",
                "autoprefixer": "^10.4.17",
                "postcss": "^8.4.33",
                "tailwindcss": "^3.4.1"
            }
        }

        # Add npm configurations to reduce warnings
        npm_rc = {
            "fund": False,
            "audit": False,
            "loglevel": "error",
            "save-exact": True
        }

        with open(self.frontend_dir / 'package.json', 'w') as f:
            json.dump(package_json, f, indent=2)

        with open(self.frontend_dir / '.npmrc', 'w') as f:
            for key, value in npm_rc.items():
                f.write(f"{key}={str(value).lower()}")

def main():
    parser = argparse.ArgumentParser(description='Control project services')
    parser.add_argument('action', choices=['start', 'stop', 'restart'],
                      help='Action to perform')
    parser.add_argument('service', choices=['front', 'back', 'both'],
                      help='Service to control')
    parser.add_argument('--daemon', action='store_true',
                      help='Run in daemon mode (for start/restart)')
    
    args = parser.parse_args()
    controller = ProjectController()

    if args.action == 'stop':
        controller.stop_service(args.service)
    elif args.action == 'start':
        controller.start_service(args.service, args.daemon)
    elif args.action == 'restart':
        controller.stop_service(args.service)
        controller.start_service(args.service, args.daemon)

if __name__ == "__main__":
    main()
