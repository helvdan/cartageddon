. ./extract/set_env.sh
#. ./open_ssh_tunnel.sh
PYTHONPATH="/www/zoovostorg.com/etl" python3 extract/extract.py "$@"
#. ./close_ssh_tunnel.sh