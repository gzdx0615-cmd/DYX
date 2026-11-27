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
source_url="https://raw.githubusercontent.com/gzdx0615-cmd/DYX/c7ef372f4becac10d57bbe55e149039af9351697/X-Video-Share-unsigned.shortcut"
curl --fail --location --retry 2 "$source_url" --output "$dest/X-Video-Share-unsigned.shortcut"
actual="$(shasum -a 256 "$dest/X-Video-Share-unsigned.shortcut" | awk '{print $1}')"
if [[ "$actual" != "b0328f08137f61f17b0251dc29dce7b6b4166eab63ea1dd73e19e0a3cb0eb575" ]]; then
  echo "文件校验失败，已停止。请重新下载仓库中的最新安装脚本。" >&2
  exit 1
fi
plutil -lint "$dest/X-Video-Share-unsigned.shortcut"
shortcuts sign --mode anyone --input "$dest/X-Video-Share-unsigned.shortcut" --output "$dest/X 视频保存（分享版）.shortcut"
open "$dest/X 视频保存（分享版）.shortcut"
printf '\n已打开导入窗口。文件保存在：%s\n' "$dest"
