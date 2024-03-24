
set -e

test_file=tests/test_$1.py

echo ======================================================================
echo Running $test_file
cd "$(dirname "$0")"/..
python -m unittest --failfast --verbose --locals $test_file
