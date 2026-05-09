# R619AC OpenWRT 24.10 自动编译

> 竞斗云2.0 (P&W R619AC 128M) 的 OpenWRT 固件自动化编译仓库

## 固件信息

| 项目 | 详情 |
|------|------|
| **设备** | P&W R619AC 128M (竞斗云2.0) |
| **源码** | [OpenWRT 官方](https://git.openwrt.org/openwrt/openwrt.git) `openwrt-24.10` 分支 |
| **内核** | Linux 6.6 |
| **架构** | Qualcomm IPQ4019 (ipq40xx / arm_cortex-a7) |

## 预装功能

### 核心功能
| 功能 | 包名 | 说明 |
|------|------|------|
| ✅ LuCI 中文界面 | `luci-i18n-*-zh-cn` | 含 Argon 主题 + 配置面板 |
| ✅ Passwall | `luci-app-passwall` | 科学上网（Xray 核心 + ChinaDNS-NG） |
| ✅ AdGuard Home | `luci-app-adguardhome` | DNS 广告过滤 |
| ✅ SmartDNS | `luci-app-smartdns` | DNS 加速分流 |

### 网络管理
| 功能 | 包名 | 说明 |
|------|------|------|
| ✅ MWAN3 | `luci-app-mwan3` | 多线负载均衡/故障切换 |
| ✅ Frpc / Frps | `luci-app-frpc/frps` | 内网穿透 |
| ✅ SQM QoS | `luci-app-sqm` | 智能流量控制 |
| ✅ DDNS | `luci-app-ddns` | 动态域名（Cloudflare/DNSPod） |
| ✅ UPnP | `luci-app-upnp` | 端口自动映射 |
| ✅ IPv6 | `ipv6helper` | 完整 IPv6 协议栈 |
| ✅ PPPoE | `ppp-mod-pppoe` | 备用拨号支持 |

### 存储与下载
| 功能 | 包名 | 说明 |
|------|------|------|
| ✅ Samba4 | `luci-app-samba4` | USB 硬盘网络共享 (SMB) |
| ✅ Transmission | `luci-app-transmission` | BT 下载 |
| ✅ 文件管理器 | `luci-app-filemanager` | Web 文件管理 |
| ✅ USB 3.0 | `kmod-usb3` | ext4/NTFS/FAT 文件系统 |

### 系统工具
| 功能 | 包名 | 说明 |
|------|------|------|
| ✅ KMS 服务器 | `luci-app-vlmcsd` | Windows/Office 激活 |
| ✅ 网速测试 | `luci-app-netspeedtest` | 内置测速 |
| ✅ 定时重启 | `luci-app-watchcat` | 定时/断网自动重启 |
| ✅ irqbalance | `irqbalance` | 多核中断均衡 |
| ✅ 系统监控 | `luci-app-statistics` | CPU/内存/流量统计 |
| ✅ 硬盘休眠 | `luci-app-hd-idle` | USB 硬盘省电 |

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

**通过 OpBoot（推荐）：**
1. 断电 → 按住 Reset → 通电 → 等待指示灯闪烁
2. 电脑设置静态 IP `192.168.1.2`
3. 浏览器访问 OpBoot 管理页面
4. 上传 `*-factory.ubi` 固件
5. 等待完成重启

**通过现有 OpenWRT：**
1. 登录 LuCI → 系统 → 备份/升级
2. 上传 `*-sysupgrade.bin`
3. **取消勾选** "保留配置"（从旧版升级必须！）
4. 开始升级

### 首次配置

1. 网线连接 LAN 口 → 访问 `http://192.168.1.1`
2. 默认用户 `root`，无密码
3. 设置密码 → 配置 WAN → 配置 WiFi
4. 配置 Passwall（导入订阅）
5. 按需启用其他服务（Samba / AdGuard / Transmission 等）

## 文件说明

```
.
├── .config                          # 编译配置文件（完整插件列表）
├── .github/workflows/
│   └── build-openwrt.yml            # GitHub Actions 自动编译脚本
├── diy-part1.sh                     # 添加第三方插件源
├── diy-part2.sh                     # 修改默认设置（主机名/时区）
└── README.md                        # 本文件
```

## ⚠️ 注意事项

- 从旧版（21.02 等）升级必须**全新刷入**，不保留配置
- 刷机前**备份**旧的 WAN/WiFi/防火墙/科学上网节点配置
- 128M NAND 空间充裕，当前配置不会超出限制
- AdGuardHome 和 SmartDNS 不建议同时启用（端口冲突）

## 致谢

- [OpenWRT](https://openwrt.org/) 官方项目
- [P3TERX/Actions-OpenWrt](https://github.com/P3TERX/Actions-OpenWrt) 编译模板
- [xiaorouji/openwrt-passwall](https://github.com/xiaorouji/openwrt-passwall) Passwall
- [jerrykuku/luci-theme-argon](https://github.com/jerrykuku/luci-theme-argon) Argon 主题
- [kenzok8/openwrt-packages](https://github.com/kenzok8/openwrt-packages) 第三方插件合集
