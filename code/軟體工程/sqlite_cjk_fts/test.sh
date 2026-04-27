set -x
make test
pip install -e .
python test_cjk.py
python example.py