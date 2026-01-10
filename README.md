# Clash Subscription Converter

> Automated tool to convert proxy subscription links into Clash-compatible YAML configuration files.

## 📋 Overview

This tool automates the conversion of proxy subscription URLs into Clash configuration files. Instead of manually downloading, decoding base64, parsing URIs, and building YAML configs, simply provide a subscription link and get a ready-to-use Clash configuration.

**Supported Protocols:**
- Shadowsocks (SS)
- VMess
- Trojan
- VLESS

---

## ⚡ Quick Start

### Installation

```bash
cd /home/jetson/2025_FYP/proxyYAML_decoder
pip3 install -r requirements.txt
```

### Basic Usage

**Option 1: Interactive Mode (Recommended)**
```bash
python3 clash_sub_converter.py
```
The program will guide you through the conversion process step by step with a user-friendly interface.

**Option 2: URL Mode (Online Subscription)**
```bash
python3 clash_sub_converter.py --url "https://your-airport.com/subscribe?token=xxx"
```
Output saved to: `subscribe_yaml_output/subscribe_<timestamp>.yaml`

**Option 3: File Mode (Local File)**
```bash
python3 clash_sub_converter.py --file /path/to/subscription.txt
```
Output saved to: `test_yaml_output/local_<timestamp>.yaml`

---

## 📁 Output Files

| Mode | Output Directory | Filename Format |
|------|------------------|-----------------|
| `--url` | `subscribe_yaml_output/` | `subscribe_YYYYMMDD_HHMMSS.yaml` |
| `--file` | `test_yaml_output/` | `local_YYYYMMDD_HHMMSS.yaml` |
| Interactive | Based on input type | Same as above |

---

## 🎯 Command Options

```bash
python3 clash_sub_converter.py [OPTIONS]

Options:
  --url TEXT      Subscription URL to convert
  --file TEXT     Local file path to convert
  --output TEXT   Custom output file path (optional)
  --help          Show help message
```

### Examples

```bash
# Convert online subscription
python3 clash_sub_converter.py --url "https://example.com/sub?token=abc123"

# Convert local base64 file
python3 clash_sub_converter.py --file ~/Downloads/sub.txt

# Specify custom output path
python3 clash_sub_converter.py --url "https://example.com/sub" --output ~/clash/config.yaml
```

---

## 📊 Output Example

```
╔══════════════════════════════════════════════════════════════╗
║        🚀 Clash Subscription Converter v1.1.0                ║
║            Interactive Console Mode                          ║
╚══════════════════════════════════════════════════════════════╝

📥 [Step 1/5] Downloading subscription...
   ✓ Download complete (11.4 KB)

🔍 [Step 2/5] Detecting format...
   ✓ Format detected: base64

🔓 [Step 3/5] Decoding content...
   ✓ Base64 decode successful
   ✓ Found 54 URIs

📦 [Step 4/5] Parsing proxy nodes...
   ✓ Parsed 54 nodes (0 failed)
   Protocol breakdown:
     - SS: 50 nodes
     - VMess: 4 nodes

💾 [Step 5/5] Generating configuration...
   ✓ Created proxy groups
   ✓ Added routing rules
   ✓ YAML validation passed
   ✓ Saved to: subscribe_yaml_output/subscribe_20260111_143022.yaml
```

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Download timeout | Use proxy: `export http_proxy=http://127.0.0.1:7890` |
| Invalid base64 | Check if file is already plain text or YAML format |
| Parse errors | Enable debug mode to see details |
| Clash won't load | Verify YAML syntax with `python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"` |

---

## 📄 Project Structure

```
proxyYAML_decoder/
├── clash_sub_converter.py   # Main CLI program
├── config_template.yaml     # Configuration template
├── requirements.txt         # Python dependencies
├── modules/                 # Core modules
│   ├── downloader.py        # HTTP download
│   ├── decoder.py           # Format detection & decoding
│   ├── parser.py            # URI parsing (SS/VMess/Trojan/VLESS)
│   ├── generator.py         # YAML generation
│   └── validator.py         # Config validation
├── tests/                   # Test suite
├── subscribe_yaml_output/   # URL subscription outputs
└── test_yaml_output/        # Local file test outputs
```

---

## 📚 More Information

For detailed technical documentation, architecture design, and contribution guidelines, see:
- **[DEVELOPMENT.md](./DEVELOPMENT.md)** - Developer documentation

---

## 📄 License

MIT License

**Last Updated**: 2026-01-11 | **Version**: 1.1.0
