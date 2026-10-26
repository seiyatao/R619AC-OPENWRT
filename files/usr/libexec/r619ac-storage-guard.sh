#!/bin/sh

r619ac_storage_mount_ready() {
	awk -v target="$1" '
		{
			mount_path = $2
			gsub(/\\040/, " ", mount_path)
			gsub(/\\011/, "\t", mount_path)
			if (mount_path != target || $3 ~ /^(overlay|squashfs|tmpfs|ramfs|rootfs|ubifs|jffs2)$/)
				next
			count = split($4, options, ",")
			for (i = 1; i <= count; i++)
				if (options[i] == "rw") ready = 1
		}
		END { exit !ready }
	'
}

r619ac_storage_ready() {
	local path="$1" suffix mount_root ancestor resolved_root resolved_ancestor
	case "$path" in
		/mnt|/media) return 1 ;;
		/mnt/*) suffix="${path#/mnt/}"; mount_root="/mnt/${suffix%%/*}" ;;
		/media/*) suffix="${path#/media/}"; mount_root="/media/${suffix%%/*}" ;;
		*) return 0 ;;
	esac
	case "$path/" in */../*) return 1 ;; esac
	[ -d "$mount_root" ] || return 1
	resolved_root=$(readlink -f "$mount_root") || return 1

	# 允许尚未创建的下载子目录，但不能经符号链接落回内部闪存。
	ancestor="$path"
	while [ ! -e "$ancestor" ]; do
		[ ! -L "$ancestor" ] || return 1
		ancestor="${ancestor%/*}"
		[ -n "$ancestor" ] || return 1
	done
	resolved_ancestor=$(readlink -f "$ancestor") || return 1
	case "$resolved_ancestor/" in "$resolved_root/"*) ;; *) return 1 ;; esac
	r619ac_storage_mount_ready "$resolved_root" < /proc/self/mounts
}

r619ac_require_storage() {
	local path
	for path in "$@"; do
		if ! r619ac_storage_ready "$path"; then
			logger -t transmission -p daemon.err "拒绝启动：外接存储未读写挂载或路径不安全：$path"
			return 1
		fi
	done
}
