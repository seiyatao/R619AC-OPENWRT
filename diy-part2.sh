#!/bin/bash
#=============================================================
# diy-part2.sh — 自定义配置加载后执行
# 用途：修改默认设置（主机名、时区、IP 等）
#=============================================================

# 修改默认主机名
sed -i 's/OpenWrt/R619AC/g' package/base-files/files/bin/config_generate

# 修改默认时区为中国 (CST-8)
sed -i "s/'UTC'/'CST-8'/g" package/base-files/files/bin/config_generate
sed -i 's/"UTC"/"CST-8"/g' package/base-files/files/bin/config_generate

# 修改默认时区名称
sed -i "s/'UTC0'/'CST-8'/g" package/base-files/files/bin/config_generate
sed -i 's/timezone=.*/timezone="CST-8"/g' package/base-files/files/bin/config_generate

# 默认 LAN IP（保持 192.168.1.1，按需修改）
# sed -i 's/192.168.1.1/192.168.10.1/g' package/base-files/files/bin/config_generate

# 移除默认的 dnsmasq，使用 dnsmasq-full（支持 ipset/nftset）
# sed -i 's/dnsmasq/dnsmasq-full/g' include/target.mk

# 移除导致 Kconfig 循环依赖报错的无用第三方包
rm -rf package/feeds/small/luci-app-fchomo
rm -rf package/feeds/small/luci-app-homeproxy
rm -rf package/feeds/small/luci-app-momo
rm -rf package/feeds/small/momo
rm -rf package/feeds/kenzo/luci-app-fchomo
rm -rf package/feeds/kenzo/luci-app-homeproxy
rm -rf package/feeds/kenzo/luci-app-momo
rm -rf package/feeds/kenzo/momo

# 移除第三方源中可能导致冲突的 argon 主题，使用单独的 jerrykuku 源
rm -rf package/feeds/kenzo/luci-theme-argon
rm -rf package/feeds/kenzo/luci-app-argon-config

echo ">>> diy-part2.sh: 默认配置已修改"
echo "    主机名: R619AC"
echo "    时区: CST-8 (中国)"
echo "    LAN IP: 192.168.1.1"
