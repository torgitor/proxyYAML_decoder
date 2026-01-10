"""
URI Parser Module
Parses various proxy protocol URIs (SS, VMess, Trojan, etc.) into structured data
"""

import base64
import json
import urllib.parse
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ProxyNode:
    """Data class representing a parsed proxy node"""
    name: str
    type: str
    server: str
    port: int
    # Protocol-specific fields stored in extra
    extra: Dict[str, Any]
    
    def to_clash_dict(self) -> Dict[str, Any]:
        """Convert to Clash proxy configuration dictionary"""
        result = {
            'name': self.name,
            'type': self.type,
            'server': self.server,
            'port': self.port,
            **self.extra
        }
        return result


class URIParser:
    """
    Parses proxy URIs into structured ProxyNode objects.
    Supports Shadowsocks (SS), VMess, Trojan, and VLESS protocols.
    """
    
    def parse(self, uri: str) -> Optional[ProxyNode]:
        """
        Parse a single proxy URI.
        
        Args:
            uri: Proxy URI string (e.g., ss://..., vmess://...)
            
        Returns:
            ProxyNode object or None if parsing fails
        """
        uri = uri.strip()
        
        if uri.startswith('ss://'):
            return self.parse_ss(uri)
        elif uri.startswith('vmess://'):
            return self.parse_vmess(uri)
        elif uri.startswith('trojan://'):
            return self.parse_trojan(uri)
        elif uri.startswith('vless://'):
            return self.parse_vless(uri)
        else:
            logger.warning(f"Unsupported protocol: {uri[:20]}...")
            return None
    
    def parse_batch(self, uris: List[str]) -> List[ProxyNode]:
        """
        Parse multiple URIs and return successful results.
        
        Args:
            uris: List of proxy URI strings
            
        Returns:
            List of successfully parsed ProxyNode objects
        """
        nodes = []
        failed = 0
        
        for uri in uris:
            try:
                node = self.parse(uri)
                if node:
                    nodes.append(node)
                else:
                    failed += 1
            except Exception as e:
                logger.warning(f"Failed to parse URI: {e}")
                failed += 1
        
        logger.info(f"Parsed {len(nodes)} nodes successfully, {failed} failed")
        return nodes
    
    def parse_ss(self, uri: str) -> Optional[ProxyNode]:
        """
        Parse Shadowsocks URI.
        
        Format: ss://[base64(method:password)]@server:port#name
        Alternative: ss://[base64(method:password@server:port)]#name
        
        Args:
            uri: Shadowsocks URI string
            
        Returns:
            ProxyNode object or None if parsing fails
        """
        try:
            # Remove protocol prefix
            content = uri[5:]  # Remove "ss://"
            
            # Split name (after #)
            if '#' in content:
                main_part, name_encoded = content.rsplit('#', 1)
                name = urllib.parse.unquote(name_encoded)
            else:
                main_part = content
                name = "SS-Node"
            
            # Check which format: base64@server:port or pure base64
            if '@' in main_part:
                # Format: base64@server:port
                b64_auth, server_port = main_part.rsplit('@', 1)
                
                # Parse server:port
                server, port_str = server_port.rsplit(':', 1)
                port = int(port_str)
                
                # Decode auth (method:password)
                auth_decoded = self._safe_base64_decode(b64_auth)
                if ':' in auth_decoded:
                    method, password = auth_decoded.split(':', 1)
                else:
                    raise ValueError(f"Invalid auth format: {auth_decoded}")
            else:
                # Format: base64(method:password@server:port)
                decoded = self._safe_base64_decode(main_part)
                
                if '@' in decoded:
                    auth_part, server_port = decoded.rsplit('@', 1)
                    method, password = auth_part.split(':', 1)
                    server, port_str = server_port.rsplit(':', 1)
                    port = int(port_str)
                else:
                    raise ValueError(f"Invalid SS URI format")
            
            return ProxyNode(
                name=name,
                type='ss',
                server=server,
                port=port,
                extra={
                    'cipher': method,
                    'password': password,
                    'udp': True
                }
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse SS URI: {e}")
            return None
    
    def parse_vmess(self, uri: str) -> Optional[ProxyNode]:
        """
        Parse VMess URI.
        
        Format: vmess://[base64(json)]
        
        Args:
            uri: VMess URI string
            
        Returns:
            ProxyNode object or None if parsing fails
        """
        try:
            # Remove protocol prefix
            content = uri[8:]  # Remove "vmess://"
            
            # Decode base64 JSON
            decoded = self._safe_base64_decode(content)
            config = json.loads(decoded)
            
            # Extract fields
            name = config.get('ps', config.get('remarks', 'VMess-Node'))
            server = config.get('add', config.get('host', ''))
            port = int(config.get('port', 0))
            uuid = config.get('id', '')
            alter_id = int(config.get('aid', 0))
            
            return ProxyNode(
                name=name,
                type='vmess',
                server=server,
                port=port,
                extra={
                    'uuid': uuid,
                    'alterId': alter_id,
                    'cipher': config.get('scy', 'auto'),
                    'network': config.get('net', 'tcp'),
                    'tls': config.get('tls', '') == 'tls',
                    'udp': True
                }
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse VMess URI: {e}")
            return None
    
    def parse_trojan(self, uri: str) -> Optional[ProxyNode]:
        """
        Parse Trojan URI.
        
        Format: trojan://password@server:port?params#name
        
        Args:
            uri: Trojan URI string
            
        Returns:
            ProxyNode object or None if parsing fails
        """
        try:
            # Remove protocol prefix
            content = uri[9:]  # Remove "trojan://"
            
            # Split name
            if '#' in content:
                main_part, name_encoded = content.rsplit('#', 1)
                name = urllib.parse.unquote(name_encoded)
            else:
                main_part = content
                name = "Trojan-Node"
            
            # Split params
            params = {}
            if '?' in main_part:
                main_part, params_str = main_part.split('?', 1)
                params = dict(urllib.parse.parse_qsl(params_str))
            
            # Parse password@server:port
            password, server_port = main_part.rsplit('@', 1)
            server, port_str = server_port.rsplit(':', 1)
            port = int(port_str)
            
            return ProxyNode(
                name=name,
                type='trojan',
                server=server,
                port=port,
                extra={
                    'password': password,
                    'sni': params.get('sni', server),
                    'skip-cert-verify': params.get('allowInsecure', 'false') == 'true',
                    'udp': True
                }
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse Trojan URI: {e}")
            return None
    
    def parse_vless(self, uri: str) -> Optional[ProxyNode]:
        """
        Parse VLESS URI.
        
        Format: vless://uuid@server:port?params#name
        
        Args:
            uri: VLESS URI string
            
        Returns:
            ProxyNode object or None if parsing fails
        """
        try:
            # Remove protocol prefix
            content = uri[8:]  # Remove "vless://"
            
            # Split name
            if '#' in content:
                main_part, name_encoded = content.rsplit('#', 1)
                name = urllib.parse.unquote(name_encoded)
            else:
                main_part = content
                name = "VLESS-Node"
            
            # Split params
            params = {}
            if '?' in main_part:
                main_part, params_str = main_part.split('?', 1)
                params = dict(urllib.parse.parse_qsl(params_str))
            
            # Parse uuid@server:port
            uuid, server_port = main_part.rsplit('@', 1)
            server, port_str = server_port.rsplit(':', 1)
            port = int(port_str)
            
            return ProxyNode(
                name=name,
                type='vless',
                server=server,
                port=port,
                extra={
                    'uuid': uuid,
                    'network': params.get('type', 'tcp'),
                    'tls': params.get('security', 'none') != 'none',
                    'servername': params.get('sni', server),
                    'udp': True
                }
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse VLESS URI: {e}")
            return None
    
    def _safe_base64_decode(self, data: str) -> str:
        """
        Safely decode base64 with padding correction.
        
        Args:
            data: Base64 encoded string
            
        Returns:
            Decoded string
        """
        # Handle URL-safe base64
        data = data.replace('-', '+').replace('_', '/')
        
        # Add padding if needed
        padding_needed = len(data) % 4
        if padding_needed:
            data += '=' * (4 - padding_needed)
        
        decoded_bytes = base64.b64decode(data)
        return decoded_bytes.decode('utf-8')
