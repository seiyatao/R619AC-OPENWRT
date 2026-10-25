#!/bin/bash
set -euo pipefail

required_packages=(
  luci luci-base luci-app-package-manager luci-i18n-base-zh-cn
  luci-i18n-package-manager-zh-cn luci-theme-bootstrap
  luci-app-passwall luci-i18n-passwall-zh-cn
  xray-core v2ray-geoip v2ray-geosite chinadns-ng dnsmasq-full firewall4
  nftables-json kmod-nft-tproxy kmod-nft-socket luci-app-smartdns smartdns
  luci-i18n-smartdns-zh-cn lucky luci-app-lucky luci-i18n-lucky-zh-cn
  block-mount kmod-usb-storage kmod-usb-storage-uas kmod-usb3
  kmod-fs-ext4 kmod-fs-ntfs3 kmod-fs-exfat kmod-fs-vfat kmod-nls-utf8
  luci-app-hd-idle smartmontools wsdd2 samba4-server luci-app-samba4
  transmission-daemon transmission-web luci-app-transmission
  minidlna luci-app-minidlna mwan3 luci-app-mwan3 sqm-scripts luci-app-sqm
  luci-app-ddns luci-app-upnp odhcp6c odhcpd-ipv6only wpad-openssl
)

fail() {
  echo "校验失败：$*" >&2
  exit 1
}

check_config() {
  grep -qx 'CONFIG_TARGET_ipq40xx_generic_DEVICE_p2w_r619ac-128m=y' .config || fail '目标机型不正确'
  grep -qx 'CONFIG_USE_APK=y' .config || fail '必须使用原生 APK 包管理器'
  grep -qx 'CONFIG_LUCI_LANG_zh_Hans=y' .config || fail '未启用简体中文'
  grep -qx 'CONFIG_PACKAGE_luci-app-passwall_Nftables_Transparent_Proxy=y' .config || fail '未启用 Passwall nftables 支持'
  for package in "${required_packages[@]}"; do
    grep -qx "CONFIG_PACKAGE_${package}=y" .config || fail "必需组件未进入镜像：$package"
  done
  if grep -Eq '^CONFIG_PACKAGE_(adguardhome|luci-app-adguardhome|sing-box|geoview|v2ray-plugin)=y$' .config; then
    fail '出现已排除的组件'
  fi
  test -s feeds/passwall_luci/luci-app-passwall/po/zh_Hans/passwall.po || fail '缺少 Passwall 中文翻译源码'
  grep -qx 'GO_DEFAULT_VERSION:=1.27' feeds/packages/lang/golang/golang-values.mk || fail 'Go 默认工具链不正确'
  grep -qx 'GO_VERSION_PATCH:=3' feeds/packages/lang/golang/golang1.27/Makefile || fail 'Go 安全更新版本不正确'
  grep -qx 'PKG_VERSION:=26.10.21' package/feeds/passwall_packages/xray-core/Makefile || fail 'Xray 版本不正确'
  test ! -e package/feeds/packages/xray-core || fail '仍有同名官方 Xray 包'
}

check_version() {
  local package="$1" minimum="$2" version
  version=$(awk -v name="$package" '$1 == name && $2 == "-" { print $3; exit }' "$manifest")
  test -n "$version" || fail "产物缺少组件：$package"
  version=${version%%~*}
  dpkg --compare-versions "$version" ge "$minimum" || fail "$package 低于安全版本 $minimum"
}

case "${1:-config}" in
  config)
    check_config
    echo '配置校验通过：APK、配套核心、中文及必需功能均已选中'
    ;;
  firmware)
    shopt -s nullglob
    images=(bin/targets/ipq40xx/generic/*p2w_r619ac-128m-squashfs-sysupgrade.bin)
    manifests=(bin/targets/ipq40xx/generic/*.manifest)
    ((${#images[@]} == 1)) || fail '没有生成唯一的本机型 sysupgrade 镜像'
    ((${#manifests[@]} > 0)) || fail '没有生成软件包清单'
    for manifest in "${manifests[@]}"; do
      for package in apk-mbedtls "${required_packages[@]}"; do
        awk -v name="$package" '$1 == name && $2 == "-" { found=1 } END { exit !found }' "$manifest" || fail "产物缺少组件：$package"
      done
      check_version uhttpd 2026.08.24
      check_version odhcpd-ipv6only 2026.06.29
      check_version libopenssl3 3.5.9
      check_version xray-core 26.10.21
      check_version luci-app-passwall 26.10.22-r2
      if grep -q '^libmbedtls21 - ' "$manifest"; then
        check_version libmbedtls21 3.6.7
      fi
    done
    echo '固件清单校验通过：升级镜像、必需组件和关键安全版本齐全'
    ;;
  *) fail '参数应为 config 或 firmware' ;;
esac
