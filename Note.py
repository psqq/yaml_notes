import locale
import os
import re
import shutil
from datetime import datetime
from os import path
from typing import Optional, Any, Callable

from formats.common.CommonNoteFormat import CommonNoteFormat
from formats.md.MdNoteFormat import MdNoteFormat

locale.setlocale(locale.LC_TIME, "ru_RU.utf8")


class NoteLoadException(Exception):
    pass


def save_note(note):
    import db

    db.save_note(note)


class Note:
    def __init__(self) -> None:
        self.params: Optional[list[dict]] = None
        self._filepath: Optional[str] = None
        self.real_filepath: Optional[str] = None
        self.is_saved = False
        self.text = ""
        self.datetime_format = "%a %d %b %Y %H:%M:%S"
        self.noteFormat: CommonNoteFormat = MdNoteFormat()

    def get_child_files(self) -> list[str]:
        if not self.get_bool_param("folder"):
            return []
        child_files = []
        note_dir = path.dirname(self.filepath)
        for root, dirs, files in os.walk(note_dir):
            for filename in files:
                filepath = os.path.join(root, filename)
                if path.samefile(self.filepath, filepath):
                    continue
                child_files.append(filepath)
        return child_files

    def full_remove(self):
        if self.get_bool_param("folder"):
            shutil.rmtree(path.dirname(self.filepath))
        else:
            os.remove(self.filepath)

    @property
    def filepath(self):
        return self._filepath

    @filepath.setter
    def filepath(self, value: Optional[str]):
        if value:
            value = os.path.abspath(value)
        self._filepath = value

    def get_filename(self) -> Optional[str]:
        if not self.filepath:
            return
        return os.path.basename(self.filepath)

    def has_tag(self, tag: str) -> bool:
        return tag in self.get_tags()

    def has_param(self, param_key: str) -> bool:
        return self.get_param(param_key) is not None

    def clear(self):
        self.params = None
        self.filepath = None
        self.text = ""

    def get_links(self) -> list[int]:
        links = self.get_param("links") or []
        return links + self.find_links_in_text()

    def find_links_in_text(self) -> list[int]:
        # пока что не определился с форматом ссылок внутри текста
        return []

    def is_task(self) -> bool:
        return "task" in self.get_tags()

    def _on_param(
        self,
        param_key: str,
        on_param: Callable[[Any, str], Any],
        on_no_param: Callable[[str], Any],
    ) -> bool:
        if not self.params or not isinstance(self.params, list):
            return on_no_param(param_key)
        for param in self.params:
            if param_key in param:
                return on_param(param[param_key], param_key)
        return on_no_param(param_key)

    def is_param(self, param_key: str) -> bool:
        return self._on_param(
            param_key, on_param=lambda x, k: True, on_no_param=lambda k: False
        )

    def get_bool_param(self, param_key: str) -> Optional[bool]:
        if not self.is_param(param_key):
            return
        val = self.get_param(param_key)
        if (
            val == True
            or val == 1
            or (isinstance(val, str) and val.lower() in ["y", "yes", "true", "on", "1"])
        ):
            return True
        if (
            val == False
            or val == 0
            or (
                isinstance(val, str) and val.lower() in ["n", "no", "false", "off", "0"]
            )
        ):
            return False

    def is_already_in_its_folder(self):
        dirname = os.path.split(os.path.dirname(self.real_filepath))[1]
        filename = os.path.splitext(os.path.split(self.real_filepath)[1])[0]
        return dirname == filename

    def set_bool_param(self, param_key: str, val: bool):
        self.set_param(param_key, True if val else False)

    def set_datetime_param(self, param_key: str, t: datetime):
        self.set_param(param_key, t.strftime(self.datetime_format))

    def get_datetime_param(self, param_key: str) -> datetime:
        return datetime.strptime(self.get_param(param_key), self.datetime_format)

    def get_created_at(self) -> datetime:
        return self.get_datetime_param("created_at")

    def add_created_at_timestamp(self) -> None:
        if self.is_param("createdAtTimestamp"):
            return
        created_at = self.get_created_at()
        self.params.append({"createdAtTimestamp": int(created_at.timestamp())})

    def remove_param(self, param_key: str) -> None:
        for param in self.params:
            if param_key in param:
                del param[param_key]
        self.params = list(filter(lambda x: len(x) > 0, self.params))

    def remove_created_at_timestamp(self) -> None:
        self.remove_param("createdAtTimestamp")

    def is_done_task(self) -> bool:
        return self.is_task() and self.get_bool_param("done") == True

    def is_active(self) -> bool:
        return self.get_bool_param("active") == True

    def get_param(self, param_key: str) -> Any:
        return self._on_param(param_key, lambda x, k: x, lambda k: None)

    def get_id(self) -> int:
        return int(self.get_param("id"))

    def set_param(self, param_key, param_value):
        if not self.params:
            self.params = []
        if not isinstance(self.params, list):
            raise Exception("Note.set_param: self.params is not list")
        for param in self.params:
            if param_key in param:
                param[param_key] = param_value
                return
        self.params.append({param_key: param_value})

    def add_tag(self, tag_name: str) -> bool:
        tags = self.get_param("tags")
        if not tags:
            tags = []
        if tag_name in tags:
            return False
        tags.append(tag_name)
        self.set_param("tags", tags)
        return True

    def set_tags(self, tags: list[str]) -> bool:
        self.set_param("tags", tags)

    def get_tags(self, flatten=True) -> list[str]:
        tags = self.get_param("tags")
        if not tags:
            return []
        if not flatten:
            return tags
        flatten_tags = []
        for tag in tags:
            if isinstance(tag, list):
                flatten_tags += tag
            else:
                flatten_tags.append(str(tag))
        return flatten_tags

    def get_tags_as_str(self) -> str:
        return " ".join(self.get_tags())

    def fix_folder_note(self):
        if self.is_already_in_its_folder():
            return
        filename = os.path.basename(self.real_filepath)
        dirpath = path.split(self.real_filepath)[0]
        new_dirname = path.splitext(filename)[0]
        new_dirpath = path.join(dirpath, new_dirname)
        if not os.path.exists(new_dirpath):
            os.makedirs(new_dirpath)
        new_filepath = path.join(new_dirpath, filename)
        os.rename(self.real_filepath, new_filepath)
        self.real_filepath = new_filepath

    def real_move(self, to_path) -> bool:
        if self.get_bool_param("folder") == True:
            self.fix_folder_note()
            from_dirpath = path.dirname(self.real_filepath)
            from_filename = path.split(self.real_filepath)[1]
            to_filename = path.split(to_path)[1]
            to_dirname = path.splitext(to_filename)[0]
            to_dirpath = path.join(path.dirname(to_path), to_dirname)
            is_changes_in_fs = True
            if os.path.isdir(to_path) and os.path.samefile(from_path, to_path):
                is_changes_in_fs = False
            else:
                dir_of_to_dirpath = path.split(to_dirpath)[0]
                if not os.path.exists(dir_of_to_dirpath):
                    os.makedirs(dir_of_to_dirpath)
                os.rename(from_dirpath, to_dirpath)
            from_path = path.join(to_dirpath, from_filename)
            to_path = path.join(to_dirpath, to_filename)
            if os.path.isfile(to_path) and os.path.samefile(from_path, to_path):
                is_changes_in_fs = False
            else:
                os.rename(from_path, to_path)
            self.real_filepath = to_path

            return is_changes_in_fs

        from_path = self.real_filepath
        new_dir = os.path.dirname(to_path)
        if not os.path.exists(new_dir):
            os.makedirs(new_dir)
        if os.path.isfile(to_path) and os.path.samefile(from_path, to_path):
            return False
        if os.path.exists(to_path):
            raise Exception("Can not move note: filepath already exists!")
        os.rename(from_path, to_path)
        self.real_filepath = to_path

        return True

    def move(self, filepath, noRealMv=False) -> bool:
        self.filepath = filepath
        if noRealMv:
            return False
        if not self.filepath:
            raise Exception("Can't move! Note doesn't have filepath!")
        return self.real_move(self.filepath)

    def move_to_dir(self, new_dir, noRealMv=False) -> bool:
        if not self.filepath:
            raise Exception("Note doesn't have filapth. Save note before move!")
        filename = os.path.basename(self.filepath)
        return self.move(os.path.join(new_dir, filename), noRealMv=noRealMv)

    def rename_folder_note(self, filename, noRealMv=False) -> bool:
        if noRealMv or not self.is_already_in_its_folder():
            raise Exception("rename_folder_note: bad note or params")
        to_filename_without_ext, _ = path.splitext(filename)
        from_dirpath = path.dirname(self.real_filepath)
        to_dirpath = path.join(path.dirname(from_dirpath), to_filename_without_ext)

        from_filepath = self.real_filepath
        from_dirpath = path.dirname(self.real_filepath)
        to_filepath = path.join(from_dirpath, filename)

        is_changes_in_fs = False

        if os.path.exists(to_dirpath) and not os.path.samefile(
            to_dirpath, from_dirpath
        ):
            raise Exception("rename_folder_note: bad to_dirpath")

        if os.path.exists(to_filepath) and not os.path.samefile(
            from_filepath, to_filepath
        ):
            raise Exception("rename_folder_note: bad to_filepath")

        if not (
            os.path.exists(to_filepath) and os.path.samefile(from_filepath, to_filepath)
        ):
            is_changes_in_fs = True
            os.rename(from_filepath, to_filepath)

        if not (
            os.path.isdir(to_dirpath) and os.path.samefile(to_dirpath, from_dirpath)
        ):
            is_changes_in_fs = True
            os.rename(from_dirpath, to_dirpath)

        self.filepath = path.join(to_dirpath, filename)
        self.real_filepath = self.filepath

        return is_changes_in_fs

    def rename(self, filename, noRealMv=False) -> bool:
        if self.get_bool_param("folder"):
            is_moved = self.rename_folder_note(filename, noRealMv)
            if is_moved:
                save_note(self)
            return is_moved
        if not self.filepath:
            raise Exception("Note doesn't have filapth. Save note before move!")
        if "/" in filename or "\\" in filename:
            raise Exception("Note.rename: filename includes '\\' or '/'!")
        curdir = os.path.dirname(self.filepath)
        is_moved = self.move(os.path.join(curdir, filename), noRealMv=noRealMv)
        if is_moved:
            save_note(self)
        return is_moved

    def from_text(self, s: str):
        self.text, self.params = self.noteFormat.from_text(s)

    def to_text(self):
        return self.noteFormat.to_text(self.params, self.text)

    def is_note_filepath(self, filepath: str):
        filename = path.split(filepath)[1]
        return bool(re.match(r"^\d+[\w\_\- ]*\.(md|norg)$", filename))

    def set_filepath(self, filepath):
        self.filepath = filepath
        self.real_filepath = self.filepath

    def load(self):
        if not self.filepath:
            raise NoteLoadException("Can not load! Note doesn't have filepath!")
        if not self.is_note_filepath(self.filepath):
            raise NoteLoadException("Filepath for note load is not note filepath")
        filepath = self.filepath
        self.clear()
        with open(filepath, "r") as f:
            self.from_text(f.read())
        self.set_filepath(filepath)
        self.is_saved = True

    def save(self):
        if not self.filepath:
            raise Exception("Can not save! Note doesn't have filepath!")
        note_dir = path.dirname(self.filepath)
        if not path.exists(note_dir):
            os.makedirs(note_dir)
        with open(self.filepath, "w") as f:
            f.write(self.to_text())
        self.real_filepath = self.filepath
        self.is_saved = True
        save_note(self)

    def save_child_file(self, filepath, data):
        file_dir = path.dirname(filepath)
        if not path.exists(file_dir):
            os.makedirs(file_dir)
        with open(filepath, "bw") as f:
            f.write(data)

    def to_dict_for_json(self):
        parameters_object = dict()
        for param in self.params:
            for k, v in param.items():
                parameters_object[k] = v
        return {
            "parameters_array": self.params,
            "parameters_object": parameters_object,
            "created_at_timestamp": self.get_created_at().timestamp(),
            "text": self.text,
        }
