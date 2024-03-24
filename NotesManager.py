from typing import Iterator, Optional
from Note import Note, NoteLoadException
from os import path
from datetime import datetime
import os
import config
import db
from formats.norg.NorgNoteFormat import NorgNoteFormat
from formats.md.MdNoteFormat import MdNoteFormat


class NotesManager:
    def __init__(self, notes_dir: str) -> None:
        self.notes_dir = notes_dir
        self._verbose = True
        self.archive_path = path.join(notes_dir, "archive")

        self.tags_for_dirs = []

    def init_tags_for_dirs(self):
        self.tags_for_dirs = db.get_json_option(db.TAGS_FOR_DIRS_KEY)
        if not self.tags_for_dirs:
            self.tags_for_dirs = []

    def verbose(self, *args, **kwargs):
        if self._verbose:
            print("NotesManager: VERBOSE:", *args, **kwargs)

    def update_next_note_id(self, id: int):
        db.set_option(db.NEXT_NOTE_ID_OPTION_KEY, id)
        self.verbose(f"note_id updated in db to {repr(str(id))}")

    def get_next_note_id(self, update=True) -> int:
        next_note_id = db.get_option(db.NEXT_NOTE_ID_OPTION_KEY)
        if not next_note_id:
            next_note_id = 1
        next_note_id = int(next_note_id)
        self.verbose(f"next_note_id = {next_note_id}")
        if update:
            self.update_next_note_id(next_note_id + 1)
        return next_note_id

    def make_note(self, noteFormat=None) -> Note:
        id = self.get_next_note_id(False)
        note = Note()
        if not noteFormat:
            noteFormat = config.get_default_format_class()()
        note.noteFormat = noteFormat
        note.filepath = path.join(
            self.notes_dir, f"{id}.{note.noteFormat.get_default_file_extension()}"
        )
        note.set_param("id", id)
        note.set_param("active", True)
        note.set_datetime_param("created_at", datetime.now())
        self.update_next_note_id(id + 1)
        return note

    def move_note(self, note: Note, new_filepath: str):
        prev_filepath = note.filepath
        if note.move(new_filepath):
            self.verbose(
                f"Note moved from {repr(prev_filepath)} to {repr(note.filepath)}"
            )

    def move_to_dir(self, note: Note, dir_path: str):
        prev_filepath = note.filepath
        if note.move_to_dir(dir_path):
            self.verbose(
                f"Note moved from {repr(prev_filepath)} to {repr(note.filepath)}"
            )

    def rename_note(self, note: Note, filename: str, noRealMv=False):
        prev_filepath = note.filepath
        if note.rename(filename, noRealMv=noRealMv):
            self.verbose(
                f"Note moved from {repr(prev_filepath)} to {repr(note.filepath)}"
            )

    def load_note(self, filepath_for_load: str):
        note = Note()
        if filepath_for_load.endswith(".norg"):
            note_formats = [NorgNoteFormat]
            # note_formats = [NorgNoteFormat, MdNoteFormat]
        else:
            note_formats = [MdNoteFormat]
            # note_formats = [MdNoteFormat, NorgNoteFormat]
        exception = None
        for noteFormat in note_formats:
            try:
                note.filepath = filepath_for_load
                note.noteFormat = noteFormat()
                note.load()
                exception = None
                break
            except NoteLoadException as e:
                exception = e
        if exception:
            raise exception
        return note

    def iter_notes_by_db(self, remove_row_on_file_not_found=True) -> Iterator[Note]:
        l = db.ListNotesById()
        for n in l.iter():
            fn = path.join(self.notes_dir, n["relative_path"])
            try:
                note = self.load_note(fn)
            except FileNotFoundError as e:
                print(f"Note file is not found: '{fn}'")
                if remove_row_on_file_not_found:
                    print("Deleting note row from db (no yet)")
                continue
            yield note

    def iter_notes_by_fs_walk(self) -> Iterator[Note]:
        for dirpath, dirnames, filenames in os.walk(self.notes_dir):
            if "/.git" in dirpath:
                continue
            for filename in filenames:
                filepath_for_load = path.abspath(path.join(dirpath, filename))
                try:
                    note = self.load_note(filepath_for_load)
                except NoteLoadException as e:
                    print(f"Can't load note {repr(filepath_for_load)}")
                    note = None
                if note and isinstance(note.get_param("id"), int):
                    yield note

    def iter_notes(self, by_db=True) -> Iterator[Note]:
        if by_db:
            return self.iter_notes_by_db()
        else:
            return self.iter_notes_by_fs_walk()

    def is_for_archive(self, note: Note) -> bool:
        if note.is_active() or (note.is_task() and not note.is_done_task()):
            return False
        return True

    def archive(self, note: Note, noRealMv=False):
        self.move_in_dirs_by_tags(note, self.archive_path, noRealMv=noRealMv)

    def move_in_dirs_by_tags(
        self, note: Note, base_dir: Optional[str] = None, noRealMv=False
    ):
        self.init_tags_for_dirs()
        if not base_dir:
            base_dir = self.notes_dir
        tags = note.get_tags()
        new_dir = [base_dir]
        for tags_dirs in self.tags_for_dirs:
            has_all_dir_tags = True
            for tag in tags_dirs:
                if tag not in tags:
                    has_all_dir_tags = False
                    break
            if not has_all_dir_tags:
                continue
            new_dir += tags_dirs
            break
        fp = note.filepath
        if note.move_to_dir(os.path.join(*new_dir), noRealMv=noRealMv):
            self.verbose(f"Note moved from {fp} to {note.filepath}")
        db.update_note(
            note.get_id(),
            "relative_path",
            path.relpath(note.real_filepath, config.notes_dir),
        )
