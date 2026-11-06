#!/bin/bash
set -euo pipefail
#=============================================================
# diy-part1.sh — feeds 更新前执行
# 用途：加载全部固定版本的官方及第三方插件源
#=============================================================

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cp "$repo_dir/feeds.conf.default" feeds.conf.default
echo ""
echo ">>> diy-part1.sh: 全部 feeds 已固定提交，保留原有插件版本"
echo "==========================================="
cat feeds.conf.default
echo "==========================================="
