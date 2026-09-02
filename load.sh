#. ../../env/bin/activate
. ./load/set_env.sh
#. ./open_ssh_tunnel.sh
PYTHONPATH="/www/zoovostorg.com/etl" python3 load/load.py
#. ./close_ssh_tunnel.sh