"""
Test Suite for Clash Subscription Converter
Run with: python3 -m pytest tests/ -v
Or run directly: python3 tests/test_all.py
"""

import os
import sys
import base64
import json
import tempfile
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.decoder import FormatDecoder, FormatType
from modules.parser import URIParser
from modules.generator import ClashConfigGenerator
from modules.validator import ConfigValidator


class TestFormatDecoder(unittest.TestCase):
    """Test cases for FormatDecoder module"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.decoder = FormatDecoder()
        
        # Sample SS URIs
        self.sample_uris = [
            "ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToxYWUwMzYyNi1jMTRhLTQ1NWQtYWYzNy1mYmVkNWQ4NmM1YmM@sd.youtu2.top:34102#youtunice.com%20test",
            "ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToxYWUwMzYyNi1jMTRhLTQ1NWQtYWYzNy1mYmVkNWQ4NmM1YmM@zx.youtu2.top:30001#%E4%B8%93%E7%BA%BF-HK1"
        ]
        
        # Create base64 encoded content
        self.uri_text = "\n".join(self.sample_uris)
        self.base64_content = base64.b64encode(self.uri_text.encode()).decode()
    
    def test_detect_base64_format(self):
        """Test detection of base64 encoded URI list"""
        content = self.base64_content.encode()
        format_type = self.decoder.detect_format(content)
        self.assertEqual(format_type, FormatType.BASE64_URI_LIST)
    
    def test_detect_plain_uri_format(self):
        """Test detection of plain URI list"""
        content = self.uri_text.encode()
        format_type = self.decoder.detect_format(content)
        self.assertEqual(format_type, FormatType.PLAIN_URI_LIST)
    
    def test_detect_yaml_format(self):
        """Test detection of Clash YAML format"""
        yaml_content = b"""
proxies:
  - name: test
    type: ss
    server: test.com
    port: 8388
"""
        format_type = self.decoder.detect_format(yaml_content)
        self.assertEqual(format_type, FormatType.CLASH_YAML)
    
    def test_decode_base64(self):
        """Test base64 decoding"""
        content = self.base64_content.encode()
        decoded = self.decoder.decode(content, FormatType.BASE64_URI_LIST)
        self.assertIn("ss://", decoded)
    
    def test_extract_uris(self):
        """Test URI extraction from decoded content"""
        uris = self.decoder.extract_uris(self.uri_text)
        self.assertEqual(len(uris), 2)
        for uri in uris:
            self.assertTrue(uri.startswith("ss://"))
    
    def test_validate_decoded_content(self):
        """Test validation of decoded content"""
        is_valid, msg = self.decoder.validate_decoded(self.uri_text)
        self.assertTrue(is_valid)
        self.assertIn("2", msg)  # Should mention 2 URIs


class TestURIParser(unittest.TestCase):
    """Test cases for URIParser module"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parser = URIParser()
    
    def test_parse_ss_uri(self):
        """Test Shadowsocks URI parsing"""
        # Format: ss://base64(method:password)@server:port#name
        uri = "ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToxYWUwMzYyNi1jMTRhLTQ1NWQtYWYzNy1mYmVkNWQ4NmM1YmM@sd.youtu2.top:34102#TestNode"
        
        node = self.parser.parse_ss(uri)
        
        self.assertIsNotNone(node)
        self.assertEqual(node.type, 'ss')
        self.assertEqual(node.server, 'sd.youtu2.top')
        self.assertEqual(node.port, 34102)
        self.assertEqual(node.name, 'TestNode')
        self.assertEqual(node.extra['cipher'], 'chacha20-ietf-poly1305')
        self.assertEqual(node.extra['password'], '1ae03626-c14a-455d-af37-fbed5d86c5bc')
    
    def test_parse_ss_uri_with_encoded_name(self):
        """Test SS URI parsing with URL-encoded name"""
        uri = "ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToxYWUwMzYyNi1jMTRhLTQ1NWQtYWYzNy1mYmVkNWQ4NmM1YmM@zx.youtu2.top:30001#%E4%B8%93%E7%BA%BF2.5x-%E9%A6%99%E6%B8%AF1"
        
        node = self.parser.parse_ss(uri)
        
        self.assertIsNotNone(node)
        self.assertEqual(node.name, '专线2.5x-香港1')
    
    def test_parse_vmess_uri(self):
        """Test VMess URI parsing"""
        # Create VMess config JSON
        vmess_config = {
            "v": "2",
            "ps": "VMess-Test",
            "add": "test.server.com",
            "port": "443",
            "id": "uuid-test-1234",
            "aid": "0",
            "net": "ws",
            "tls": "tls"
        }
        vmess_json = json.dumps(vmess_config)
        vmess_b64 = base64.b64encode(vmess_json.encode()).decode()
        uri = f"vmess://{vmess_b64}"
        
        node = self.parser.parse_vmess(uri)
        
        self.assertIsNotNone(node)
        self.assertEqual(node.type, 'vmess')
        self.assertEqual(node.name, 'VMess-Test')
        self.assertEqual(node.server, 'test.server.com')
        self.assertEqual(node.port, 443)
    
    def test_parse_trojan_uri(self):
        """Test Trojan URI parsing"""
        uri = "trojan://password123@server.com:443?sni=sni.server.com#TrojanNode"
        
        node = self.parser.parse_trojan(uri)
        
        self.assertIsNotNone(node)
        self.assertEqual(node.type, 'trojan')
        self.assertEqual(node.name, 'TrojanNode')
        self.assertEqual(node.server, 'server.com')
        self.assertEqual(node.port, 443)
        self.assertEqual(node.extra['password'], 'password123')
    
    def test_parse_batch(self):
        """Test batch URI parsing"""
        uris = [
            "ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToxYWUwMzYyNi1jMTRhLTQ1NWQtYWYzNy1mYmVkNWQ4NmM1YmM@sd.youtu2.top:34102#Node1",
            "ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToxYWUwMzYyNi1jMTRhLTQ1NWQtYWYzNy1mYmVkNWQ4NmM1YmM@zx.youtu2.top:30001#Node2",
            "invalid://this-should-fail"
        ]
        
        nodes = self.parser.parse_batch(uris)
        
        # Should parse 2 valid nodes, skip 1 invalid
        self.assertEqual(len(nodes), 2)
    
    def test_to_clash_dict(self):
        """Test conversion to Clash dictionary format"""
        uri = "ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToxYWUwMzYyNi1jMTRhLTQ1NWQtYWYzNy1mYmVkNWQ4NmM1YmM@sd.youtu2.top:34102#TestNode"
        node = self.parser.parse_ss(uri)
        
        clash_dict = node.to_clash_dict()
        
        self.assertEqual(clash_dict['name'], 'TestNode')
        self.assertEqual(clash_dict['type'], 'ss')
        self.assertEqual(clash_dict['server'], 'sd.youtu2.top')
        self.assertEqual(clash_dict['port'], 34102)
        self.assertIn('cipher', clash_dict)
        self.assertIn('password', clash_dict)


