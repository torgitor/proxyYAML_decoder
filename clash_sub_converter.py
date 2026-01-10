#!/usr/bin/env python3
"""
Clash Subscription Converter - CLI Tool
Automatically downloads, decodes, and converts proxy subscriptions to Clash YAML format.

Author: LUO
Date: 2026-01-10
Version: 1.0.0

Usage:
    python3 clash_sub_converter.py --url "订阅链接"
    python3 clash_sub_converter.py --url "订阅链接" --output config.yaml
    python3 clash_sub_converter.py --file raw_subscription.txt --output config.yaml
    python3 clash_sub_converter.py  # Interactive mode
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

# Add modules to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.downloader import SubscriptionDownloader
from modules.decoder import FormatDecoder, FormatType
from modules.parser import URIParser
from modules.generator import ClashConfigGenerator
from modules.validator import ConfigValidator

# Version info
__version__ = '1.1.0'
__author__ = 'LUO'

# Project directories
PROJECT_DIR = Path(__file__).parent.absolute()
TEST_OUTPUT_DIR = PROJECT_DIR / 'test_yaml_output'
SUBSCRIBE_OUTPUT_DIR = PROJECT_DIR / 'subscribe_yaml_output'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def generate_timestamped_filename(prefix: str = 'clash_config') -> str:
    """
    Generate a filename with current timestamp.
    
    Args:
        prefix: Filename prefix (default: 'clash_config')
        
    Returns:
        Filename like 'clash_config_20260110_142530.yaml'
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{prefix}_{timestamp}.yaml"


