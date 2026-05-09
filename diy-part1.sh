#!/bin/bash
#=============================================================
# diy-part1.sh — feeds 更新前执行
# 用途：添加第三方插件源
#=============================================================

# ===== 科学上网：使用 xiaorouji 官方源 (完美适配 24.10) =====
echo "src-git passwall_packages https://github.com/xiaorouji/openwrt-passwall-packages.git;main" >> feeds.conf.default
echo "src-git passwall https://github.com/xiaorouji/openwrt-passwall.git;main" >> feeds.conf.default






echo ""
echo ">>> diy-part1.sh: 第三方 feeds 已添加"
echo "==========================================="
cat feeds.conf.default
echo "==========================================="
