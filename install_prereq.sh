#!/usr/bin/env bash
set -euo pipefail

rye_install() {
	echo Installing rye...
	curl -sSf https://rye.astral.sh/get | RYE_INSTALL_OPTION="--yes" bash
}

rye_init() {
	echo "Initializing rye..."
	. "$HOME"/.rye/env
}

archInstall() {
	sudo pacman -S --needed base-devel uv git iw dnsmasq hostapd screen curl mosquitto haveged net-tools openssl
	echo "Dependencies from OS package manager have been installed."
	echo

	echo "This script uses python installed via rye. If rye is not installed, it will be attempted to get installed."
	echo "This script installs python packages with uv."
	if ! command -v rye >/dev/null 2>&1; then
		echo "No rye in path, but do we have it installed?"

		if [ -f "$HOME"/.rye/env ]; then
			echo "Yes!"
		else
			echo "Definitely no."
			rye_install
		fi
	fi

	rye_init
	uv venv --seed
	source .venv/bin/activate

	echo "Activated venv. Installing python dependencies..."
	uv pip install -r requirements.txt

	cat <<'EOF'
Installed python dependencies.

Your venv is ready to use.
activate with:
	source .venv/bin/activate

EOF
}

if [[ -e /etc/os-release ]]; then
	source /etc/os-release
else
	echo "/etc/os-release not found!"
	exit 1
fi

if [[ ${ID} == 'arch' ]] || [[ ${ID_LIKE-} == 'arch' ]]; then
	archInstall
else
	if [[ -n ${ID_LIKE-} ]]; then
		printID="${ID}/${ID_LIKE}"
	else
		printID="${ID}"
	fi
	echo "/etc/os-release found but distribution ${printID} is not supported."
	exit 1
fi
