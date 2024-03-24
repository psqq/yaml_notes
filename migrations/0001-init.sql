CREATE TABLE `yaml_notes_options` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `key` TEXT NOT NULL,
    `value` TEXT
);

CREATE TABLE `yaml_notes_tags` (
    `tag` TEXT NOT NULL UNIQUE,
    `description` TEXT
);

CREATE TABLE `yaml_notes` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `text` TEXT NOT NULL DEFAULT '',
    `yaml_parameters` TEXT,
    `relative_path` TEXT NOT NULL DEFAULT '' UNIQUE,
    `tags` TEXT DEFAULT '[]',
    `created_at` DATE NOT NULL DEFAULT (datetime('now', 'localtime')),
    `updated_at` DATE NOT NULL DEFAULT (datetime('now', 'localtime')),
    `deleted_at` DATE DEFAULT NULL,
    `is_active` INTEGER DEFAULT 1,
    `json_parameters` TEXT
);

CREATE TABLE `yaml_notes_child_files` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `note_id` INTEGER NOT NULL,
    `content` BLOB,
    `relative_path` TEXT NOT NULL DEFAULT '' UNIQUE
);

CREATE TABLE `yaml_notes_tasks` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `parent_task_id` INTEGER DEFAULT NULL,
    `note_id` INTEGER DEFAULT NULL,
    `line_number_in_note` INTEGER DEFAULT NULL,
    `text` TEXT NOT NULL DEFAULT '',
    `order` INTEGER DEFAULT 0,
    `priority` INTEGER DEFAULT 0,
    `urgency` INTEGER DEFAULT 0,
    `created_at` DATE NOT NULL DEFAULT (datetime('now', 'localtime')),
    `updated_at` DATE NOT NULL DEFAULT (datetime('now', 'localtime')),
    `indexed_at` DATE NOT NULL DEFAULT (datetime('now', 'localtime')),
    `deleted_at` DATE DEFAULT NULL,
    `done_at` DATE DEFAULT NULL,
    `canceled_at` DATE DEFAULT NULL,
    `suspended_until` DATE DEFAULT NULL,
    UNIQUE(`note_id`, `line_number_in_note`, `text`)
);
