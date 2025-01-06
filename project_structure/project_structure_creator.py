import zipfile
import sqlite3
import os
from pathlib import Path

# Исправленный импорт: убедитесь, что папка называется 'project_structure', а не 'project_stucture'
from project_structure.paths import (
    PROJECT_ROOT,
    STRUCTURE_DIR,
    STRUCTURE_FILE,
    IMAGES_STRUCTURE_FILE,
    ARCHIVE_FILE,
    IGNORE_DIRS,
    IGNORE_FILES,
    IMAGE_EXTENSIONS,
    IGNORE_EXT,
    DATABASE_SCHEMA_FILE,
    DB_DESCRIPTION_FILE,
    DATABASE_PATH
)


def should_ignore(file_path: Path, relative_path: Path, ignore_dirs, ignore_files, ignore_ext) -> bool:
    """
    Проверяет, нужно ли пропускать файл/директорию при архивировании (и в других операциях).
    """
    # Проверка на директории
    for ignore_dir in ignore_dirs:
        ignore_dir_path = Path(ignore_dir)
        if ignore_dir_path in relative_path.parents:
            print(f"Игнорируется файл/папка {relative_path} из-за игнорируемой директории {ignore_dir}")
            return True

    # Игнорируем по имени целиком (например, .DS_Store, project_archive.zip и пр.)
    if relative_path.name in ignore_files:
        print(f"Игнорируется файл {relative_path} из-за игнорируемого имени")
        return True

    # Игнорируем по расширению
    if relative_path.suffix.lower() in ignore_ext:
        print(f"Игнорируется файл {relative_path} из-за игнорируемого расширения")
        return True

    return False


def get_project_structure(root_dir: Path, output_file: Path, ignore_dirs):
    """
    Рекурсивно обходит структуру проекта и записывает дерево файлов в output_file.
    """
    with output_file.open('w', encoding='utf-8') as f:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            current_dir = Path(dirpath)
            try:
                relative_dir = current_dir.relative_to(root_dir)
            except ValueError:
                continue

            # Убираем из dirnames те, что содержатся в ignore_dirs (по имени),
            # чтобы не заходить внутрь. Например, если 'backup' в ignore_dirs, не заходить в 'backup'
            dirnames[:] = [
                d for d in dirnames
                if d not in ignore_dirs
            ]

            # Вычисляем уровень вложенности для отступов
            if relative_dir == Path('.'):
                level = 0
            else:
                level = len(relative_dir.parts)
            indent = '    ' * level
            f.write(f"{indent}{current_dir.name}/\n")

            subindent = '    ' * (level + 1)
            for name in filenames:
                f.write(f"{subindent}{name}\n")


def get_images_structure(root_dir: Path, image_extensions, output_file: Path, ignore_dirs):
    """
    Рекурсивно обходит структуру проекта и записывает дерево изображений в output_file.
    """
    with output_file.open('w', encoding='utf-8') as f:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            current_dir = Path(dirpath)
            try:
                relative_dir = current_dir.relative_to(root_dir)
            except ValueError:
                continue

            dirnames[:] = [
                d for d in dirnames
                if d not in ignore_dirs
            ]

            # Фильтруем только изображения
            image_files = [
                file for file in filenames
                if (current_dir / file).suffix.lower() in image_extensions
            ]
            if image_files:
                if relative_dir == Path('.'):
                    level = 0
                else:
                    level = len(relative_dir.parts)
                indent = '    ' * level
                f.write(f"{indent}{current_dir.name}/\n")
                subindent = '    ' * (level + 1)
                for name in image_files:
                    f.write(f"{subindent}{name}\n")


