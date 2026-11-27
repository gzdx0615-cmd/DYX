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
original="https://raw.githubusercontent.com/gzdx0615-cmd/DYX/main/Douyin-unsigned.shortcut"
valid=0
for source_url in "https://v4.gh-proxy.org/$original" "$original"; do
  if curl --fail --location --connect-timeout 10 --max-time 60 "$source_url" --output "$dest/Douyin-unsigned.shortcut"; then
    actual="$(shasum -a 256 "$dest/Douyin-unsigned.shortcut" | awk '{print $1}')"
    if [[ "$actual" == "05085fa66d03d6499486f9b32716f2f5a18f4756b06bb2a761ff53731192316a" ]]; then
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
plutil -lint "$dest/Douyin-unsigned.shortcut"
shortcuts sign --mode anyone --input "$dest/Douyin-unsigned.shortcut" --output "$dest/抖音视频保存.shortcut"
open "$dest/抖音视频保存.shortcut"
printf '\n已打开导入窗口。文件保存在：%s\n' "$dest"
