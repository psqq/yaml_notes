from os import path


# DON'T CHANGE
version = "0.1.0"
all_formats_exts = ["md", "norg"]


# values that checks for conflicts in db
app_root = path.dirname(__file__)
notes_dir = path.abspath(path.join(app_root, "../../data/yaml_notes"))
db_path = path.abspath(path.join(app_root, "../../mydb.sqlite3"))

# values can be replaced by value in db
default_format_ext = "md"
clear_empty_folders = False


# DON'T CHANGE
def get_default_format_class():
    from formats.md.MdNoteFormat import MdNoteFormat
    from formats.norg.NorgNoteFormat import NorgNoteFormat

    if default_format_ext == "md" or default_format_ext not in all_formats_exts:
        return MdNoteFormat
    if default_format_ext == "norg":
        return NorgNoteFormat


try:
    import custom_config
except ModuleNotFoundError:
    pass
