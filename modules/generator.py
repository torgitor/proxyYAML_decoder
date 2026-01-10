"""
Clash Config Generator Module
Generates valid Clash YAML configuration from parsed proxy nodes
"""

import yaml
import logging
from typing import Dict, List, Any, Optional
from .parser import ProxyNode

logger = logging.getLogger(__name__)


class ClashConfigGenerator:
    """
    Generates Clash-compatible YAML configuration files.
    Supports custom templates, proxy groups, and rule sets.
    """
    
    # Default configuration values
    DEFAULT_CONFIG = {
        'port': 7890,
        'socks-port': 7891,
        'allow-lan': True,
        'mode': 'rule',
        'log-level': 'info',
        'ipv6': False,
        'external-controller': '127.0.0.1:9090'
    }
    
    # URL for connectivity testing
    TEST_URL = 'http://www.gstatic.com/generate_204'
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the generator.
        
        Args:
            config: Optional base configuration override
        """
        self.config = {**self.DEFAULT_CONFIG}
        if config:
            self.config.update(config)
    
    def generate(self, nodes: List[ProxyNode]) -> Dict[str, Any]:
        """
        Generate complete Clash configuration.
        
        Args:
            nodes: List of ProxyNode objects
            
        Returns:
            Complete Clash configuration dictionary
        """
        if not nodes:
            raise ValueError("No proxy nodes provided")
        
        # Build proxies list
        proxies = [node.to_clash_dict() for node in nodes]
        
        # Build proxy groups
        proxy_groups = self._build_proxy_groups(nodes)
        
        # Build rules
        rules = self._build_rules()
        
        # Assemble final config
        config = {
            **self.config,
            'proxies': proxies,
            'proxy-groups': proxy_groups,
            'rules': rules
        }
        
        logger.info(f"Generated config with {len(proxies)} proxies")
        return config
    
    def _build_proxy_groups(self, nodes: List[ProxyNode]) -> List[Dict[str, Any]]:
        """
        Build proxy groups configuration.
        
        Args:
            nodes: List of ProxyNode objects
            
        Returns:
            List of proxy group configurations
        """
        proxy_names = [node.name for node in nodes]
        
        # Categorize nodes by region (based on name keywords)
        regions = self._categorize_by_region(nodes)
        
        groups = []
        
        # Main selection group
        main_group_proxies = ['Auto', 'Fallback']
        # Add region groups if they have nodes
        for region, region_nodes in regions.items():
            if region_nodes:
                main_group_proxies.append(region)
        main_group_proxies.extend(proxy_names)
        
        groups.append({
            'name': 'Proxy',
            'type': 'select',
            'proxies': main_group_proxies
        })
        
        # Auto-test group (all nodes)
        groups.append({
            'name': 'Auto',
            'type': 'url-test',
            'proxies': proxy_names,
            'url': self.TEST_URL,
            'interval': 300
        })
        
        # Fallback group
        groups.append({
            'name': 'Fallback',
            'type': 'fallback',
            'proxies': proxy_names,
            'url': self.TEST_URL,
            'interval': 300
        })
        
        # Region-specific groups
        for region, region_nodes in regions.items():
            if region_nodes:
                groups.append({
                    'name': region,
                    'type': 'url-test',
                    'proxies': [n.name for n in region_nodes],
                    'url': self.TEST_URL,
                    'interval': 300
                })
        
        return groups
    
    def _categorize_by_region(self, nodes: List[ProxyNode]) -> Dict[str, List[ProxyNode]]:
        """
        Categorize nodes by region based on name keywords.
        
        Args:
            nodes: List of ProxyNode objects
            
        Returns:
            Dictionary mapping region names to node lists
        """
        # Region keywords mapping
        region_keywords = {
            '香港节点': ['香港', 'HK', 'Hong Kong', 'HongKong'],
            '日本节点': ['日本', 'JP', 'Japan', 'Tokyo'],
            '台湾节点': ['台湾', 'TW', 'Taiwan'],
            '新加坡节点': ['新加坡', 'SG', 'Singapore'],
            '美国节点': ['美国', 'US', 'USA', 'United States', 'America'],
            '韩国节点': ['韩国', 'KR', 'Korea'],
            '英国节点': ['英国', 'UK', 'Britain', 'England'],
            '澳洲节点': ['澳洲', 'AU', 'Australia']
        }
        
        regions = {region: [] for region in region_keywords}
        
        for node in nodes:
            name_lower = node.name.lower()
            for region, keywords in region_keywords.items():
                for keyword in keywords:
                    if keyword.lower() in name_lower:
                        regions[region].append(node)
                        break
        
        # Remove empty regions
        return {k: v for k, v in regions.items() if v}
    
    def _build_rules(self) -> List[str]:
        """
        Build routing rules.
        
        Returns:
            List of rule strings
        """
        return [
            # Direct connections for China
            'GEOIP,CN,DIRECT',
            # Default to proxy
            'MATCH,Proxy'
        ]
    
    def to_yaml(self, config: Dict[str, Any]) -> str:
        """
        Convert configuration to YAML string.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            YAML formatted string
        """
        # Custom representer to handle unicode properly
        yaml.add_representer(
            str,
            lambda dumper, data: dumper.represent_scalar('tag:yaml.org,2002:str', data)
        )
        
        return yaml.dump(
            config,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False
        )
    
    def save(self, config: Dict[str, Any], filepath: str) -> int:
        """
        Save configuration to YAML file.
        
        Args:
            config: Configuration dictionary
            filepath: Output file path
            
        Returns:
            Number of bytes written
        """
        yaml_content = self.to_yaml(config)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            bytes_written = f.write(yaml_content)
        
        logger.info(f"Saved config to {filepath}: {bytes_written} bytes")
        return bytes_written
    
    def generate_and_save(self, nodes: List[ProxyNode], filepath: str) -> Dict[str, Any]:
        """
        Generate config and save to file.
        
        Args:
            nodes: List of ProxyNode objects
            filepath: Output file path
            
        Returns:
            Generated configuration dictionary
        """
        config = self.generate(nodes)
        self.save(config, filepath)
        return config
