import sqlite3
from os import path
from typing import Any
import json
import yaml
from datetime import datetime

import config
import Note
from Task import Task

con: sqlite3.Connection = None
cur: sqlite3.Cursor = None


def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def init_db(db_path=None):
    global con, cur
    if db_path is None:
        db_path = path.join(config.app_root, config.db_path)
    con = sqlite3.connect(db_path)
    con.row_factory = dict_factory
    cur = con.cursor()


def run_migrations():
    with open(path.join(config.app_root, "migrations", "0001-init.sql"), "r") as f:
        cur.executescript(f.read())


NEXT_NOTE_ID_OPTION_KEY = "nextNoteId"
TAGS_FOR_DIRS_KEY = "tags_for_dirs"
SKIPPED_TASKS_KEY = "skipped_tasks"


class ListNotesById:
    def __init__(self) -> None:
        self.id = 999999

    def iter(self):
        while True:
            res = cur.execute(
                "SELECT * FROM yaml_notes WHERE id < :id order by id desc limit 1",
                {
                    "id": self.id,
                },
            )
            row = res.fetchone()
            if not row:
                return
            self.id = row["id"]
            yield row


def get_note_by_id(id: int):
    res = cur.execute(
        "SELECT * FROM yaml_notes WHERE id = :id",
        {
            "id": id,
        },
    )
    return res.fetchone()


def find_first(table: str, params: dict):
    where = ""
    for k in params:
        if where:
            where += " and "
        where += f"`{k}` = :{k}"
    res = cur.execute(f"SELECT * FROM {table} WHERE " + where, params)
    return res.fetchone()


def clear_table(table_name):
    cur.execute(f"DELETE FROM {table_name}")
    con.commit()


def replace_task(task: Task):
    cur.execute(
        """
            REPLACE INTO yaml_notes_tasks
            (
                `parent_task_id`,
                `note_id`,
                `line_number_in_note`,
                `text`,
                `order`,
                `priority`,
                `urgency`,
                `created_at`,
                `updated_at`,
                `deleted_at`,
                `indexed_at`,
                `done_at`,
                `canceled_at`,
                `suspended_until`
            )
            VALUES (
                :parent_task_id,
                :note_id,
                :line_number_in_note,
                :text,
                :order,
                :priority,
                :urgency,
                :created_at,
                :updated_at,
                :deleted_at,
                :indexed_at,
                :done_at,
                :canceled_at,
                :suspended_until
            )
        """,
        {
            "parent_task_id": task.parent_task_id,
            "note_id": task.note_id,
            "line_number_in_note": task.line_number_in_note,
            "text": task.text,
            "order": task.order,
            "priority": task.priority,
            "urgency": task.urgency,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "deleted_at": task.deleted_at,
            "indexed_at": task.indexed_at,
            "done_at": task.done_at,
            "canceled_at": task.canceled_at,
            "suspended_until": task.suspended_until,
        },
    )
    con.commit()


def delete_note_by_id(id: int):
    cur.execute(
        "DELETE FROM yaml_notes WHERE id = :id",
        {
            "id": id,
        },
    )
    con.commit()


def get_options():
    res = cur.execute("SELECT * FROM yaml_notes_options")
    options = dict()
    for d in res.fetchall():
        options[d["key"]] = d["value"]
    return options


def get_option(key, default_value=None):
    options = get_options()
    if not key in options:
        return default_value
    value = options[key]
    return value


def get_json_option(key, default_value=None):
    value = get_option(key)
    if value is None:
        return default_value
    return json.loads(value)


def set_json_option(key, value: Any):
    set_option(key, json.dumps(value))


def set_option(key, value):
    cur.execute(
        "UPDATE yaml_notes_options SET value = :value WHERE key = :key",
        {
            "key": str(key),
            "value": str(value),
        },
    )
    if not cur.rowcount:
        cur.execute(
            "INSERT INTO yaml_notes_options (key, value) VALUES (:key, :value)",
            {
                "key": str(key),
                "value": str(value),
            },
        )
    con.commit()


def save_note_child_file(note: Note.Note, filepath: str, do_commit=True):
    data = dict()
    data["note_id"] = note.get_id()
    data["relative_path"] = path.relpath(filepath, config.notes_dir)
    with open(filepath, "br") as f:
        data["content"] = f.read()
    cur.execute(
        """REPLACE INTO yaml_notes_child_files (
            note_id,
            relative_path,
            content
        ) VALUES (
            :note_id,
            :relative_path,
            :content
        )""",
        data,
    )
    if do_commit:
        con.commit()


def update_note(note_id, column, value):
    cur.execute(
        f"UPDATE yaml_notes SET {column} = :value WHERE id = :note_id",
        {
            "value": value,
            "note_id": note_id,
        },
    )
    con.commit()


def save_note(note: Note.Note, do_commit=True):
    data = dict()
    data["id"] = note.get_id()
    data["text"] = note.text
    data["relative_path"] = path.relpath(note.filepath, config.notes_dir)
    data["tags"] = json.dumps(note.get_tags())
    data["created_at"] = note.get_created_at().strftime("%Y-%m-%d %H:%M:%S")
    data["is_active"] = int(note.is_active())
    data["yaml_parameters"] = yaml.safe_dump(note.params)
    json_parameters = dict()
    for param in note.params:
        for k, v in param.items():
            json_parameters[k] = v
    data["json_parameters"] = json.dumps(json_parameters)
    data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute(
        """REPLACE INTO yaml_notes (
            id,
            text,
            relative_path,
            tags,
            created_at,
            is_active,
            yaml_parameters,
            json_parameters,
            updated_at
        ) VALUES (
            :id,
            :text,
            :relative_path,
            :tags,
            :created_at,
            :is_active,
            :yaml_parameters,
            :json_parameters,
            :updated_at
        )""",
        data,
    )
    if do_commit:
        con.commit()