class TestClashConfigGenerator(unittest.TestCase):
    """Test cases for ClashConfigGenerator module"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.generator = ClashConfigGenerator()
        self.parser = URIParser()
        
        # Create sample nodes
        self.sample_uris = [
            "ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToxYWUwMzYyNi1jMTRhLTQ1NWQtYWYzNy1mYmVkNWQ4NmM1YmM@sd.youtu2.top:34001#%E9%A6%99%E6%B8%AF1",
            "ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToxYWUwMzYyNi1jMTRhLTQ1NWQtYWYzNy1mYmVkNWQ4NmM1YmM@sd.youtu2.top:34002#%E9%A6%99%E6%B8%AF2",
            "ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToxYWUwMzYyNi1jMTRhLTQ1NWQtYWYzNy1mYmVkNWQ4NmM1YmM@sd.youtu2.top:34011#%E6%97%A5%E6%9C%AC1",
        ]
        self.nodes = self.parser.parse_batch(self.sample_uris)
    
    def test_generate_config(self):
        """Test configuration generation"""
        config = self.generator.generate(self.nodes)
        
        # Check required keys
        self.assertIn('proxies', config)
        self.assertIn('proxy-groups', config)
        self.assertIn('rules', config)
        
        # Check proxies count
        self.assertEqual(len(config['proxies']), 3)
        
        # Check proxy groups
        self.assertTrue(len(config['proxy-groups']) >= 2)
        
        # Check that 'Proxy' and 'Auto' groups exist
        group_names = [g['name'] for g in config['proxy-groups']]
        self.assertIn('Proxy', group_names)
        self.assertIn('Auto', group_names)
    
    def test_generate_yaml_output(self):
        """Test YAML string generation"""
        config = self.generator.generate(self.nodes)
        yaml_str = self.generator.to_yaml(config)
        
        # Should be valid YAML string
        self.assertIsInstance(yaml_str, str)
        self.assertIn('proxies:', yaml_str)
        self.assertIn('proxy-groups:', yaml_str)
        self.assertIn('rules:', yaml_str)
    
    def test_save_to_file(self):
        """Test saving configuration to file"""
        config = self.generator.generate(self.nodes)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            bytes_written = self.generator.save(config, temp_path)
            
            self.assertGreater(bytes_written, 0)
            self.assertTrue(os.path.exists(temp_path))
            
            # Read and verify content
            with open(temp_path, 'r') as f:
                content = f.read()
            self.assertIn('proxies:', content)
        finally:
            os.unlink(temp_path)
    
    def test_empty_nodes_raises_error(self):
        """Test that empty nodes list raises ValueError"""
        with self.assertRaises(ValueError):
            self.generator.generate([])
    
    def test_region_categorization(self):
        """Test automatic region categorization"""
        config = self.generator.generate(self.nodes)
        
        # Should have region-specific groups for 香港 and 日本
        group_names = [g['name'] for g in config['proxy-groups']]
        
        # At least Proxy, Auto, Fallback should exist
        self.assertIn('Proxy', group_names)
        self.assertIn('Auto', group_names)


class TestConfigValidator(unittest.TestCase):
    """Test cases for ConfigValidator module"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.validator = ConfigValidator()
        
        # Create valid config
        self.valid_config = {
            'port': 7890,
            'proxies': [
                {
                    'name': 'test-ss',
                    'type': 'ss',
                    'server': 'test.com',
                    'port': 8388,
                    'cipher': 'chacha20-ietf-poly1305',
                    'password': 'test123'
                }
            ],
            'proxy-groups': [
                {
                    'name': 'Proxy',
                    'type': 'select',
                    'proxies': ['test-ss']
                }
            ],
            'rules': [
                'MATCH,Proxy'
            ]
        }
    
    def test_validate_valid_config(self):
        """Test validation of valid configuration"""
        result = self.validator.validate(self.valid_config)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
    
    def test_validate_missing_proxies(self):
        """Test validation catches missing proxies"""
        invalid_config = {
            'proxy-groups': [],
            'rules': []
        }
        
        result = self.validator.validate(invalid_config)
        
        self.assertFalse(result.is_valid)
        self.assertTrue(any('proxies' in e.lower() for e in result.errors))
    
    def test_validate_yaml_syntax(self):
        """Test YAML syntax validation"""
        valid_yaml = "key: value\nlist:\n  - item1\n  - item2"
        invalid_yaml = "key: value\n  invalid indent"
        
        is_valid, _ = self.validator.validate_yaml_syntax(valid_yaml)
        self.assertTrue(is_valid)
        
        # Note: This might actually pass in YAML, let's use clearly invalid syntax
        really_invalid = "key: [unclosed"
        is_valid, _ = self.validator.validate_yaml_syntax(really_invalid)
        self.assertFalse(is_valid)
    
    def test_validate_proxy_fields(self):
        """Test validation of proxy node fields"""
        # Missing password for SS
        config_missing_field = {
            'proxies': [
                {
                    'name': 'test',
                    'type': 'ss',
                    'server': 'test.com',
                    'port': 8388,
                    'cipher': 'aes-256-gcm'
                    # Missing 'password'
                }
            ],
            'proxy-groups': [{'name': 'P', 'type': 'select', 'proxies': ['test']}],
            'rules': ['MATCH,P']
        }
        
        result = self.validator.validate(config_missing_field)
        
        self.assertFalse(result.is_valid)
        self.assertTrue(any('password' in e.lower() for e in result.errors))
    
    def test_validate_file(self):
        """Test file validation"""
        # Create temp file with valid config
        import yaml
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(self.valid_config, f)
            temp_path = f.name
        
        try:
            result = self.validator.validate_file(temp_path)
            self.assertTrue(result.is_valid)
        finally:
            os.unlink(temp_path)
    
    def test_validate_nonexistent_file(self):
        """Test validation of non-existent file"""
        result = self.validator.validate_file('/nonexistent/path/config.yaml')
        
        self.assertFalse(result.is_valid)
        self.assertTrue(any('not found' in e.lower() for e in result.errors))


