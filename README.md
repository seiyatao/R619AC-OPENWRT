# R619AC OpenWRT 25.12 自动编译

> 竞斗云2.0 (P&W R619AC 128M) 的 OpenWRT 固件自动化编译仓库

当前为 **25.12.6 迁移测试版**。GitHub 编译、组件及版本校验通过后发布为 Pre-release；
尚需在实机验证网口、双频 WiFi、代理和存储功能。当前路由器不会自动升级。

## 固件信息

| 项目 | 详情 |
|------|------|
| **设备** | P&W R619AC 128M (竞斗云2.0) |
| **源码** | [OpenWRT 官方](https://git.openwrt.org/openwrt/openwrt.git) `v25.12.6` 标签 |
| **内核** | Linux 6.12 |
| **架构** | Qualcomm IPQ4019 (`ipq40xx/generic` / `arm_cortex-a7_neon-vfpv4`) |
| **包管理器** | APK；不能安装原来的 24.10 IPK 包 |
| **Passwall / Xray** | `26.10.22-r2` / `26.10.21`，中文与主程序同源码编译 |
| **Go** | 官方 packages feed 的 `1.27.3`，用于编译新版 Xray |

### 源码固定与构建检查

- 官方主源码固定发行标签，官方 packages 固定 25.12 安全维护分支的提交。
- Passwall、配套核心和 Lucky 均固定提交，详见 `diy-part1.sh` 和 `diy-part2.sh`。
- SmartDNS 和其管理界面使用官方 feed，去掉旧 LEDE 分支及开机安装中文 IPK 的方式。
- `make defconfig` 后检查必需组件，防止未知配置被静默移除。
- 发布前检查固件 manifest 中的功能包、uhttpd、odhcpd、OpenSSL、Mbed TLS 和 Xray 版本。
- 固件附件保留 `build-sources.txt`、`build.config` 和软件包 manifest，便于追溯。

## 预装功能

### 核心功能
| 功能 | 包名 | 说明 |
|------|------|------|
| ✅ LuCI 中文界面 | `luci-i18n-*-zh-cn` | 使用默认 Bootstrap 主题 |
| ✅ Passwall | `luci-app-passwall` | 科学上网（Xray 核心 + ChinaDNS-NG） |
| ✅ SmartDNS | `luci-app-smartdns` | DNS 加速分流 |
| ✅ Lucky | `luci-app-lucky` | DDNS、端口转发与反向代理 |

### 网络管理
| 功能 | 包名 | 说明 |
|------|------|------|
| ✅ MWAN3 | `luci-app-mwan3` | 多线负载均衡/故障切换 |
| ✅ SQM QoS | `luci-app-sqm` | 智能流量控制 |
| ✅ DDNS | `luci-app-ddns` | 动态域名（Cloudflare/DNSPod） |
| ✅ UPnP | `luci-app-upnp` | 端口自动映射 |
| ✅ IPv6 | `odhcp6c` / `odhcpd-ipv6only` | IPv6 地址获取、DHCPv6 与 RA |
| ✅ PPPoE | `ppp-mod-pppoe` | 备用拨号支持 |

### 存储与下载
| 功能 | 包名 | 说明 |
|------|------|------|
| ✅ Samba4 | `luci-app-samba4` | USB 硬盘网络共享 (SMB) |
| ✅ wsdd2 | `wsdd2` | Windows 网络发现 |
| ✅ Transmission | `luci-app-transmission` | BT 下载 |
| ✅ MiniDLNA | `luci-app-minidlna` | 局域网媒体服务器 |
| ✅ smartmontools | `smartmontools` | 硬盘健康状态检查 |

### 系统工具
| 功能 | 包名 | 说明 |
|------|------|------|
| ✅ 定时重启 | `luci-app-watchcat` | 定时/断网自动重启 |
| ✅ irqbalance | `irqbalance` | 多核中断均衡 |
| ✅ 系统监控 | `luci-app-statistics` | CPU/内存/流量统计 |

## 使用方法

### 编译固件

1. **Fork 本仓库**
2. 进入 **Actions** → **Build OpenWrt for R619AC**
3. 点击 **Run workflow** → 开始编译
4. 等待 ~2-3 小时
5. 从 **Releases** 下载固件

### 自定义配置

如需修改编译配置（增删插件），可以：

1. 触发 workflow 时开启 **SSH 远程调试**
2. 通过 SSH 连接后运行 `cd openwrt && make menuconfig`
3. 保存配置后输入 `exit` 继续编译

### 刷机

**从当前正常工作的 24.10 升级到 25.12：**

1. 导出 LuCI 系统备份，并单独保存 `/etc/lucky/`、Passwall 自定义分流/直连清单及挂载、共享配置。
2. 在电脑保存当前可用的 24.10 固件，确认可以进入 OpBoot 恢复界面。
3. 在路由器旁用网线进入 LuCI，上传本机型 `*-sysupgrade.bin`，确认镜像兼容性检查通过；不要强制刷入。
4. 官方支持多数 24.10 到 25.12 的配置迁移，可尝试保留配置；额外安装的软件和自定义文件不保证保留。
5. 升级后检查所有 LAN 口、WAN、2.4G/5G WiFi、Passwall 分流、Lucky、硬盘挂载、Samba、DLNA 和 Transmission。
6. 旧 `/etc/opkg/` 软件源、IPK 和旧内核模块不能用于 25.12；有自定义软件源时重新配置对应 APK 源。
7. 如果网口、无线或存储异常，先保存日志并使用已知可用固件回退，不反复强刷。

**首次刷机或需要恢复时：保留已有官方打底经验**

以下是此前本机验证过的 24.10 恢复流程，不代表已验证从 OpBoot 首刷 25.12 自编译固件。

1. 断电 → 按住 Reset → 通电 → 等待指示灯闪烁
2. 电脑设置静态 IP `192.168.1.2`
3. 浏览器访问 OpBoot 管理页面
4. 先上传官方原版 `openwrt-24.10.0-ipq40xx-generic-p2w_r619ac-128m-squashfs-factory.ubi`
5. 等待完成重启，进入官方 OpenWrt 后完成基础访问确认
6. 登录 LuCI → 系统 → 备份/升级
7. 上传本仓库编译出的 `*-sysupgrade.bin`
8. 勾选“保留配置”，开始升级

### 首次配置

1. 网线连接 LAN 口 → 访问 `http://192.168.2.1`
2. 默认用户 `root`，无密码
3. 设置密码 → 配置 WAN → 配置 WiFi
4. 配置 Passwall（导入订阅）
5. 按需启用其他服务（Samba / SmartDNS / Transmission 等）

## 文件说明

```
.
├── .config                          # 编译配置文件（完整插件列表）
├── .github/workflows/
│   └── build-openwrt.yml            # GitHub Actions 自动编译脚本
├── diy-part1.sh                     # 添加第三方插件源
├── diy-part2.sh                     # 修改默认设置（主机名/时区）
├── scripts/check-build.sh           # 配置、功能包和安全版本检查
└── README.md                        # 本文件
```

## ⚠️ 注意事项

- R619AC 通过 OpBoot 刷机时，建议先刷官方 24.10.0 `factory.ubi` 打底，再在官方后台保留配置刷本仓库的 `sysupgrade.bin`
- 不建议直接用 OpBoot 首刷本仓库自编译 `factory.ubi`
- 从旧版（21.02 等）升级到官方 24.10.0 打底时，建议先备份配置，再按实际情况决定是否保留配置
- 刷机前**备份**旧的 WAN/WiFi/防火墙/科学上网节点配置
- 以实际镜像生成和空间检查结果为准，预留足够的 overlay 空间。
- 保留配置升级也会保留原有公网管理入口；升级固件不会自动收紧 Lucky 转发和防火墙规则。

## 致谢

- [OpenWRT](https://openwrt.org/) 官方项目
- [P3TERX/Actions-OpenWrt](https://github.com/P3TERX/Actions-OpenWrt) 编译模板
- [Openwrt-Passwall/openwrt-passwall](https://github.com/Openwrt-Passwall/openwrt-passwall) Passwall
- [kenzok8/openwrt-packages](https://github.com/kenzok8/openwrt-packages) 第三方插件合集
