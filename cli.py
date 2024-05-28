import datetime
import os
import pprint
import subprocess
import sys
from collections import defaultdict
from os import path
from typing import Optional, Union
import yaml
import json
from tabulate import tabulate

import db
from Note import Note
from NotesManager import NotesManager
import config
from formats.common.NoteAst import TaskNode
from formats.md.MdNoteFormat import MdNoteFormat
from formats.norg.NorgNoteFormat import NorgNoteFormat
from Task import Task
import functools


CONFIG_ATTRS_FOR_CHECK = ["version", "db_path", "notes_dir", "app_root"]
CONFIG_ATTRS_ADDITIONAL = ["default_format_ext", "clear_empty_folders"]


def get_check_config_errors():
    errors = []
    for attr in CONFIG_ATTRS_FOR_CHECK:
        db_value = db.get_option(f"config__{attr}")
        config_value = getattr(config, attr)
        if db_value != config_value:
            errors.append(
                f"Error: config__{attr} != config.{attr}, '{db_value}' != '{config_value}'"
            )
    return errors


def check_config():
    errors = get_check_config_errors()
    for err in errors:
        print(err)
    if errors.__len__():
        print("Saved configs values in db is not equal values from config.")
        print("May be you use wrong code or data.")
        print("To save current config in db run command save_config_in_db.")
        sys.exit(1)


def needs_db(func):
    @functools.wraps(func)
    def wrapper_decorator(self, *args, **kwargs):
        check_config()
        config__clear_empty_folders = db.get_option("config__clear_empty_folders")
        if config__clear_empty_folders:
            config.clear_empty_folders = (
                db.get_option("config__clear_empty_folders") == "True"
            )
        config__default_format_ext = db.get_option("config__default_format_ext")
        if config__default_format_ext:
            config.default_format_ext = config__default_format_ext
        value = func(self, *args, **kwargs)
        return value

    return wrapper_decorator


def save_config_in_db():
    for attr in CONFIG_ATTRS_FOR_CHECK + CONFIG_ATTRS_ADDITIONAL:
        db.set_option(f"config__{attr}", getattr(config, attr))


pp = pprint.PrettyPrinter(indent=4)


