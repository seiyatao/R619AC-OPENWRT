#!/bin/bash
set -euo pipefail

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# 只改变新生成无线接口的默认值，不覆盖保留的无线配置。
patch --batch --forward --fuzz=0 -p1 < "$repo_dir/patches/openwrt/100-enable-default-wifi.patch"
bash "$repo_dir/scripts/prepare-packages.sh"

#=============================================================
# diy-part2.sh — 自定义配置加载后执行
# 用途：修改默认设置（主机名、时区、IP 等）
#=============================================================

# 修改默认 LAN IP 为 192.168.2.1
sed -i 's/192\.168\.1\.1/192.168.2.1/g' package/base-files/files/bin/config_generate

# 使用 UCI 设置默认值，避免修改 config_generate 中的 shell 语法。
mkdir -p package/base-files/files/etc/uci-defaults
cat > package/base-files/files/etc/uci-defaults/99-r619ac-defaults <<'EOF'
#!/bin/sh
uci -q batch <<'UCI'
set system.@system[0].hostname='R619AC'
set system.@system[0].timezone='CST-8'
set system.@system[0].zonename='Asia/Shanghai'
set luci.main.lang='zh_cn'
set luci.main.mediaurlbase='/luci-static/bootstrap'
set luci.languages.zh_cn='简体中文 (Simplified Chinese)'
commit system
commit luci
UCI
exit 0
EOF

# Xray 26.10.21 的 go.mod 要求 Go 1.27，使用官方 feed 的原生多版本工具链。
test -f feeds/packages/lang/golang/golang1.27/Makefile
sed -i 's/^GO_DEFAULT_VERSION:=.*/GO_DEFAULT_VERSION:=1.27/' feeds/packages/lang/golang/golang-values.mk

# 强制选择 Passwall 配套核心，防止同名包落到官方版本。
rm -rf feeds/packages/net/xray-core
rm -rf package/feeds/packages/xray-core
./scripts/feeds install -p passwall_packages -f xray-core

# SmartDNS 及其 LuCI 使用官方 feeds；仅补充官方缺少的 Lucky。
clone_at() {
  local url="$1" revision="$2" destination="$3"
  test ! -e "$destination"
  git init -q "$destination"
  git -C "$destination" remote add origin "$url"
  git -C "$destination" fetch --depth=1 origin "$revision"
  git -C "$destination" checkout -q --detach FETCH_HEAD
}

clone_at https://github.com/sirpdboy/luci-app-lucky.git \
  31f068051de9798c0fb8f3e1d8e32310b4063e5d package/lucky

# 翻译由同一份 Passwall 源码编译成原生 APK，不在开机时下载或安装 IPK。
test -s feeds/passwall_luci/luci-app-passwall/po/zh_Hans/passwall.po

echo ">>> diy-part2.sh: 默认配置已修改"
echo "    主机名: R619AC"
echo "    时区: CST-8 (中国)"
echo "    LAN IP: 192.168.2.1"
