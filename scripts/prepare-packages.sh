#!/bin/bash
set -euo pipefail

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
for patch_file in "$repo_dir"/patches/packages/*.patch; do
  patch --dry-run --batch --forward --fuzz=0 -p1 -d feeds/packages < "$patch_file"
done
for patch_file in "$repo_dir"/patches/packages/*.patch; do
  patch --batch --forward --fuzz=0 -p1 -d feeds/packages < "$patch_file"
done

echo '软件包修复已应用：Samba 4.22.11、Transmission 挂载保护'
