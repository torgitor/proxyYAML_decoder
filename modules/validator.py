"""
Config Validator Module
Validates generated Clash configuration for syntax and structure
"""

import yaml
import socket
import logging
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Data class for validation results"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    info: Dict[str, Any]
    
    def __bool__(self):
        return self.is_valid


class ConfigValidator:
    """
    Validates Clash configuration files.
    Checks YAML syntax, required fields, and structure.
    """
    
    # Required top-level keys in Clash config
    REQUIRED_KEYS = ['proxies', 'proxy-groups', 'rules']
    
    # Required fields for proxy nodes by type
    PROXY_REQUIRED_FIELDS = {
        'ss': ['name', 'type', 'server', 'port', 'cipher', 'password'],
        'vmess': ['name', 'type', 'server', 'port', 'uuid', 'alterId'],
        'trojan': ['name', 'type', 'server', 'port', 'password'],
        'vless': ['name', 'type', 'server', 'port', 'uuid']
    }
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """
        Perform full validation on config dictionary.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            ValidationResult object
        """
        errors = []
        warnings = []
        info = {}
        
        # Check required top-level keys
        for key in self.REQUIRED_KEYS:
            if key not in config:
                errors.append(f"Missing required key: {key}")
        
        if errors:
            return ValidationResult(False, errors, warnings, info)
        
        # Validate proxies
        proxy_errors, proxy_warnings, proxy_info = self._validate_proxies(config['proxies'])
        errors.extend(proxy_errors)
        warnings.extend(proxy_warnings)
        info.update(proxy_info)
        
        # Validate proxy-groups
        group_errors, group_warnings = self._validate_proxy_groups(
            config['proxy-groups'],
            [p['name'] for p in config['proxies']]
        )
        errors.extend(group_errors)
        warnings.extend(group_warnings)
        
        # Validate rules
        rule_warnings = self._validate_rules(config['rules'])
        warnings.extend(rule_warnings)
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, info)
    
    def validate_yaml_syntax(self, yaml_content: str) -> Tuple[bool, str]:
        """
        Validate YAML syntax.
        
        Args:
            yaml_content: YAML string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            yaml.safe_load(yaml_content)
            return True, "YAML syntax is valid"
        except yaml.YAMLError as e:
            return False, f"YAML syntax error: {e}"
    
    def validate_file(self, filepath: str) -> ValidationResult:
        """
        Validate a YAML configuration file.
        
        Args:
            filepath: Path to the YAML file
            
        Returns:
            ValidationResult object
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check YAML syntax first
            is_valid, error = self.validate_yaml_syntax(content)
            if not is_valid:
                return ValidationResult(False, [error], [], {})
            
            # Parse and validate structure
            config = yaml.safe_load(content)
            return self.validate(config)
            
        except FileNotFoundError:
            return ValidationResult(False, [f"File not found: {filepath}"], [], {})
        except Exception as e:
            return ValidationResult(False, [f"Error reading file: {e}"], [], {})
    
    def _validate_proxies(self, proxies: List[Dict]) -> Tuple[List[str], List[str], Dict]:
        """
        Validate proxy nodes list.
        
        Returns:
            Tuple of (errors, warnings, info)
        """
        errors = []
        warnings = []
        info = {
            'total_proxies': len(proxies),
            'by_type': {}
        }
        
        if not proxies:
            errors.append("No proxy nodes found")
            return errors, warnings, info
        
        names_seen = set()
        
        for i, proxy in enumerate(proxies):
            # Check for name
            if 'name' not in proxy:
                errors.append(f"Proxy {i} missing 'name' field")
                continue
            
            name = proxy['name']
            
            # Check for duplicate names
            if name in names_seen:
                warnings.append(f"Duplicate proxy name: {name}")
            names_seen.add(name)
            
            # Check for type
            if 'type' not in proxy:
                errors.append(f"Proxy '{name}' missing 'type' field")
                continue
            
            proxy_type = proxy['type']
            
            # Count by type
            info['by_type'][proxy_type] = info['by_type'].get(proxy_type, 0) + 1
            
            # Check required fields for this type
            if proxy_type in self.PROXY_REQUIRED_FIELDS:
                for field in self.PROXY_REQUIRED_FIELDS[proxy_type]:
                    if field not in proxy:
                        errors.append(f"Proxy '{name}' ({proxy_type}) missing '{field}' field")
            
            # Check port range
            if 'port' in proxy:
                port = proxy['port']
                if not isinstance(port, int) or port < 1 or port > 65535:
                    errors.append(f"Proxy '{name}' has invalid port: {port}")
        
        return errors, warnings, info
    
    def _validate_proxy_groups(
        self, 
        groups: List[Dict], 
        proxy_names: List[str]
    ) -> Tuple[List[str], List[str]]:
        """
        Validate proxy groups.
        
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        if not groups:
            errors.append("No proxy groups found")
            return errors, warnings
        
        group_names = set()
        all_valid_names = set(proxy_names)
        
        # First pass: collect group names
        for group in groups:
            if 'name' in group:
                group_names.add(group['name'])
        
        # Add group names to valid reference names
        all_valid_names.update(group_names)
        # Add special values
        all_valid_names.update(['DIRECT', 'REJECT'])
        
        # Second pass: validate references
        for group in groups:
            if 'name' not in group:
                errors.append("Proxy group missing 'name' field")
                continue
            
            name = group['name']
            
            if 'type' not in group:
                errors.append(f"Proxy group '{name}' missing 'type' field")
                continue
            
            if 'proxies' not in group:
                errors.append(f"Proxy group '{name}' missing 'proxies' field")
                continue
            
            # Check for empty proxies list
            if not group['proxies']:
                errors.append(f"Proxy group '{name}' has no proxies")
            
            # Check proxy references
            for proxy_ref in group['proxies']:
                if proxy_ref not in all_valid_names:
                    warnings.append(f"Proxy group '{name}' references unknown proxy: {proxy_ref}")
        
        return errors, warnings
    
    def _validate_rules(self, rules: List[str]) -> List[str]:
        """
        Validate routing rules.
        
        Returns:
            List of warnings
        """
        warnings = []
        
        if not rules:
            warnings.append("No routing rules defined")
            return warnings
        
        has_match = False
        for rule in rules:
            if rule.startswith('MATCH,'):
                has_match = True
                break
        
        if not has_match:
            warnings.append("No MATCH rule found (unmatched traffic may fail)")
        
        return warnings
    
    def check_connectivity(
        self, 
        proxies: List[Dict], 
        timeout: float = 3.0
    ) -> Dict[str, bool]:
        """
        Check if proxy servers are reachable (TCP connection test).
        Note: This only tests TCP connectivity, not actual proxy functionality.
        
        Args:
            proxies: List of proxy configurations
            timeout: Connection timeout in seconds
            
        Returns:
            Dictionary mapping proxy names to connectivity status
        """
        results = {}
        
        for proxy in proxies:
            name = proxy.get('name', 'unknown')
            server = proxy.get('server', '')
            port = proxy.get('port', 0)
            
            if not server or not port:
                results[name] = False
                continue
            
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                result = sock.connect_ex((server, port))
                sock.close()
                results[name] = (result == 0)
            except Exception as e:
                logger.debug(f"Connectivity check failed for {name}: {e}")
                results[name] = False
        
        return results
