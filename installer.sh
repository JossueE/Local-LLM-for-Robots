#!/usr/bin/env bash
# setup_octopy.sh — One-shot installer for Local-LLM-for-Robots
# Tested on Ubuntu/Debian-like systems.

set -euo pipefail

APT_PKGS=(
  python3-dev python3-venv build-essential curl unzip
  portaudio19-dev ffmpeg
)

log()   { printf "\n\033[1;34m[INFO]\033[0m %s\n" "$*"; }
ok()    { printf "\033[1;32m[OK]\033[0m %s\n" "$*"; }
warn()  { printf "\033[1;33m[WARN]\033[0m %s\n" "$*"; }
fail()  { printf "\033[1;31m[FAIL]\033[0m %s\n" "$*"; exit 1; }


require_sudo() {
  if [[ $EUID -ne 0 ]]; then
    if command -v sudo >/dev/null 2>&1; then
      SUDO="sudo"
    else
      fail "Run as root or install sudo."
    fi
  else
    SUDO=""
  fi
}

install_apt() {
  log "Updating apt and installing base packages…"
  $SUDO apt update -y
  $SUDO apt install -y "${APT_PKGS[@]}"
  ok "System packages installed."
}

ensure_snapd() {
  if ! command -v snap >/dev/null 2>&1; then
    log "snap not found. Installing snapd…"
    $SUDO apt install -y snapd
  fi
}

install_yq() {
  if ! command -v yq >/dev/null 2>&1; then
    log "Installing yq via snap…"
    $SUDO snap install yq
    ok "yq installed."
  else
    ok "yq already installed."
  fi
}

download_models() {
  log "Downloading/verifying models (this can take a while on first run)…"
  bash "utils/download_models.sh"
  ok "Model download/verify step completed."
}

sync_tts_models() {
  local DEST="${XDG_CACHE_HOME:-$HOME/.cache}/Local-LLM-for-Robots/tts"
  local SRC1="utils/es_419-Octybot-medium.onnx"
  local SRC2="utils/es_419-Octybot-medium.onnx.json"
  local DST1="$DEST/es_419-Octybot-medium.onnx"
  local DST2="$DEST/es_419-Octybot-medium.onnx.json"

  # mueve solo si NO están ya en DEST
  [[ -f "$DST1" ]] || { [[ -f "$SRC1" ]] && mv -- "$SRC1" "$DEST/"; }
  [[ -f "$DST2" ]] || { [[ -f "$SRC2" ]] && mv -- "$SRC2" "$DEST/"; }

  rm -f "$SRC1" "$SRC2"  # limpia si quedaron

  command -v ok >/dev/null && ok "TTS sync listo en $DEST" || echo "[✓] TTS sync: $DEST"
}




create_venv_and_install() {
  log "Creating Python virtual environment…"
  python3 -m venv ".venv" || fail "venv creation failed."
  ok "venv created: .venv"

  log "Installing Python dependencies into the venv…"
  ".venv/bin/pip" install --upgrade pip
  ".venv/bin/pip" install -r "requirements.txt"
  ok "Dependencies installed."
}

post_instructions() {
  cat <<'EOS'

────────────────────────────────────────────────────────────
✅ Setup completed.

Next steps:
  1) Activate the virtual environment:
       source Local-LLM-for-Robots/.venv/bin/activate
  2) (Optional) Run the models script anytime:
       bash Local-LLM-for-Robots/utils/download_models.sh
  3) You're ready to use the project.
Tip: The cache lives in ~/.cache/Local-LLM-for-Robots or `$OCTOPY_CACHE` if set).
────────────────────────────────────────────────────────────
EOS
}

main() {
  require_sudo
  install_apt
  ensure_snapd
  install_yq
  download_models
  sync_tts_models
  create_venv_and_install
  post_instructions
}

main "$@"