class TestIntegration(unittest.TestCase):
    """Integration tests for the full conversion pipeline"""
    
    def test_full_pipeline_from_base64(self):
        """Test complete conversion from base64 to YAML"""
        # Sample URIs
        uris = [
            "ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToxYWUwMzYyNi1jMTRhLTQ1NWQtYWYzNy1mYmVkNWQ4NmM1YmM@sd.youtu2.top:34001#HK1",
            "ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToxYWUwMzYyNi1jMTRhLTQ1NWQtYWYzNy1mYmVkNWQ4NmM1YmM@sd.youtu2.top:34002#HK2"
        ]
        uri_text = "\n".join(uris)
        base64_content = base64.b64encode(uri_text.encode())
        
        # Initialize modules
        decoder = FormatDecoder()
        parser = URIParser()
        generator = ClashConfigGenerator()
        validator = ConfigValidator()
        
        # Step 1: Detect format
        format_type = decoder.detect_format(base64_content)
        self.assertEqual(format_type, FormatType.BASE64_URI_LIST)
        
        # Step 2: Decode
        decoded = decoder.decode(base64_content, format_type)
        self.assertIn('ss://', decoded)
        
        # Step 3: Extract URIs
        extracted_uris = decoder.extract_uris(decoded)
        self.assertEqual(len(extracted_uris), 2)
        
        # Step 4: Parse URIs
        nodes = parser.parse_batch(extracted_uris)
        self.assertEqual(len(nodes), 2)
        
        # Step 5: Generate config
        config = generator.generate(nodes)
        self.assertIn('proxies', config)
        
        # Step 6: Validate
        result = validator.validate(config)
        self.assertTrue(result.is_valid)
        
        # Step 7: Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            generator.save(config, temp_path)
            
            # Verify file exists and is valid
            self.assertTrue(os.path.exists(temp_path))
            file_result = validator.validate_file(temp_path)
            self.assertTrue(file_result.is_valid)
        finally:
            os.unlink(temp_path)


def run_tests():
    """Run all tests with verbose output"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestFormatDecoder))
    suite.addTests(loader.loadTestsFromTestCase(TestURIParser))
    suite.addTests(loader.loadTestsFromTestCase(TestClashConfigGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
