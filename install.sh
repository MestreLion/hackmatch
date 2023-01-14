#!/bin/bash
#
# Exapunks Hack*Match bot dependencies installer
#
# This file is part of HackMatch, see <https://github.com/MestreLion/hackmatch>
# Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>
#------------------------------------------------------------------------------
set -xEeuo pipefail  # exit on any error
trap '>&2 echo "error: line $LINENO, status $?: $BASH_COMMAND"' ERR
#------------------------------------------------------------------------------
myself=${0##*/}
here=$(dirname "$(readlink -f "$0")")
vdir=$here/venv
python=$(compgen -c python | grep -P '^python\d[.\d]*$' | sort -ruV | head -n1)

apt_packages=(
	"$python"-venv  # To create the Python Virtual Environment
	"$python"-dev   # Some of its dependencies needed to pip-install pyautogui deps
	python3-tk      # PyAutoGui system dependency
)
pip_deps=(
	pip             # Upgrade pip in venv
	wheel           # Upgrade wheels in venv for pip installs
	setuptools      # Upgrade setuptools in venv for pip installs
)
#------------------------------------------------------------------------------
usage() {
	cat <<-USAGE
	Usage: $myself [options]

	Install system dependencies and virtual env for Exapunks' Hack*Match bot
	See https://github.com/MestreLion/hackmatch for details

	Options:
	  -h|--help     - show this page.

	Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
	License: GPLv3 or later. See <http://www.gnu.org/licenses/gpl.html>
	USAGE
	exit
}
for arg in "$@"; do [[ "$arg" == "-h" || "$arg" == "--help" ]] && usage ; done

#------------------------------------------------------------------------------
apt_install() {
	# Avoid marking installed packages as manual by only installing missing ones
	local pkg=
	local pkgs=()
	local ok
	for pkg in "$@"; do
		# shellcheck disable=SC1083
		ok=$(dpkg-query --showformat=\${Version} --show "$pkg" 2>/dev/null || true)
		if [[ -z "$ok" ]]; then pkgs+=( "$pkg" ); fi
	done
	if (("${#pkgs[@]}")); then
		sudo apt install "${pkgs[@]}"
	fi
}
#------------------------------------------------------------------------------

apt_install "${apt_packages[@]}"
"$python" -m venv "$vdir"
source "$vdir"/bin/activate
# pip-install packages inside the venv. Do NOT use --user!
pip install --disable-pip-version-check --upgrade -- "${pip_deps[@]}"
pip install --disable-pip-version-check --upgrade -r "$here"/requirements.txt
