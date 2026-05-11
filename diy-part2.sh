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

# 修改默认 LAN IP 为 192.168.2.1
sed -i 's/192.168.1.1/192.168.2.1/g' package/base-files/files/bin/config_generate

# 设置 LuCI 默认语言为简体中文
mkdir -p package/base-files/files/etc/uci-defaults
cat > package/base-files/files/etc/uci-defaults/99-luci-language <<'EOF'
#!/bin/sh
uci set luci.main.lang='zh_cn'
uci set luci.languages.zh_cn='简体中文 (Simplified Chinese)'
uci commit luci
exit 0
EOF

# 移除 geoview 和 v2ray-plugin（要求 Go 版本过高，且非核心必备插件）
rm -rf feeds/passwall_packages/geoview
rm -rf package/feeds/passwall_packages/geoview
rm -rf feeds/passwall_packages/v2ray-plugin
rm -rf package/feeds/passwall_packages/v2ray-plugin

# 独立拉取缺失的第三方插件，避免引入整个 kenzo 源的冲突
git clone --depth=1 https://github.com/rufengsuixing/luci-app-adguardhome.git package/luci-app-adguardhome
git clone --depth=1 https://github.com/sirpdboy/luci-app-netspeedtest.git package/luci-app-netspeedtest
git clone --depth=1 https://github.com/cokebar/openwrt-vlmcsd.git package/vlmcsd
git clone --depth=1 https://github.com/cokebar/luci-app-vlmcsd.git package/luci-app-vlmcsd
git clone --depth=1 -b lede https://github.com/pymumu/luci-app-smartdns.git package/luci-app-smartdns

echo ">>> diy-part2.sh: 默认配置已修改"
echo "    主机名: R619AC"
echo "    时区: CST-8 (中国)"
echo "    LAN IP: 192.168.2.1"
