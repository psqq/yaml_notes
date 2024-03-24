
Программа разрабатывалась "под себя" для личного пользования. Возможны баги, недоработки 💩.

# Основные особенности программы

* Является частью идеи `mydb` (позже тут будет ссылка о том, что это такое).
* Позволяет вести заметки по системе Цеттелькастен.
* Заметки создаются в виде обычных текстовых файлов в файловой системе.
* Размещение заметок по папкам и присваивание имен файлам происходит автоматически в зависимости от тегов.
* Есть команды для работы со списками задач (экспериментальная фича).

# Вариант установки

```shell
cd ~/mydb/code
git clone https://github.com/psqq/yaml_notes
cd yaml_notes
```

## Настройки

По умолчанию приложение считает, что:

* находится в папке `mydb/code/yaml_notes`
* заметки находятся в папке `../../data/yaml_notes` относительно того места где находится приложение
* `SQLite` база данных находится в папке `../../mydb.sqlite3` относительно того места где находится приложение

Посмотреть текущие настройки можно с помощью команды:

```shell
python cli.py config
```

Что поменять настройки скопируйте файл `custom_config_example.py` в `custom_config.py` и замените необходимые настройки.

## Инициализация

Данная команда запустит миграции и сохранит текущую значения из `config` в БД.

```shell
python cli.py init
```

## Добавление в PATH

Далее можно добавить скрипт `scripts/bin` в `PATH` для запуска `cli.py` с помощью сокращения `n`. Далее `n ...` - это сокращение для `python cli.py ...`.

# Заметка

Заметка - это файл `*.md` следующего вида:

<pre>
```yaml
- parameter1: value
- parameter2: value
```

Текст заметки.
</pre>

## Текст заметки

Текст может быть любым он парситься целиком сразу после параметров.

Из текста могу извлекаться задачи с помощью специальных команд.

## Параметры заметки

Изначально создается с такими параметрами:

```yaml
- id: 1
- active: true
- created_at: Сб 23 мар 2024 10:04:13
```

Есть также дополнительные параметры `tags` и `folder`:

```yaml
- id: 1
- active: true
- created_at: Сб 23 мар 2024 10:04:13
- tags:
  - home
  - hobby
- folder: y
```

* `id` - ид заметки, уникальный для каждой заметки;
* `active` - статус активности заметки, неактивные заметки перемещаются в папку `archive`;
* `created_at` - дата создания заметки;
* `tags` - теги заметки;
* `folder` - если установить в `true`, то заметка будет размещаться в папке с таким же именем, а все файлы, которые будут располагаться в этой папке будут считаться прикрепленными к данной заметке;

## Размещение заметок по папкам в зависимости от тегов

Если установить для опции `tags_for_dirs` в таблице `yaml_notes_options` следующие `JSON` значение:

```json
[
  [
    "tag-a",
  ],
  [
    "tag-b",
  ],
  [
    "tag-x",
    "tag-y",
    "tag-z"
  ]
]
```

то при запуске `n`, `n c`, `n default` заметки с тегами `tag-a`, `tag-b` будут размещены в папках `tag-a`, `tag-b`, а заметка, у которой установлены все три тега `tag-x`, `tag-y` и `tag-z` будет размещена в папке `tag-x/tag-y/tag-z`.

# Все команды

## Команды для работы с настройками

* `n save_config_in_db` - сохранить текущие настройки в БД
* `n config` - показывает текущие настройки без учета значений в БД
* `n config_db` - показывает текущие настройки с учетом значений из БД

## Команды для работы с заметками

Далее идет список всех доступных команд.

