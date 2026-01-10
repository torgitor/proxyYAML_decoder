# Clash Subscription Converter | Clash 订阅转换工具

> Automated tool to convert proxy subscription links into Clash-compatible YAML configuration files.
> 
> 自动将代理订阅链接转换为 Clash 兼容的 YAML 配置文件。

## 📋 Overview | 概述

This tool automates the conversion of proxy subscription URLs into Clash configuration files. Instead of manually downloading, decoding base64, parsing URIs, and building YAML configs, simply provide a subscription link and get a ready-to-use Clash configuration.

本工具自动化处理代理订阅 URL 到 Clash 配置文件的转换。无需手动下载、base64 解码、URI 解析和构建 YAML 配置，只需提供订阅链接即可获得可用的 Clash 配置。

**Supported Protocols | 支持的协议：**
- Shadowsocks (SS)
- VMess
- Trojan
- VLESS

---

## ⚡ Quick Start | 快速开始

### Installation | 安装

```bash
cd /home/jetson/2025_FYP/proxyYAML_decoder
pip3 install -r requirements.txt
```

### Basic Usage | 基本使用

**Option 1: Interactive Mode (Recommended) | 交互模式（推荐）**
```bash
python3 clash_sub_converter.py
```
The program will guide you through the conversion process step by step with a user-friendly interface.

程序将通过友好的界面逐步引导您完成转换过程。

**Option 2: URL Mode (Online Subscription) | URL 模式（在线订阅）**
```bash
python3 clash_sub_converter.py --url "https://your-airport.com/subscribe?token=xxx"
```
Output saved to | 输出保存到: `subscribe_yaml_output/subscribe_<timestamp>.yaml`

**Option 3: File Mode (Local File) | 文件模式（本地文件）**
```bash
python3 clash_sub_converter.py --file /path/to/subscription.txt
```
Output saved to | 输出保存到: `test_yaml_output/local_<timestamp>.yaml`

---

## 📁 Output Files | 输出文件

| Mode 模式 | Output Directory 输出目录 | Filename Format 文件名格式 |
|------|------------------|-----------------|
| `--url` | `subscribe_yaml_output/` | `subscribe_YYYYMMDD_HHMMSS.yaml` |
| `--file` | `test_yaml_output/` | `local_YYYYMMDD_HHMMSS.yaml` |
| Interactive 交互式 | Based on input type 根据输入类型 | Same as above 同上 |

---

## 🎯 Command Options | 命令选项

```bash
python3 clash_sub_converter.py [OPTIONS]

Options | 选项:
  --url TEXT      Subscription URL to convert | 要转换的订阅 URL
  --file TEXT     Local file path to convert | 要转换的本地文件路径
  --output TEXT   Custom output file path (optional) | 自定义输出路径（可选）
  --help          Show help message | 显示帮助信息
```

### Examples | 示例

```bash
# Convert online subscription | 转换在线订阅
python3 clash_sub_converter.py --url "https://example.com/sub?token=abc123"

# Convert local base64 file | 转换本地 base64 文件
python3 clash_sub_converter.py --file ~/Downloads/sub.txt

# Specify custom output path | 指定自定义输出路径
python3 clash_sub_converter.py --url "https://example.com/sub" --output ~/clash/config.yaml
```

---

## 📊 Output Example | 输出示例

```
  🚀 Clash Subscription Converter v1.1.0
  ----------------------------------------

  Supported inputs:
    • Subscription URL
    • Local file (base64/URI list)

  Tip: Press Ctrl+C to exit anytime

  Select input source:
    [1] URL  - Download from internet
    [2] File - Load from local path

  > Choice (1/2): 1

  [URL Mode]
  > Enter URL: https://example.com/subscribe?token=xxx

  Output: subscribe_yaml_output/clash_config_20260110_143022.yaml
  > Custom path (Enter=default): 

  ----------------------------------------
  Summary:
    Type   : URL
    Source : https://example.com/subscribe?token=xxx
    Output : subscribe_yaml_output/clash_config_20260110_143022.yaml
  ----------------------------------------

  > Start conversion? (y/n): y

  Processing...

    [1/5] Downloaded 11,948 bytes
    [2/5] Format: base64_uri_list
    [3/5] Decoded 8,959 characters
    [4/5] Found 54 proxy URIs
    [5/5] Parsed 54 nodes (ss:54)

  ----------------------------------------
  ✓ Conversion successful!
  ----------------------------------------
    Output  : subscribe_yaml_output/clash_config_20260110_143022.yaml
    Proxies : 54
    Failed  : 0
    Format  : base64_uri_list

  Next: Import the YAML file into Clash
```

---

## 🔧 Troubleshooting | 故障排除

| Issue 问题 | Solution 解决方案 |
|-------|----------|
| Download timeout 下载超时 | Use proxy 使用代理: `export http_proxy=http://127.0.0.1:7890` |
| Invalid base64 无效的 base64 | Check if file is already plain text or YAML 检查文件是否已是纯文本或 YAML |
| Parse errors 解析错误 | Enable debug mode to see details 启用调试模式查看详情 |
| Clash won't load Clash 无法加载 | Verify YAML syntax 验证 YAML 语法: `python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"` |

---

## 📄 Project Structure | 项目结构

```
proxyYAML_decoder/
├── clash_sub_converter.py   # Main CLI program | 主程序
├── config_template.yaml     # Configuration template | 配置模板
├── requirements.txt         # Python dependencies | Python 依赖
├── modules/                 # Core modules | 核心模块
│   ├── downloader.py        # HTTP download | HTTP 下载
│   ├── decoder.py           # Format detection & decoding | 格式检测与解码
│   ├── parser.py            # URI parsing (SS/VMess/Trojan/VLESS) | URI 解析
│   ├── generator.py         # YAML generation | YAML 生成
│   └── validator.py         # Config validation | 配置验证
├── tests/                   # Test suite | 测试套件
├── subscribe_yaml_output/   # URL subscription outputs | URL 订阅输出
└── test_yaml_output/        # Local file test outputs | 本地文件测试输出
```

---

## 📚 More Information | 更多信息

For detailed technical documentation, architecture design, and contribution guidelines, see:

详细的技术文档、架构设计和贡献指南，请参阅：

- **[DEVELOPMENT.md](./DEVELOPMENT.md)** - Developer documentation | 开发者文档

---

## 📄 License | 许可证

MIT License

**Last Updated | 最后更新**: 2026-01-10 | **Version | 版本**: 1.1.0
