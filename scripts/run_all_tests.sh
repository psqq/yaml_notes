set -e

cd "$(dirname "$0")"

bash run_test.sh MdNoteFormat
bash run_test.sh NorgNoteFormat
bash run_test.sh BaseDb
bash run_test.sh DbOptions
bash run_test.sh NoteManager
