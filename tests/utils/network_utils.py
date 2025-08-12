"""
Network utilities for capturing and logging network traffic during tests.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse

class NetworkRecorder:
    """
    Records network traffic during test execution.
    """
    def __init__(self, page, test_name: str):
        """
        Initialize the network recorder.
        
        Args:
            page: Playwright page object
            test_name: Name of the test for logging purposes
        """
        self.page = page
        self.test_name = test_name
        self.requests = []
        self.responses = []
        self.network_logs = []
        self.output_dir = Path("test-results/network_logs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def start_recording(self):
        """Start recording network traffic."""
        self.page.on("request", self._on_request)
        self.page.on("response", self._on_response)
        self.page.on("requestfailed", self._on_request_failed)
        print(f"✅ Started network recording for test: {self.test_name}")
        
    def stop_recording(self):
        """Stop recording network traffic and save logs."""
        self.page.remove_listener("request", self._on_request)
        self.page.remove_listener("response", self._on_response)
        self.page.remove_listener("requestfailed", self._on_request_failed)
        self._save_network_logs()
        print(f"✅ Stopped network recording for test: {self.test_name}")
    
    async def _on_request(self, request):
        """Handle request events."""
        request_data = {
            "type": "request",
            "url": request.url,
            "method": request.method,
            "headers": dict(request.headers),
            "post_data": request.post_data,
            "timestamp": datetime.now().isoformat(),
            "resource_type": request.resource_type,
            "is_navigation_request": request.is_navigation_request(),
            "frame": request.frame.name if request.frame else "main"
        }
        self.requests.append(request_data)
        self.network_logs.append(request_data)
        
    async def _on_response(self, response):
        """Handle response events."""
        try:
            response_data = {
                "type": "response",
                "url": response.url,
                "status": response.status,
                "status_text": response.status_text,
                "headers": dict(response.headers),
                "timestamp": datetime.now().isoformat(),
                "from_service_worker": response.from_service_worker,
                "request": {
                    "method": response.request.method,
                    "headers": dict(response.request.headers),
                    "post_data": response.request.post_data
                }
            }
            
            # Try to get response body for non-binary responses
            if "image" not in response.request.resource_type and "font" not in response.request.resource_type:
                try:
                    response_data["body"] = await response.text()
                except:
                    response_data["body"] = "[Binary or unreadable content]"
            
            self.responses.append(response_data)
            self.network_logs.append(response_data)
            
        except Exception as e:
            error_data = {
                "type": "response_error",
                "url": response.url,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.network_logs.append(error_data)
    
    async def _on_request_failed(self, request):
        """Handle failed requests."""
        failure = request.failure
        failure_data = {
            "type": "request_failed",
            "url": request.url,
            "method": request.method,
            "failure_text": failure,
            "timestamp": datetime.now().isoformat(),
            "resource_type": request.resource_type,
            "is_navigation_request": request.is_navigation_request()
        }
        self.network_logs.append(failure_data)
    
    def _save_network_logs(self):
        """Save the network logs to a JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_test_name = "".join(c if c.isalnum() else "_" for c in self.test_name)
        filename = f"{safe_test_name}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        # Prepare log data
        log_data = {
            "test_name": self.test_name,
            "timestamp": datetime.now().isoformat(),
            "requests": self.requests,
            "responses": self.responses,
            "logs": self.network_logs
        }
        
        # Save to file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Network logs saved to: {filepath}")
        return filepath

def capture_network(page, test_name: str):
    """
    Context manager for capturing network traffic during a test.

    Args:
        page: Playwright page object
        test_name: Name of the test for logging purposes

    Yields:
        NetworkRecorder: The network recorder instance

    Example:
        with capture_network(page, "test_login"):
            # Test code here
            pass
    """
    recorder = NetworkRecorder(page, test_name)
    recorder.start_recording()
    try:
        yield recorder
    finally:
        recorder.stop_recording()