class ClashSubscriptionConverter:
    """
    Main converter class that orchestrates the entire conversion process.
    Downloads subscription -> Decodes content -> Parses URIs -> Generates YAML
    """
    
    def __init__(
        self,
        port: int = 7890,
        socks_port: int = 7891,
        allow_lan: bool = True,
        timeout: int = 30,
        quiet: bool = False
    ):
        """
        Initialize the converter.
        
        Args:
            port: HTTP proxy port (default: 7890)
            socks_port: SOCKS5 proxy port (default: 7891)
            allow_lan: Allow LAN connections (default: True)
            timeout: Download timeout in seconds (default: 30)
            quiet: Suppress logging output (default: False)
        """
        self.quiet = quiet
        if quiet:
            logging.getLogger().setLevel(logging.WARNING)
        self.downloader = SubscriptionDownloader(timeout=timeout)
        self.decoder = FormatDecoder()
        self.parser = URIParser()
        self.generator = ClashConfigGenerator(config={
            'port': port,
            'socks-port': socks_port,
            'allow-lan': allow_lan
        })
        self.validator = ConfigValidator()
        
        # Statistics
        self.stats = {
            'download_size': 0,
            'decoded_size': 0,
            'uri_count': 0,
            'parsed_count': 0,
            'failed_count': 0,
            'format_type': None
        }
    
    def convert_from_url(self, url: str, output_path: str) -> Dict[str, Any]:
        """
        Convert subscription from URL to Clash YAML.
        
        Args:
            url: Subscription URL
            output_path: Output YAML file path
            
        Returns:
            Result dictionary with status and statistics
        """
        if not self.quiet:
            logger.info("Downloading subscription...")
        
        try:
            # Step 1: Download subscription
            content = self.downloader.download(url)
            self.stats['download_size'] = len(content)
            if not self.quiet:
                logger.info(f"Downloaded: {len(content):,} bytes")
            
            # Continue with common processing
            return self._process_content(content, output_path)
            
        except Exception as e:
            logger.error(f"❌ Conversion failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'stats': self.stats
            }
    
    def convert_from_file(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """
        Convert subscription from local file to Clash YAML.
        
        Args:
            input_path: Input file path (base64 or URI list)
            output_path: Output YAML file path
            
        Returns:
            Result dictionary with status and statistics
        """
        if not self.quiet:
            logger.info("Reading local file...")
        
        try:
            # Step 1: Read file
            with open(input_path, 'rb') as f:
                content = f.read()
            self.stats['download_size'] = len(content)
            if not self.quiet:
                logger.info(f"Read: {len(content):,} bytes")
            
            # Continue with common processing
            return self._process_content(content, output_path)
            
        except FileNotFoundError:
            logger.error(f"❌ File not found: {input_path}")
            return {
                'success': False,
                'error': f"File not found: {input_path}",
                'stats': self.stats
            }
        except Exception as e:
            logger.error(f"❌ Conversion failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'stats': self.stats
            }
    
    def _process_content(self, content: bytes, output_path: str) -> Dict[str, Any]:
        """
        Process downloaded/read content through decode->parse->generate pipeline.
        
        Args:
            content: Raw bytes content
            output_path: Output YAML file path
            
        Returns:
            Result dictionary
        """
        # Helper function for progress output
        def log(msg):
            if self.quiet:
                print(f"  {msg}")
            else:
                logger.info(msg)
        
        # Step 1: Show download/read size
        log(f"  [1/5] Downloaded {len(content):,} bytes")
        
        # Step 2: Detect format
        format_type = self.decoder.detect_format(content)
        self.stats['format_type'] = format_type.value
        log(f"  [2/5] Format: {format_type.value}")
        
        if format_type == FormatType.UNKNOWN:
            raise ValueError("Unable to detect subscription format")
        
        # Step 3: Decode content
        decoded = self.decoder.decode(content, format_type)
        self.stats['decoded_size'] = len(decoded)
        log(f"  [3/5] Decoded {len(decoded):,} characters")
        
        # Step 4: Extract URIs (if not YAML)
        if format_type != FormatType.CLASH_YAML:
            uris = self.decoder.extract_uris(decoded)
            self.stats['uri_count'] = len(uris)
            log(f"  [4/5] Found {len(uris)} proxy URIs")
            
            if not uris:
                raise ValueError("No valid proxy URIs found in subscription")
            
            # Step 5: Parse URIs
            nodes = self.parser.parse_batch(uris)
            self.stats['parsed_count'] = len(nodes)
            self.stats['failed_count'] = len(uris) - len(nodes)
            
            # Count by protocol
            protocol_counts = {}
            for node in nodes:
                p = node.type if hasattr(node, 'type') else node.get('type', 'unknown')
                protocol_counts[p] = protocol_counts.get(p, 0) + 1
            protocol_str = ', '.join([f"{k}:{v}" for k, v in protocol_counts.items()])
            log(f"  [5/5] Parsed {len(nodes)} nodes ({protocol_str})")
            
            if not nodes:
                raise ValueError("Failed to parse any proxy nodes")
            
            # Step 6: Generate config
            config = self.generator.generate(nodes)
            
        else:
            # Already YAML format, just pass through
            import yaml
            config = yaml.safe_load(decoded)
            self.stats['parsed_count'] = len(config.get('proxies', []))
        
        # Step 7: Validate config
        result = self.validator.validate(config)
        
        if result.errors:
            raise ValueError(f"Validation failed: {result.errors[0]}")
        
        # Step 8: Save file
        bytes_written = self.generator.save(config, output_path)
        
        # Print summary (only in non-quiet mode)
        if not self.quiet:
            self._print_summary(config, output_path)
        
        return {
            'success': True,
            'output_path': output_path,
            'stats': self.stats,
            'proxy_info': result.info
        }
    
    def _print_summary(self, config: Dict[str, Any], output_path: str):
        """Print conversion summary (for CLI mode only)."""
        print()
        print(f"  Conversion complete!")
        print(f"  Proxies: {len(config['proxies'])}")
        print(f"  Output: {output_path}")


def interactive_mode():
    """Run in interactive mode, prompting user for input."""
    print()
    print("  🚀 Clash Subscription Converter v{}".format(__version__))
    print("  " + "-" * 40)
    print()
    print("  Supported inputs:")
    print("    • Subscription URL")
    print("    • Local file (base64/URI list)")
    print()
    print("  Tip: Press Ctrl+C to exit anytime")
    print()
    
    # Get subscription source
    print("  Select input source:")
    print("    [1] URL  - Download from internet")
    print("    [2] File - Load from local path")
    
    while True:
        choice = input("\n  > Choice (1/2): ").strip()
        if choice in ['1', '2']:
            break
        print("  ! Invalid choice, enter 1 or 2")
    
    if choice == '1':
        print()
        print("  [URL Mode]")
        url = input("  > Enter URL: ").strip()
        if not url:
            print("  ✗ URL cannot be empty")
            sys.exit(1)
        if not url.startswith(('http://', 'https://')):
            print("  ! Warning: URL should start with http:// or https://")
            confirm = input("  > Continue anyway? (y/n): ").strip().lower()
            if confirm != 'y':
                print("  ✗ Cancelled")
                sys.exit(1)
        source_type = 'url'
        source = url
        default_dir = SUBSCRIBE_OUTPUT_DIR
        default_filename = generate_timestamped_filename('clash_config')
    else:
        print()
        print("  [File Mode]")
        filepath = input("  > Enter path: ").strip()
        if not filepath:
            print("  ✗ Path cannot be empty")
            sys.exit(1)
        if not os.path.exists(filepath):
            print(f"  ✗ File not found: {filepath}")
            sys.exit(1)
        source_type = 'file'
        source = filepath
        default_dir = TEST_OUTPUT_DIR
        default_filename = generate_timestamped_filename('test_config')
    
    # Get output path with timestamp
    default_output = str(default_dir / default_filename)
    print()
    print(f"  Output: {default_output}")
    output = input("  > Custom path (Enter=default): ").strip()
    if not output:
        output = default_output
    
    # Confirm before proceeding
    print()
    print("  " + "-" * 40)
    print("  Summary:")
    print(f"    Type   : {source_type.upper()}")
    if source_type == 'url':
        display_source = source[:45] + "..." if len(source) > 45 else source
    else:
        display_source = source
    print(f"    Source : {display_source}")
    print(f"    Output : {output}")
    print("  " + "-" * 40)
    
    confirm = input("\n  > Start conversion? (y/n): ").strip().lower()
    if confirm != 'y':
        print("  ✗ Cancelled")
        sys.exit(0)
    
    print()
    print("  Processing...")
    print()
    
    # Create converter with quiet mode (suppress logging in interactive mode)
    converter = ClashSubscriptionConverter(quiet=True)
    
    if source_type == 'url':
        result = converter.convert_from_url(source, output)
    else:
        result = converter.convert_from_file(source, output)
    
    # Final summary
    print()
    print("  " + "-" * 40)
    if result['success']:
        print("  ✓ Conversion successful!")
        print("  " + "-" * 40)
        print(f"    Output  : {result['output_path']}")
        print(f"    Proxies : {result['stats']['parsed_count']}")
        print(f"    Failed  : {result['stats']['failed_count']}")
        print(f"    Format  : {result['stats']['format_type']}")
        print()
        print("  Next: Import the YAML file into Clash")
    else:
        print("  ✗ Conversion failed")
        print("  " + "-" * 40)
        print(f"    Error: {result.get('error', 'Unknown error')}")
        print()
        print("  Tips:")
        print("    • Check URL accessibility")
        print("    • Verify subscription validity")
        print("    • Try --debug for details")
    
    print()
    return result


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Convert proxy subscriptions to Clash YAML configuration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # From URL
  python3 clash_sub_converter.py --url "https://example.com/subscribe?token=xxx"
  
  # From local file
  python3 clash_sub_converter.py --file subscription.txt --output config.yaml
  
  # Interactive mode
  python3 clash_sub_converter.py
  
  # With custom ports
  python3 clash_sub_converter.py --url "URL" --port 8080 --socks-port 8081
"""
    )
    
    parser.add_argument(
        '--url', '-u',
        help='Subscription URL to download and convert'
    )
    parser.add_argument(
        '--file', '-f',
        help='Local file to convert (base64 or URI list)'
    )
    parser.add_argument(
        '--output', '-o',
        default=None,
        help='Output YAML file path (default: auto-generated with timestamp)'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=7890,
        help='HTTP proxy port (default: 7890)'
    )
    parser.add_argument(
        '--socks-port', '-s',
        type=int,
        default=7891,
        help='SOCKS5 proxy port (default: 7891)'
    )
    parser.add_argument(
        '--timeout', '-t',
        type=int,
        default=30,
        help='Download timeout in seconds (default: 30)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'clash_sub_converter {__version__}'
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create converter
    converter = ClashSubscriptionConverter(
        port=args.port,
        socks_port=args.socks_port,
        timeout=args.timeout
    )
    
    # Determine output path with timestamp if not specified
    if args.output:
        output_path = args.output
    elif args.url:
        # URL mode -> subscribe_yaml_output folder
        output_path = str(SUBSCRIBE_OUTPUT_DIR / generate_timestamped_filename('clash_config'))
    elif args.file:
        # File mode -> test_yaml_output folder
        output_path = str(TEST_OUTPUT_DIR / generate_timestamped_filename('test_config'))
    else:
        output_path = None  # Will be handled by interactive mode
    
    # Determine mode
    if args.url:
        result = converter.convert_from_url(args.url, output_path)
    elif args.file:
        result = converter.convert_from_file(args.file, output_path)
    else:
        # Interactive mode
        result = interactive_mode()
    
    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)


if __name__ == '__main__':
    main()