def export_database_schema(db_path: Path, output_file: Path):
    """
    Экспортирует полную схему базы данных, включая таблицы, индексы, вьюхи и триггеры.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        with output_file.open('w', encoding='utf-8') as f:
            # Экспортируем все объекты (таблицы, индексы, вьюхи, триггеры),
            # исключая служебное, если нужно (например sqlite_sequence).
            cursor.execute("SELECT type, name, sql FROM sqlite_master WHERE sql IS NOT NULL;")
            objects = cursor.fetchall()

            for obj_type, obj_name, obj_sql in objects:
                f.write(f"-- {obj_type.upper()}: {obj_name}\n")
                f.write(f"{obj_sql};\n\n")

            print(f"Схема базы данных экспортирована в '{output_file}'.")
        conn.close()
    except Exception as e:
        print(f"Ошибка при экспорте схемы базы данных: {e}")


def create_zip_archive(
    root_dir: Path,
    archive_path: Path,
    ignore_dirs,
    ignore_files,
    ignore_ext,
    extra_files_to_add=None
):
    """
    Создаёт zip-архив всего проекта, игнорируя ненужные файлы/папки.
    Также добавляет (в том же потоке) конкретные файлы (extra_files_to_add),
    чтобы избежать дубликатов.
    """
    added_rel_paths = set()

    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 1. Пробегаемся по всему проекту и добавляем всё, что не игнорируется
        for dirpath, dirnames, filenames in os.walk(root_dir):
            current_dir = Path(dirpath)
            try:
                relative_dir = current_dir.relative_to(root_dir)
            except ValueError:
                continue

            # Фильтрация вложенных директорий
            dirnames[:] = [
                d for d in dirnames
                if d not in ignore_dirs
            ]

            for filename in filenames:
                file_path = current_dir / filename
                rel_path = file_path.relative_to(root_dir)

                if should_ignore(file_path, rel_path, ignore_dirs, ignore_files, ignore_ext):
                    continue

                rel_path_str = str(rel_path).replace(os.sep, '/')
                if rel_path_str not in added_rel_paths:
                    zipf.write(file_path, arcname=rel_path_str)
                    added_rel_paths.add(rel_path_str)
                else:
                    print(f"Файл '{rel_path}' уже добавлен в архив, пропускаем.")

        # 2. Добавляем "специфические" файлы, если нужно
        if extra_files_to_add:
            for special_file in extra_files_to_add:
                if not special_file.exists() or not special_file.is_file():
                    print(f"Файл '{special_file}' не найден и не был добавлен в архив.")
                    continue

                # Относительный путь
                try:
                    arcname = special_file.relative_to(root_dir)
                except ValueError:
                    # Если файл вне root_dir
                    arcname = special_file.name

                arcname_str = str(arcname).replace(os.sep, '/')
                if arcname_str not in added_rel_paths:
                    zipf.write(special_file, arcname=arcname_str)
                    added_rel_paths.add(arcname_str)
                    print(f"Добавлен файл '{special_file}' в архив.")
                else:
                    print(f"Файл '{special_file}' уже есть в архиве, пропускаем.")
    print(f"Архив '{archive_path}' успешно создан.")


def create_all_codes_file(
    root_dir: Path,
    output_file: Path,
    ignore_dirs,
    ignore_files,
    ignore_ext,
    database_schema_file: Path = None
):
    """
    Создаёт файл all_codes.txt, в котором:
    1. Сначала (при наличии) пишется содержимое экспортированной схемы БД.
    2. Затем содержимое всех неигнорируемых .py файлов в формате:
       ---- FILE: <относительный путь> ----
       <содержимое файла>
    """
    with output_file.open('w', encoding='utf-8') as out:
        # 1. Добавляем схему БД (если есть и если она создана)
        if database_schema_file and database_schema_file.exists():
            db_schema_content = database_schema_file.read_text(encoding='utf-8', errors='replace')
            out.write("====== DATABASE SCHEMA BEGIN ======\n\n")
            out.write(db_schema_content)
            out.write("\n====== DATABASE SCHEMA END ======\n\n\n")
        else:
            out.write("-- Схема базы данных отсутствует или не была экспортирована --\n\n")

        # 2. Обходим все файлы проекта, игнорируя лишние, и добавляем только .py файлы
        for dirpath, dirnames, filenames in os.walk(root_dir):
            current_dir = Path(dirpath)
            try:
                relative_dir = current_dir.relative_to(root_dir)
            except ValueError:
                continue

            dirnames[:] = [
                d for d in dirnames
                if d not in ignore_dirs
            ]

            for filename in filenames:
                file_path = current_dir / filename
                rel_path = file_path.relative_to(root_dir)

                # Пропускаем файлы по тем же критериям игнорирования
                if should_ignore(file_path, rel_path, ignore_dirs, ignore_files, ignore_ext):
                    continue

                # Добавляем только .py файлы
                if file_path.suffix.lower() != '.py':
                    continue

                out.write(f"---- FILE: {rel_path} ----\n")
                try:
                    content = file_path.read_text(encoding='utf-8', errors='replace')
                except Exception as e:
                    content = f"Невозможно прочитать файл из-за ошибки: {e}\n"
                out.write(content)
                out.write("\n\n")


if __name__ == '__main__':
    # 1. Генерация структуры проекта
    print("Генерация структуры проекта...")
    get_project_structure(PROJECT_ROOT, STRUCTURE_FILE, IGNORE_DIRS)
    print(f"Структура проекта сохранена в '{STRUCTURE_FILE}'.")

    # 2. Генерация структуры изображений
    print("Генерация структуры изображений проекта...")
    get_images_structure(PROJECT_ROOT, IMAGE_EXTENSIONS, IMAGES_STRUCTURE_FILE, IGNORE_DIRS)
    print(f"Структура изображений сохранена в '{IMAGES_STRUCTURE_FILE}'.")

    # 3. Экспорт схемы базы данных
    print("Экспорт схемы базы данных...")
    if DATABASE_PATH.exists():
        export_database_schema(DATABASE_PATH, DATABASE_SCHEMA_FILE)
    else:
        print(f"База данных не найдена по пути: {DATABASE_PATH}")

    # 4. Создание списка «специфических» файлов, которые нужно гарантированно включить
    specific_files = [
        DATABASE_SCHEMA_FILE,   # schema
        IMAGES_STRUCTURE_FILE,  # images_structure.txt
        STRUCTURE_FILE,         # project_structure.txt
        DB_DESCRIPTION_FILE     # db_description.txt
    ]

    # 5. Создание ZIP-архива всего проекта + добавление «специфических» файлов
    print("Создание ZIP-архива проекта...")
    create_zip_archive(
        root_dir=PROJECT_ROOT,
        archive_path=ARCHIVE_FILE,
        ignore_dirs=IGNORE_DIRS,
        ignore_files=IGNORE_FILES,
        ignore_ext=IGNORE_EXT,
        extra_files_to_add=specific_files
    )

    # 6. Создание файла all_codes.txt со всеми .py файлами (и схемой БД в начале)
    print("Создание файла all_codes.txt со всеми .py файлами...")
    ALL_CODES_FILE = STRUCTURE_DIR / 'all_codes.txt'
    create_all_codes_file(
        root_dir=PROJECT_ROOT,
        output_file=ALL_CODES_FILE,
        ignore_dirs=IGNORE_DIRS,
        ignore_files=IGNORE_FILES,
        ignore_ext=IGNORE_EXT,
        database_schema_file=DATABASE_SCHEMA_FILE
    )
    print(f"Файл с кодами создан: {ALL_CODES_FILE}")

    # 7. Финальные сообщения
    print("\nПроцесс завершён успешно!")
    print(f"Архив: {ARCHIVE_FILE}")
    print(f"Файл структуры проекта: {STRUCTURE_FILE}")
    print(f"Файл структуры изображений: {IMAGES_STRUCTURE_FILE}")
    print(f"Схема базы данных: {DATABASE_SCHEMA_FILE}")
    print(f"Описание базы данных: {DB_DESCRIPTION_FILE}")
    print(f"Все коды: {ALL_CODES_FILE}")
