"""
Format Decoder Module
Detects and decodes various subscription formats (base64, plain text, YAML)
"""

import base64
import logging
from typing import Tuple, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class FormatType(Enum):
    """Enumeration of supported subscription formats"""
    BASE64_URI_LIST = "base64_uri_list"  # Base64 encoded URI list (most common)
    PLAIN_URI_LIST = "plain_uri_list"    # Plain text URI list  
    CLASH_YAML = "clash_yaml"            # Standard Clash YAML config
    UNKNOWN = "unknown"                   # Unknown format


class FormatDecoder:
    """
    Detects subscription format and decodes content accordingly.
    Supports base64, plain text URI lists, and standard Clash YAML.
    """
    
    # Protocol prefixes to look for
    PROXY_PROTOCOLS = [b'ss://', b'vmess://', b'trojan://', b'vless://']
    
    def detect_format(self, content: bytes) -> FormatType:
        """
        Detect the format of subscription content.
        
        Args:
            content: Raw bytes content to analyze
            
        Returns:
            FormatType enum indicating the detected format
        """
        # Strip whitespace for analysis
        stripped = content.strip()
        
        # Check if it's standard Clash YAML (has 'proxies:' key)
        if b'proxies:' in content:
            logger.info("Detected format: Clash YAML")
            return FormatType.CLASH_YAML
        
        # Check if it's plain URI list (starts with protocol)
        for protocol in self.PROXY_PROTOCOLS:
            if stripped.startswith(protocol):
                logger.info("Detected format: Plain URI list")
                return FormatType.PLAIN_URI_LIST
        
        # Try base64 decode to check for URI list
        try:
            # Handle base64 with potential line breaks
            cleaned = stripped.replace(b'\n', b'').replace(b'\r', b'')
            
            # Add padding if needed
            padding_needed = len(cleaned) % 4
            if padding_needed:
                cleaned += b'=' * (4 - padding_needed)
            
            decoded = base64.b64decode(cleaned)
            
            # Check if decoded content contains proxy protocols
            for protocol in self.PROXY_PROTOCOLS:
                if protocol in decoded:
                    logger.info("Detected format: Base64 encoded URI list")
                    return FormatType.BASE64_URI_LIST
                    
        except Exception as e:
            logger.debug(f"Base64 decode attempt failed: {e}")
        
        logger.warning("Unable to detect format")
        return FormatType.UNKNOWN
    
    def decode(self, content: bytes, format_type: Optional[FormatType] = None) -> str:
        """
        Decode subscription content based on format.
        
        Args:
            content: Raw bytes content to decode
            format_type: Optional format type (auto-detect if None)
            
        Returns:
            Decoded string content
            
        Raises:
            ValueError: If format is unknown or decode fails
        """
        if format_type is None:
            format_type = self.detect_format(content)
        
        if format_type == FormatType.BASE64_URI_LIST:
            return self._decode_base64(content)
        elif format_type == FormatType.PLAIN_URI_LIST:
            return content.decode('utf-8')
        elif format_type == FormatType.CLASH_YAML:
            return content.decode('utf-8')
        else:
            raise ValueError(f"Cannot decode unknown format: {format_type}")
    
    def _decode_base64(self, content: bytes) -> str:
        """
        Decode base64 encoded content.
        
        Args:
            content: Base64 encoded bytes
            
        Returns:
            Decoded UTF-8 string
            
        Raises:
            ValueError: If base64 decode fails
        """
        try:
            # Clean the content: remove whitespace and line breaks
            cleaned = content.strip().replace(b'\n', b'').replace(b'\r', b'')
            
            # Add padding if needed (base64 must be multiple of 4)
            padding_needed = len(cleaned) % 4
            if padding_needed:
                cleaned += b'=' * (4 - padding_needed)
            
            # Decode base64
            decoded_bytes = base64.b64decode(cleaned)
            
            # Decode to UTF-8 string
            decoded_str = decoded_bytes.decode('utf-8')
            
            logger.info(f"Base64 decode successful: {len(decoded_str)} characters")
            return decoded_str
            
        except base64.binascii.Error as e:
            raise ValueError(f"Invalid base64 content: {e}")
        except UnicodeDecodeError as e:
            raise ValueError(f"Failed to decode as UTF-8: {e}")
    
    def validate_decoded(self, content: str) -> Tuple[bool, str]:
        """
        Validate decoded content contains valid proxy URIs.
        
        Args:
            content: Decoded string content
            
        Returns:
            Tuple of (is_valid, message)
        """
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        if not lines:
            return False, "No content found after decoding"
        
        # Count valid proxy URIs
        valid_count = 0
        protocols_str = [p.decode() for p in self.PROXY_PROTOCOLS]
        
        for line in lines:
            for protocol in protocols_str:
                if line.startswith(protocol):
                    valid_count += 1
                    break
        
        if valid_count == 0:
            return False, "No valid proxy URIs found in decoded content"
        
        return True, f"Found {valid_count} valid proxy URIs"
    
    def extract_uris(self, content: str) -> list:
        """
        Extract proxy URIs from decoded content.
        
        Args:
            content: Decoded string content
            
        Returns:
            List of proxy URI strings
        """
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        uris = []
        protocols_str = [p.decode() for p in self.PROXY_PROTOCOLS]
        
        for line in lines:
            for protocol in protocols_str:
                if line.startswith(protocol):
                    uris.append(line)
                    break
        
        logger.info(f"Extracted {len(uris)} URIs")
        return uris
