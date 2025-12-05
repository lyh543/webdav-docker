#!/usr/bin/env python3
"""
WebDAV Docker Container Automated Test Script

This script tests WebDAV containers with different PUID/PGID values to verify
that files created via WebDAV have the correct ownership in the mounted volume.

THIS TEST REQUIRES SUDO PRIVILEGES TEST FILES OWNED BY DIFFERENT USERS. BE CAUTIOUS!!!

Test cases:
1. PUID=0, PGID=0 (root)
2. PUID=999, PGID=999
3. PUID=1000, PGID=1000

For each test case:
- Build Docker image with a temporary name
- Create temporary directory for volume mount
- Run container in background with specific PUID/PGID
- Create files via WebDAV HTTP requests
- Verify file ownership in mounted directory
- Clean up containers, images, and temporary files
"""

import os
import sys
import time
import shutil
import tempfile
import subprocess
import requests
from requests.auth import HTTPBasicAuth
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class WebDAVTest:
    """WebDAV container test orchestrator"""
    
    def __init__(self):
        self.image_name = f"webdav-test-{int(time.time())}"
        self.temp_dir = None
        self.containers = []
        self.test_results = []
        # Find project root directory (where Dockerfile is located)
        self.project_root = self._find_project_root()
        
    def _find_project_root(self):
        """Find the project root directory containing Dockerfile"""
        current = Path(__file__).resolve().parent
        # Check parent directories for Dockerfile
        for _ in range(3):  # Check up to 3 levels up
            if (current / "Dockerfile").exists():
                return current
            current = current.parent
        # If not found, assume current directory
        return Path.cwd()
        
    def log(self, message, color=None):
        """Print colored log message"""
        if color:
            print(f"{color}{message}{Colors.ENDC}")
        else:
            print(message)
    
    def build_image(self):
        """Build Docker image with temporary name"""
        self.log(f"\n{'='*60}", Colors.HEADER)
        self.log(f"Building Docker image: {self.image_name}", Colors.HEADER)
        self.log(f"Building from: {self.project_root}", Colors.HEADER)
        self.log(f"{'='*60}", Colors.HEADER)
        
        try:
            cmd = ["docker", "build", "-t", self.image_name, str(self.project_root)]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.log("✓ Image built successfully", Colors.OKGREEN)
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"✗ Failed to build image: {e.stderr}", Colors.FAIL)
            return False
    
    def create_temp_directory(self):
        """Create temporary directory for volume mount"""
        self.log(f"\n{'='*60}", Colors.HEADER)
        self.log("Creating temporary directory", Colors.HEADER)
        self.log(f"{'='*60}", Colors.HEADER)
        
        try:
            self.temp_dir = tempfile.mkdtemp(prefix="webdav_test_")
            self.log(f"✓ Created: {self.temp_dir}", Colors.OKGREEN)
            return True
        except Exception as e:
            self.log(f"✗ Failed to create temp directory: {e}", Colors.FAIL)
            return False
    
    def run_container(self, puid, pgid, port):
        """Run Docker container with specific PUID/PGID"""
        container_name = f"webdav-test-{puid}-{pgid}-{int(time.time())}"
        
        self.log(f"\nStarting container: {container_name}", Colors.OKCYAN)
        self.log(f"  PUID={puid}, PGID={pgid}, PORT={port}")
        
        # Set ownership of temp directory to match PUID/PGID
        try:
            subprocess.run(["sudo", "chown", f"{puid}:{pgid}", self.temp_dir], 
                         check=True, capture_output=True)
            subprocess.run(["sudo", "chmod", "755", self.temp_dir], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            self.log(f"  ⚠ Warning: Could not set directory ownership: {e.stderr}", Colors.WARNING)
        
        try:
            cmd = [
                "docker", "run", "-d",
                "--name", container_name,
                "-p", f"{port}:80",
                "-e", f"PUID={puid}",
                "-e", f"PGID={pgid}",
                "-e", "WEBDAV_USERNAME=admin",
                "-e", "WEBDAV_PASSWORD=admin123",
                "-v", f"{self.temp_dir}:/var/www/webdav",
                self.image_name
            ]
            
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            container_id = result.stdout.strip()
            self.containers.append(container_name)
            
            # Wait for container to be ready
            time.sleep(3)
            
            # Check if container is running
            check_cmd = ["docker", "ps", "-q", "-f", f"name={container_name}"]
            check_result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            if check_result.stdout.strip():
                self.log(f"✓ Container started: {container_id[:12]}", Colors.OKGREEN)
                return True, container_name, port
            else:
                self.log(f"✗ Container failed to start", Colors.FAIL)
                # Show logs for debugging
                logs_cmd = ["docker", "logs", container_name]
                logs = subprocess.run(logs_cmd, capture_output=True, text=True)
                self.log(f"Container logs:\n{logs.stdout}\n{logs.stderr}", Colors.WARNING)
                return False, container_name, port
                
        except subprocess.CalledProcessError as e:
            self.log(f"✗ Failed to start container: {e.stderr}", Colors.FAIL)
            return False, None, port
    
    def create_webdav_file(self, port, filename, content):
        """Create file via WebDAV HTTP PUT request"""
        url = f"http://localhost:{port}/webdav/{filename}"
        auth = HTTPBasicAuth("admin", "admin123")
        
        try:
            response = requests.put(url, data=content, auth=auth, timeout=10)
            if response.status_code in [200, 201, 204]:
                self.log(f"  ✓ Created file via WebDAV: {filename}", Colors.OKGREEN)
                return True
            else:
                self.log(f"  ✗ Failed to create file: HTTP {response.status_code}", Colors.FAIL)
                return False
        except Exception as e:
            self.log(f"  ✗ Request failed: {e}", Colors.FAIL)
            return False
    
    def check_file_ownership(self, filename, expected_uid, expected_gid):
        """Check file ownership in mounted directory"""
        filepath = Path(self.temp_dir) / filename
        
        if not filepath.exists():
            self.log(f"  ✗ File does not exist: {filepath}", Colors.FAIL)
            return False
        
        stat_info = filepath.stat()
        actual_uid = stat_info.st_uid
        actual_gid = stat_info.st_gid
        
        self.log(f"  File ownership: UID={actual_uid}, GID={actual_gid}")
        
        if actual_uid == expected_uid and actual_gid == expected_gid:
            self.log(f"  ✓ Ownership correct: UID={actual_uid}, GID={actual_gid}", Colors.OKGREEN)
            return True
        else:
            self.log(f"  ✗ Ownership incorrect!", Colors.FAIL)
            self.log(f"    Expected: UID={expected_uid}, GID={expected_gid}", Colors.WARNING)
            self.log(f"    Actual:   UID={actual_uid}, GID={actual_gid}", Colors.WARNING)
            return False
    
    def test_case(self, puid, pgid, port):
        """Run a single test case"""
        self.log(f"\n{'='*60}", Colors.HEADER)
        self.log(f"TEST CASE: PUID={puid}, PGID={pgid}", Colors.HEADER)
        self.log(f"{'='*60}", Colors.HEADER)
        
        success, container_name, _ = self.run_container(puid, pgid, port)
        if not success:
            self.test_results.append({
                'puid': puid,
                'pgid': pgid,
                'status': 'FAILED',
                'reason': 'Container failed to start'
            })
            return False
        
        # Wait a bit more for WebDAV service to be fully ready
        time.sleep(2)
        
        # Create test file
        filename = f"test_{puid}_{pgid}.txt"
        content = f"Test file created with PUID={puid}, PGID={pgid}"
        
        if not self.create_webdav_file(port, filename, content):
            self.test_results.append({
                'puid': puid,
                'pgid': pgid,
                'status': 'FAILED',
                'reason': 'Failed to create file via WebDAV'
            })
            return False
        
        # Check file ownership
        if not self.check_file_ownership(filename, puid, pgid):
            self.test_results.append({
                'puid': puid,
                'pgid': pgid,
                'status': 'FAILED',
                'reason': 'Incorrect file ownership'
            })
            return False
        
        self.test_results.append({
            'puid': puid,
            'pgid': pgid,
            'status': 'PASSED',
            'reason': 'All checks passed'
        })
        return True
    
    def cleanup(self):
        """Clean up containers, image, and temporary directory"""
        self.log(f"\n{'='*60}", Colors.HEADER)
        self.log("CLEANUP", Colors.HEADER)
        self.log(f"{'='*60}", Colors.HEADER)
        
        # Stop and remove containers
        for container in self.containers:
            try:
                self.log(f"Stopping container: {container}")
                subprocess.run(["docker", "stop", container], 
                             capture_output=True, check=True, timeout=10)
                subprocess.run(["docker", "rm", container], 
                             capture_output=True, check=True)
                self.log(f"  ✓ Removed: {container}", Colors.OKGREEN)
            except subprocess.CalledProcessError as e:
                self.log(f"  ✗ Failed to remove container {container}: {e.stderr}", 
                        Colors.WARNING)
            except subprocess.TimeoutExpired:
                self.log(f"  ✗ Timeout stopping container {container}", Colors.WARNING)
                # Force kill if stop times out
                try:
                    subprocess.run(["docker", "kill", container], capture_output=True)
                    subprocess.run(["docker", "rm", container], capture_output=True)
                except:
                    pass
        
        # Remove image (force removal to handle any lingering references)
        if self.image_name:
            try:
                self.log(f"Removing image: {self.image_name}")
                subprocess.run(["docker", "rmi", "-f", self.image_name], 
                             capture_output=True, check=True)
                self.log(f"  ✓ Removed image: {self.image_name}", Colors.OKGREEN)
            except subprocess.CalledProcessError as e:
                self.log(f"  ✗ Failed to remove image: {e.stderr}", Colors.WARNING)
        
        # Remove temporary directory
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                self.log(f"Removing temporary directory: {self.temp_dir}")
                # Use sudo to remove files that may be owned by different users
                subprocess.run(["sudo", "rm", "-rf", self.temp_dir], 
                             check=True, capture_output=True)
                self.log(f"  ✓ Removed: {self.temp_dir}", Colors.OKGREEN)
            except subprocess.CalledProcessError as e:
                self.log(f"  ✗ Failed to remove temp directory: {e.stderr}", Colors.WARNING)
                # Fallback to regular shutil.rmtree
                try:
                    shutil.rmtree(self.temp_dir)
                    self.log(f"  ✓ Removed (fallback): {self.temp_dir}", Colors.OKGREEN)
                except Exception as e2:
                    self.log(f"  ✗ Fallback also failed: {e2}", Colors.WARNING)
    
    def print_summary(self):
        """Print test summary"""
        self.log(f"\n{'='*60}", Colors.HEADER)
        self.log("TEST SUMMARY", Colors.HEADER)
        self.log(f"{'='*60}", Colors.HEADER)
        
        passed = sum(1 for r in self.test_results if r['status'] == 'PASSED')
        failed = sum(1 for r in self.test_results if r['status'] == 'FAILED')
        
        for result in self.test_results:
            status_color = Colors.OKGREEN if result['status'] == 'PASSED' else Colors.FAIL
            self.log(f"\nPUID={result['puid']}, PGID={result['pgid']}: "
                    f"{result['status']}", status_color)
            self.log(f"  Reason: {result['reason']}")
        
        self.log(f"\n{'='*60}", Colors.HEADER)
        self.log(f"Total: {len(self.test_results)} | "
                f"Passed: {passed} | Failed: {failed}", 
                Colors.OKGREEN if failed == 0 else Colors.FAIL)
        self.log(f"{'='*60}", Colors.HEADER)
        
        return failed == 0
    
    def run(self):
        """Run all tests"""
        try:
            # Build image
            if not self.build_image():
                return False
            
            # Create temp directory
            if not self.create_temp_directory():
                return False
            
            # Run test cases with different PUID/PGID values
            # Use different port ranges to avoid conflicts
            import random
            base_port = random.randint(9000, 9900)
            test_cases = [
                (0, 0, base_port),      # root
                (999, 999, base_port + 1),  # arbitrary user
                (1000, 1000, base_port + 2) # default user
            ]
            
            for puid, pgid, port in test_cases:
                self.test_case(puid, pgid, port)
            
            # Print summary
            all_passed = self.print_summary()
            
            return all_passed
            
        finally:
            # Always cleanup
            self.cleanup()


def main():
    """Main entry point"""
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║         WebDAV Docker Container Test Suite                ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")
    
    # Check if Docker is available
    try:
        subprocess.run(["docker", "--version"], 
                      capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"{Colors.FAIL}Error: Docker is not installed or not in PATH{Colors.ENDC}")
        return 1
    
    # Run tests
    test = WebDAVTest()
    success = test.run()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
