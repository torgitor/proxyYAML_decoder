"""
Subscription Downloader Module
Downloads subscription content from airport URLs with custom User-Agent
"""

import requests
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class SubscriptionDownloader:
    """
    Downloads subscription content from remote URLs.
    Handles custom headers, timeouts, and retry logic.
    """
    
    # Default User-Agent mimicking a Linux ARM64 browser
    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    def __init__(
        self, 
        user_agent: Optional[str] = None, 
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize the downloader.
        
        Args:
            user_agent: Custom User-Agent string (default: Chrome on Linux ARM64)
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum retry attempts (default: 3)
        """
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self.timeout = timeout
        self.max_retries = max_retries
        
    def _build_headers(self) -> Dict[str, str]:
        """
        Build HTTP request headers.
        
        Returns:
            Dictionary of HTTP headers
        """
        return {
            'User-Agent': self.user_agent,
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
    
    def download(self, url: str) -> bytes:
        """
        Download subscription content from URL.
        
        Args:
            url: Subscription URL to download from
            
        Returns:
            Raw bytes content from the response
            
        Raises:
            requests.RequestException: On network/HTTP errors
            ValueError: On invalid response
        """
        headers = self._build_headers()
        last_error = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Downloading subscription (attempt {attempt}/{self.max_retries})")
                logger.debug(f"URL: {url}")
                
                response = requests.get(
                    url, 
                    headers=headers, 
                    timeout=self.timeout,
                    verify=True  # Enable SSL verification
                )
                response.raise_for_status()
                
                content = response.content
                
                # Validate response
                if not self._validate_response(content):
                    raise ValueError("Invalid response content: empty or too small")
                
                logger.info(f"Download successful: {len(content)} bytes")
                return content
                
            except requests.Timeout as e:
                last_error = e
                logger.warning(f"Timeout on attempt {attempt}: {e}")
            except requests.RequestException as e:
                last_error = e
                logger.warning(f"Request error on attempt {attempt}: {e}")
                
        # All retries failed
        raise requests.RequestException(
            f"Failed to download after {self.max_retries} attempts: {last_error}"
        )
    
    def _validate_response(self, content: bytes) -> bool:
        """
        Validate the downloaded content.
        
        Args:
            content: Raw bytes to validate
            
        Returns:
            True if content is valid, False otherwise
        """
        # Check minimum size (subscription should be > 100 bytes)
        if len(content) < 100:
            logger.warning(f"Content too small: {len(content)} bytes")
            return False
        
        # Check if content is not empty/whitespace
        if not content.strip():
            logger.warning("Content is empty or whitespace only")
            return False
            
        return True
    
    def download_to_file(self, url: str, filepath: str) -> int:
        """
        Download subscription and save to file.
        
        Args:
            url: Subscription URL to download from
            filepath: Path to save the downloaded content
            
        Returns:
            Number of bytes written
        """
        content = self.download(url)
        
        with open(filepath, 'wb') as f:
            bytes_written = f.write(content)
            
        logger.info(f"Saved to {filepath}: {bytes_written} bytes")
        return bytes_written
