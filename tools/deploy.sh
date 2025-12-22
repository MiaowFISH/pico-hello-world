#!/bin/bash
# Linux/macOS Shell脚本 - 快速部署到Pico
cd "$(dirname "$0")/.."
python3 tools/deploy.py "$@"