class Cli:
    def __init__(self) -> None:
        self.nm = NotesManager(config.notes_dir)
        # for tm command
        self.current_note: Optional[Note] = None
        self.current_task: Optional[TaskNode] = None
        self.current_tags = []
        self.current_list = "in"
        self.current_list_reversed = False

    @needs_db
    def test(self, *args: str) -> None:
        print("test command")
        # note = self.nm.load_note('/home/serg/mydb/data/yaml_notes/309.norg')
        # print(note.params)

    @needs_db
    def index_tasks(self, *args: str) -> None:
        for arg in args:
            if arg == "-c":
                print("Deleting all from yaml_notes_tasks...")
                db.cur.execute("DELETE FROM yaml_notes_tasks")
                db.con.commit()
        print("Indexing tasks...")
        l = db.ListNotesById()
        indexed_at = datetime.datetime.now()
        for n in l.iter():
            filepath = os.path.join(config.notes_dir, n["relative_path"])
            note = self.nm.load_note(filepath)
            if not note.is_active():
                continue
            print(f" {note.get_id()}", end="")
            for task_node in note.noteFormat.noteNode.iter_tasks():
                print(".", end="")
                task = Task().from_task_node(task_node, note)
                task.indexed_at = indexed_at
                parent_task_node = task_node.find_parent(TaskNode)
                if parent_task_node:
                    parent_task = Task().from_task_node(parent_task_node, note)
                    parent_task_from_db = db.find_first(
                        "yaml_notes_tasks",
                        {
                            "text": parent_task.text,
                            "note_id": parent_task.note_id,
                            "line_number_in_note": parent_task.line_number_in_note,
                        },
                    )
                    task.parent_task_id = parent_task_from_db["id"]
                db.replace_task(task)
        print("\nAll tasks indexed")

    it = index_tasks

    @needs_db
    def __tm_step(self, *args, **kwargs):
        if "inp" in kwargs and type(kwargs["inp"]) is str:
            inp = kwargs["inp"]
        else:
            inp = input("tasks > ")
        cmd = inp.split()[0]
        args = []
        if " " in inp:
            args = inp.split()[1:]
        if cmd.lower() in ["q", "quit", "exit"]:
            return "exit"
        elif cmd.lower() in ["e", "edit"]:
            if len(args) > 0:
                note_id = int(args[0])
            elif type(self.current_note) is Note:
                note_id = self.current_note.get_id()
            else:
                raise Exception("No note_id")
            self.edit(note_id)
        elif cmd.lower() in ["s", "skip"]:
            if type(self.current_note) is not Note:
                raise Exception("No current note")
            if type(self.current_task) is not TaskNode:
                raise Exception("No current task")
            skipped_tasks = db.get_json_option(db.SKIPPED_TASKS_KEY, [])
            skipped_tasks.append(
                {
                    "note_id": self.current_note.get_id(),
                    "line_number": self.current_task.line_number,
                }
            )
            db.set_json_option(db.SKIPPED_TASKS_KEY, skipped_tasks)
        elif cmd.lower() in ["sn", "skip-note"]:
            if type(self.current_note) is not Note:
                raise Exception("No current note")
            skipped_tasks = db.get_json_option(db.SKIPPED_TASKS_KEY, [])
            skipped_tasks.append(
                {
                    "note_id": self.current_note.get_id(),
                }
            )
            db.set_json_option(db.SKIPPED_TASKS_KEY, skipped_tasks)
        elif cmd.lower() in ["st", "skip-tag"]:
            skipped_tasks = db.get_json_option(db.SKIPPED_TASKS_KEY, [])
            skipped_tasks.append(
                {
                    "tag": args[0],
                }
            )
            db.set_json_option(db.SKIPPED_TASKS_KEY, skipped_tasks)
        elif cmd.lower() in ["cs", "clear-skips"]:
            db.set_json_option(db.SKIPPED_TASKS_KEY, [])
        elif cmd.lower() in ["t", "tag"]:
            self.current_tags.append(args[0])
        elif cmd.lower() in ["ct", "clear-tags"]:
            self.current_tags = []
        elif cmd.lower() == "ss":
            self.__tm_step(inp="s")
            self.__tm_step(inp="f")
        elif cmd.lower() in ["help", "h", "?"]:
            print("Use one command:")
            print("  h | help | ?")
            print("  e | edit -- edit note that contains current printed task")
            print("  q | quit | exit")
            print("  (first | f) [not | n] (in | s | r) -- gets first task from list ")
            print("      lists:")
            print(
                "         -- in - simple task without any tags (tasks ready for sorting)"
            )
            print("         -- s - sorted tasks with priority and urgency")
            print("         -- r - tasks ready to be completed")
            print("  s | skip")
            print("  sn | skip-note")
            print("  st | skip-tag")
            print("  cs | clear-skips ")
            print("  t | tag : TAG_NAME -- show tasks only for this tag")
            print("  ct | clear-tags -- unset all tags that be sets by tag")
        else:
            self.t(*inp.split())

    @needs_db
    def task_manager(self, *args):
        while True:
            try:
                if self.__tm_step(*args) == "exit":
                    break
            except Exception as e:
                print(e)

    tm = task_manager

    @needs_db
    def task(self, *args: str):
        def check_in_list(task: TaskNode):
            return task.is_simple()

        def check_ready_or_in_progress_list(task: TaskNode):
            return task.isInProgress

        def check_sorted_list(task: TaskNode):
            return task.is_sorted()

        lists = {
            "in": check_in_list,
            "r": check_ready_or_in_progress_list,
            "s": check_sorted_list,
        }
        skipped_tasks = db.get_json_option(db.SKIPPED_TASKS_KEY, [])
        reversed_list = False
        if args[0] == "first" or args[0] == "f":
            if len(args) >= 3:
                if args[1] in ["n", "not"]:
                    reversed_list = True
                selected_list = args[2]
                self.current_list = selected_list
                self.current_list_reversed = reversed_list
            elif len(args) >= 2:
                selected_list = args[1]
                self.current_list = selected_list
            else:
                selected_list = self.current_list
                reversed_list = self.current_list_reversed
            print("Finding first task in", repr(selected_list), "list")
            l = db.ListNotesById()
            for n in l.iter():
                if {"note_id": n["id"]} in skipped_tasks:
                    continue
                filepath = os.path.join(config.notes_dir, n["relative_path"])
                note = self.nm.load_note(filepath)
                if not note.is_active():
                    continue
                to_skip = False
                for tag in note.get_tags():
                    if {"tag": tag} in skipped_tasks:
                        to_skip = True
                        break
                if to_skip:
                    continue
                if self.current_tags:
                    to_skip = True
                    for tag in note.get_tags():
                        if tag in self.current_tags:
                            to_skip = False
                            break
                if to_skip:
                    continue
                self.current_note = note
                for task_node in note.noteFormat.noteNode.iter_tasks():
                    if task_node.isDone:
                        continue
                    task_location = {
                        "note_id": self.current_note.get_id(),
                        "line_number": task_node.line_number,
                    }
                    if task_location in skipped_tasks:
                        continue
                    is_task_in_list = lists[selected_list](task_node)
                    if reversed_list:
                        is_task_in_list = not is_task_in_list
                    if is_task_in_list:
                        print("=" * 20)
                        print(filepath)
                        print("-" * 10, "params:")
                        print(yaml.safe_dump(note.params, allow_unicode=True))
                        print("-" * 10, "task on", f"line {task_node.line_number}")
                        print(task_node.to_text())
                        print("=" * 20)
                        self.current_task = task_node
                        return
            print("Tasks in list", '"' + selected_list + '"', "not found!")
        else:
            print("Subcommand", args[0], "not found")

    t = task

    @needs_db
    def delete_note(self, *args: str) -> None:
        note_id = int(args[0])
        note = db.get_note_by_id(note_id)
        print("Note for delete:")
        print("-" * 30)
        pp.pprint(note)
        print("-" * 30)
        ans = input("ok? y/n > ")
        if ans == "y":
            db.delete_note_by_id(note_id)
            print("note deleted from db")
            filepath = path.join(self.nm.notes_dir, note["relative_path"])
            os.remove(filepath)
            print("file", filepath, "of note deleted")

    d = delete_note

    @needs_db
    def save_notes_in_db(self, *args: str) -> None:
        print("Saving all notes in db...")
        done = 0
        progress = 0
        total = self.nm.get_next_note_id(False)
        for note in self.nm.iter_notes(by_db=False):
            db.save_note(note)
            if db.cur.rowcount <= 0:
                print("Note is not saved?", note.params)
            child_files = note.get_child_files()
            if len(child_files):
                for i, child_filepath in enumerate(child_files, 1):
                    db.save_note_child_file(note, child_filepath)
            done += 1
            percent = (done / total) * 100
            if int(percent / 10) > progress:
                print(progress * 10, end=" ", flush=True)
                progress += 1
        print("\nEnd!")

    @needs_db
    def restore_all_notes_from_db(self, *args: str) -> None:
        res = db.cur.execute("SELECT * FROM yaml_notes")
        for note_row in res.fetchall():
            filepath = path.join(config.notes_dir, note_row["relative_path"])
            note = Note()
            note.text = note_row["text"]
            note.params = yaml.safe_load(note_row["yaml_parameters"])
            note.set_filepath(filepath)
            note.save()
            res_child_files = db.cur.execute(
                "SELECT * FROM yaml_notes_child_files WHERE note_id = ?",
                (note.get_id(),),
            )
            for child_file_row in res_child_files:
                child_file_filepath = path.join(
                    config.notes_dir, child_file_row["relative_path"]
                )
                note.save_child_file(child_file_filepath, child_file_row["content"])

    @needs_db
    def delete_all_notes(self, *args: str) -> None:
        for note in self.nm.iter_notes():
            note.full_remove()
        self.clean_empty_folders()

    @needs_db
    def add(self, *args: str) -> None:
        tags = []
        i = 0
        noteFormat = config.get_default_format_class()()
        while True:
            if i >= len(args):
                break
            arg = args[i]
            if arg in ["tags", "t"]:
                i += 1
                tags += args[i].split(",")
            elif arg == "md":
                noteFormat = MdNoteFormat()
            elif arg == "norg":
                noteFormat = NorgNoteFormat()
            i += 1
        note = self.nm.make_note(noteFormat)
        for tag in tags:
            note.add_tag(tag)
        note.save()
        print(
            f"New note with id {note.get_param('id')} created in path: {note.filepath}"
        )

    a = add

    @needs_db
    def add_task(self) -> None:
        note = self.nm.make_note()
        note.add_tag("task")
        note.set_param("done", False)
        note.save()
        print(
            f"New task with id {note.get_param('id')} created in path: {note.filepath}"
        )

    at = add_task

    @needs_db
    def git_commit(self, msg="just_commit") -> None:
        root_folder = path.abspath(config.notes_dir)
        git_commit_cmd = f"cd {root_folder}"
        git_commit_cmd += " && git add ."
        git_commit_cmd += f" && git commit -m '{msg}'"
        print("Cmd for commit changes:", git_commit_cmd)
        os.system(git_commit_cmd)

    @needs_db
    def commit(self, *args) -> None:
        self.git_commit("before default action")
        self.default(by_db="fs" not in args)
        self.git_commit("after default action")
        if len(args) and "s" in args:
            self.save_notes_in_db()

    c = commit

    @needs_db
    def edit(self, note_id_arg: Optional[Union[str, int]] = None):
        if not note_id_arg:
            note_id_arg = db.get_option(db.NEXT_NOTE_ID_OPTION_KEY)
            if type(note_id_arg) is not str:
                raise Exception("note_id argument is not string")
            note_id = int(note_id_arg) - 1
        else:
            note_id = int(note_id_arg)
        editor = os.environ.get("EDITOR", "vim")
        note = db.get_note_by_id(note_id)
        filepath = os.path.join(config.notes_dir, note["relative_path"])
        subprocess.call([editor, filepath])

    e = edit

    def __search_parse_args(self, args):
        search_tags = []
        exclude_tags = []
        active_only = False
        i = 0
        if not len(args):
            raise Exception("No search parameters!")
        while True:
            if i >= len(args):
                break
            arg = args[i]
            if arg in ["tags", "t"]:
                i += 1
                search_tags += args[i].split(",")
            elif arg in ["exclude-tags", "et"]:
                i += 1
                exclude_tags += args[i].split(",")
            elif arg in ["a", "active"]:
                active_only = True
            i += 1
        return {
            "search_tags": search_tags,
            "exclude_tags": exclude_tags,
            "active_only": active_only,
        }

    def __search(self, search_options):
        search_tags = search_options["search_tags"]
        exclude_tags = search_options["exclude_tags"]
        active_only = search_options["active_only"]
        search_result: list[Note] = []
        for note in self.nm.iter_notes():
            is_ok = True
            note_tags = note.get_tags()
            for tag in search_tags:
                if tag not in note_tags:
                    is_ok = False
                    break
            for tag in note_tags:
                if tag in exclude_tags:
                    is_ok = False
                    break
            if active_only and not note.get_bool_param("active"):
                is_ok = False
            if is_ok:
                search_result.append(note)
        return search_result

    @needs_db
    def search(self, *args: str):
        search_options = self.__search_parse_args(args)
        search_result = self.__search(search_options)
        table = []
        for i, note in enumerate(search_result):
            id = note.get_param("id")
            tags = note.get_tags()
            filepath = note.filepath
            content = note.text.strip()[:100]
            table.append([id, ", ".join(tags), filepath, content])
        print(
            tabulate(
                table,
                headers=["id", "tags", "filepath", "content"],
                tablefmt="simple_grid",
            )
        )

    s = search

    @needs_db
    def process_all(self):
        # for temporary code
        # for note in self.nm.iter_notes():
        #     pass
        pass

    @needs_db
    def tags(self) -> None:
        tag_count = defaultdict(lambda: 0)
        for note in self.nm.iter_notes():
            for tag in note.get_tags():
                tag_count[tag] += 1
        for k, v in sorted(tag_count.items(), key=lambda x: x[1]):
            print(f"{k:15}: {v}")

    @needs_db
    def last(self, n: str = "5") -> None:
        n = int(n)
        notes = list(self.nm.iter_notes())
        notes.sort(key=lambda n: n.get_param("id"))
        for note in notes[-n:]:
            print(
                f"{note.get_param('id'):3}: {', '.join(sorted(note.get_tags()))}: {note.filepath}"
            )

    @needs_db
    def clean_empty_folders(self):
        clean_empty_folders_cmd = f"cd {config.notes_dir}"
        clean_empty_folders_cmd += (
            ' && find . -type d -empty -not -path "./.git/*" -delete'
        )
        print("Run clean empty folders cmd:", clean_empty_folders_cmd)
        os.system(clean_empty_folders_cmd)

    @needs_db
    def default(self, *args, by_db=True) -> None:
        for note in self.nm.iter_notes(by_db=by_db):
            tags_s = "_".join(note.get_tags())
            if self.nm.is_for_archive(note):
                self.nm.archive(note)
            else:
                self.nm.move_in_dirs_by_tags(note)
            note = self.nm.load_note(note.real_filepath)
            name = f"{note.get_param('id'):03}_{tags_s}"
            filename = f"{name}.{note.noteFormat.get_default_file_extension()}"
            self.nm.rename_note(note, filename)
        if config.clear_empty_folders:
            self.clean_empty_folders()

    @needs_db
    def projects(self):
        projects = set()
        for note in self.nm.iter_notes():
            if note.has_param("project"):
                projects.add(note.get_param("project"))
        print("Current projects:", *projects)

    @needs_db
    def total(self):
        all_tags = set()
        total_notes = 0
        for note in self.nm.iter_notes():
            for tag in note.get_tags():
                all_tags.add(tag)
            total_notes += 1
        print("Total notes:", total_notes)
        print("Total tags:", len(all_tags))

    @needs_db
    def from_folder(self, root_folder: str):
        note = self.nm.make_note()

        note.text += f"### Files from {root_folder}\n\n"

        for root, dirs, files in os.walk(root_folder):
            for filename in files:
                code_type = ""
                codes_that_same_as_ext = ["php", "yml", "yaml", "js", "py"]
                for ext_and_code in codes_that_same_as_ext:
                    if filename.endswith("." + ext_and_code):
                        code_type = ext_and_code
                filepath = os.path.join(root, filename)
                with open(filepath, "r") as file:
                    file_contents = file.read()
                note.text += f"`{os.path.relpath(filepath, root_folder)}`:\n"
                note.text += f"```{code_type}\n"
                note.text += file_contents
                note.text += f"\n```\n\n"

        note.save()

    def help(self):
        print("help")

    h = help

    def run_migrations(self):
        res = db.cur.execute(
            """
                SELECT 
                    name
                FROM 
                    sqlite_schema
                WHERE 
                    type ='table' AND 
                    name NOT LIKE 'sqlite_%';
            """
        )
        db_tables = list(map(lambda m: m["name"], res.fetchall()))
        tables_to_found = [
            "yaml_notes_options",
            "yaml_notes_tags",
            "yaml_notes",
            "yaml_notes_child_files",
            "yaml_notes_tasks",
        ]
        for tbl in tables_to_found:
            if tbl in db_tables:
                print(
                    f"Table `{tbl}` already exists in the database, so migrations are skipped"
                )
                return
        print("Running migrations...")
        db.run_migrations()
        print("done")

    @needs_db
    def clear_notes_in_db(self):
        db.clear_table("yaml_notes_child_files")
        db.clear_table("yaml_notes_tasks")
        db.clear_table("yaml_notes")

    def config(self):
        print("--- base ---")
        print("version:", config.version)
        print("app_root:", config.app_root)
        print("notes_dir:", config.notes_dir)
        print("db_path:", config.db_path)
        print("--- additional ---")
        print("default_format_ext:", config.default_format_ext)
        print("clear_empty_folders:", config.clear_empty_folders)

    @needs_db
    def config_db(self):
        print("--- base ---")
        print("version:", config.version)
        print("app_root:", config.app_root)
        print("notes_dir:", config.notes_dir)
        print("db_path:", config.db_path)
        print("--- additional ---")
        print("default_format_ext:", config.default_format_ext)
        print("clear_empty_folders:", config.clear_empty_folders)

    def init(self):
        self.run_migrations()
        save_config_in_db()

    def save_config_in_db(self):
        save_config_in_db()

    @needs_db
    def get_json_search_result(self, *args):
        search_options = self.__search_parse_args(args)
        search_result = self.__search(search_options)
        result = {
            "notes": [],
        }
        for note in search_result:
            result["notes"].append(note.to_dict_for_json())
        return json.dumps(result)

    @needs_db
    def json_search(self, *args):
        print(self.get_json_search_result(*args))


if __name__ == "__main__":
    db.init_db()
    cli = Cli()
    if len(sys.argv) > 1:
        getattr(cli, sys.argv[1])(*sys.argv[2:])
    else:
        cli.default()
    db.con.close()
