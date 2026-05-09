#!/bin/bash
#=============================================================
# diy-part1.sh — feeds 更新前执行
# 用途：添加第三方插件源
#=============================================================

# ===== 科学上网及常用插件合集（kenzok8 包含了 Passwall、AdGuardHome、SmartDNS 等所有所需插件）=====
echo "src-git kenzo https://github.com/kenzok8/openwrt-packages.git;master" >> feeds.conf.default
echo "src-git small https://github.com/kenzok8/small.git;master" >> feeds.conf.default

# ===== Argon 主题 + 配置面板 =====
echo "src-git argon https://github.com/jerrykuku/luci-theme-argon.git;master" >> feeds.conf.default
echo "src-git argon_config https://github.com/jerrykuku/luci-app-argon-config.git;master" >> feeds.conf.default



echo ""
echo ">>> diy-part1.sh: 第三方 feeds 已添加"
echo "==========================================="
cat feeds.conf.default
echo "==========================================="
