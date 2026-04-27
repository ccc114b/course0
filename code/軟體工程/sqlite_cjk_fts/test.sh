set -x
make test
deactivate
/opt/homebrew/bin/python3 -m pip install -e .
# /opt/homebrew/bin/python3 -m pip install sqlite_cjk_fts
/opt/homebrew/bin/python3 test_cjk.py
/opt/homebrew/bin/python3 example.py