Заметки могут быть как формате `Markdown`, так и в `norg` ([https://github.com/nvim-neorg/norg-specs](https://github.com/nvim-neorg/norg-specs), [https://github.com/nvim-neorg/neorg](https://github.com/nvim-neorg/neorg)). Я все таки предпочитаю использовать формат `Markdown`, поэтому `norg` может поддерживаться не полностью.

Основные:

* `n a [t|tags {{tags}}]` - создает новую заметку
  * Примеры:
    * `n a tags linux,keyboard,x11 norg` - создаст заметку с тегами `linux`, `keyboard`, `x11` в формате `norg`.
    * `n a` - создаст заметку с минимальным набором параметров в формате по умолчанию (устанавливается в настройках)
* `n delete_note|d {{id}}` - удаляет заметку с указанным ид.
  * `n d 1` - удаляет заметку с `id = 1`
* `n default`, `n` - занимается размещением заметок по папкам в зависимости их параметров

git:

* `n commit|c` - удобная команда, если поместить заметки в `git` репозиторий.
  * Делает следующее:
    1. Создает коммит с сообщением `before default action` всех изменений в папке с заметками.
    2. Запускает действие по умолчанию `n default`.
    3. Снова создает коммит с сообщением `after default action` всех изменений в папке с заметками.
 * В основном используется для того, чтобы узнать или проконтролировать, что сделало действие по умолчанию и чтобы в случае неверных действий изменения можно было откатить.

Массовые команды:

* `n clear_notes_in_db` - удаляет все заметки и задачи в БД.
* `n save_notes_in_db` - сохраняет все заметки в БД.
* `n restore_all_notes_from_db` - команда извлекает из БД в папку в файловой системе.
* `n delete_all_notes` - удаляет все заметки в файловой системе.

Редактирование:

* `n edit|e [{{note_id}}]` - открывает заметку в редакторе по умолчанию или в `vim`. Если ид заметки не указан, то открывается последняя созданная заметка.

Поиск:

* `n search|s [tags|t {{tags}}] [exclude-tags|et {{exclude_tags}}] [a|active]` - поиск заметок
  * `[tags|t {{tags}}]` - теги для поиска
  * `[exclude-tags|et {{exclude_tags}}]` - теги исключения для поиска
  * `[a|active]` - искать только среди активных заметок
  * Пример: `n s t project,task a` - поиск заметок, у которых есть теги `project` и `task`, и заметка активная (`active == true`)
* `n last [{{n = 5}}]` - выводит последние `n` заметок в формате `id: tag1, tag2: /absolute/path/to/note.md`

Статистика:

* `n tags` - выводит список всех тегов и то солько раз они использовались в порядке убывания
* `n total` - выводит общую информацию о заметках

## Команды для работы с задачами

Команды для работы с задачами вдохновлены методом `GTD` из этой статьи: [https://hamberg.no/gtd](https://hamberg.no/gtd)

* `n index_tasks` - команда проходит по всем заметкам извлекает из них задачи и сохраняет в БД.
  * Сокращение: `n it`
* `n task|t first|f [[n|not] in|r|s]` - команда для поиска задач.
  * `n task first` - находит первую задачу.
  * Аргументом можно указать список, в котором искать задачу:
    * `in` - список "Входящих" задач. Это задачи, которые готовы к тому, чтобы их взяли на выполнение. Формально это задачи, которые:
        1. Не находятся в процессе выполнения.
        2. Не отменены.
        3. Не находятся в режиме ожидания (какого-то события).
    * `r` - список задач находящихся в процессе выполнения.
    * `s` - список отсортированных задач.
    * `[n|not]` - если указать перед список, то будут находится все задачи вне этого списка.
* `n task_manager|tm` - интерактивный менеджер задач. Внутри есть команда `help`, которая показывает справку.

TODO:

* `n add_task|at` - создает заметку-задачу. Создает, но пока что это нигде и никак не учитывается.

# Разработка

## Тесты

```bash
# run all tests
bash scripts/run_all_tests.sh
# run one specific test
bash scripts/run_test.sh NoteManager
```

## BUGS

- [ ] удаление заметок-папок (нет опции удалить все остальные файлы кроме заметки)

## TODO

- [ ] учитывать заметки-задачи в командах для работы с задачами
- [ ] возможность указать для заметки путь и/или имя файла
- [ ] поиск и работа с файлами, которые не относятся не к одной заметки (возможно остались после удаления заметок-папок)
- [ ] разбить код на модули и разместить в папке `yaml_notes`
- [ ] для `n c` добавить возможность указывать сообщение для коммита
