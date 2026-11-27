#!/bin/bash
set -euo pipefail
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "请在 Mac 终端运行此脚本。" >&2
  exit 1
fi
if ! command -v shortcuts >/dev/null 2>&1; then
  echo "未找到苹果 shortcuts 命令，请使用支持快捷指令的 macOS。" >&2
  exit 1
fi
mkdir -p "$HOME/Downloads"
dest="$(mktemp -d "$HOME/Downloads/DYX-Shortcut.XXXXXX")"
original="https://raw.githubusercontent.com/gzdx0615-cmd/DYX/c7ef372f4becac10d57bbe55e149039af9351697/X-Douyin-unsigned.shortcut"
valid=0
for source_url in "https://v4.gh-proxy.org/$original" "$original"; do
  if curl --fail --location --connect-timeout 10 --max-time 60 "$source_url" --output "$dest/X-Douyin-unsigned.shortcut"; then
    actual="$(shasum -a 256 "$dest/X-Douyin-unsigned.shortcut" | awk '{print $1}')"
    if [[ "$actual" == "5bf240e8bdf330c8db1fdc24905fc7b03d1eef30870f8bff041f69afce83f8c0" ]]; then
      valid=1
      break
    fi
    echo "此线路文件校验不一致，尝试下一条线路。" >&2
  fi
done
if [[ "$valid" != 1 ]]; then
  echo "文件下载或校验失败，已停止。请重新下载仓库中的最新安装脚本。" >&2
  exit 1
fi
plutil -lint "$dest/X-Douyin-unsigned.shortcut"
shortcuts sign --mode anyone --input "$dest/X-Douyin-unsigned.shortcut" --output "$dest/X·抖音保存.shortcut"
open "$dest/X·抖音保存.shortcut"
printf '\n已打开导入窗口。文件保存在：%s\n' "$dest"
