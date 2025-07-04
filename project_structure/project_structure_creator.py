# ============================= FILE: project_structure/project_structure_creator.py =============================
import zipfile
import sqlite3
import os
from pathlib import Path

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
    Checks if the file/dir should be ignored during archiving or other operations.
    """
    for ignore_dir in ignore_dirs:
        ignore_dir_path = Path(ignore_dir)
        if ignore_dir_path in relative_path.parents:
            print(f"Ignoring {relative_path} due to ignored directory {ignore_dir}")
            return True

    if relative_path.name in ignore_files:
        print(f"Ignoring file {relative_path} due to ignored name")
        return True

    if relative_path.suffix.lower() in ignore_ext:
        print(f"Ignoring file {relative_path} due to ignored extension")
        return True

    return False

def get_project_structure(root_dir: Path, output_file: Path, ignore_dirs):
    """
    Recursively walk the project structure and write the directory tree to output_file.
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
    Recursively walk the project and write the tree of images to output_file.
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
    Exports the full database schema including tables, indexes, views, and triggers.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        with output_file.open('w', encoding='utf-8') as f:
            cursor.execute("SELECT type, name, sql FROM sqlite_master WHERE sql IS NOT NULL;")
            objects = cursor.fetchall()

            for obj_type, obj_name, obj_sql in objects:
                f.write(f"-- {obj_type.upper()}: {obj_name}\n")
                f.write(f"{obj_sql};\n\n")

            print(f"Database schema exported to '{output_file}'.")
        conn.close()
    except Exception as e:
        print(f"Error exporting database schema: {e}")


def create_zip_archive(
    root_dir: Path,
    archive_path: Path,
    ignore_dirs,
    ignore_files,
    ignore_ext,
    extra_files_to_add=None
):
    """
    Creates a zip archive of the entire project, ignoring unneeded files/folders.
    Also adds any extra_files_to_add to the archive if needed.
    """
    added_rel_paths = set()

    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
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

                if should_ignore(file_path, rel_path, ignore_dirs, ignore_files, ignore_ext):
                    continue

                rel_path_str = str(rel_path).replace(os.sep, '/')
                if rel_path_str not in added_rel_paths:
                    zipf.write(file_path, arcname=rel_path_str)
                    added_rel_paths.add(rel_path_str)
                else:
                    print(f"File '{rel_path}' already in archive, skipping.")

        if extra_files_to_add:
            for special_file in extra_files_to_add:
                if not special_file.exists() or not special_file.is_file():
                    print(f"File '{special_file}' not found, skipping.")
                    continue

                try:
                    arcname = special_file.relative_to(root_dir)
                except ValueError:
                    arcname = special_file.name

                arcname_str = str(arcname).replace(os.sep, '/')
                if arcname_str not in added_rel_paths:
                    zipf.write(special_file, arcname=arcname_str)
                    added_rel_paths.add(arcname_str)
                    print(f"Added file '{special_file}' to archive.")
                else:
                    print(f"File '{special_file}' already in archive, skipping.")
    print(f"Archive '{archive_path}' created successfully.")


def create_all_codes_file(
    root_dir: Path,
    output_file: Path,
    ignore_dirs,
    ignore_files,
    ignore_ext,
    database_schema_file: Path = None
):
    """
    Creates a file all_codes.txt containing:
    1. The database schema (if available).
    2. The content of all non-ignored .py files with a heading.
    """
    with output_file.open('w', encoding='utf-8') as out:
        if database_schema_file and database_schema_file.exists():
            db_schema_content = database_schema_file.read_text(encoding='utf-8', errors='replace')
            out.write("====== DATABASE SCHEMA BEGIN ======\n\n")
            out.write(db_schema_content)
            out.write("\n====== DATABASE SCHEMA END ======\n\n\n")
        else:
            out.write("-- Database schema is missing or was not exported --\n\n")

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

                if should_ignore(file_path, rel_path, ignore_dirs, ignore_files, ignore_ext):
                    continue

                if file_path.suffix.lower() != '.py':
                    continue

                out.write(f"---- FILE: {rel_path} ----\n")
                try:
                    content = file_path.read_text(encoding='utf-8', errors='replace')
                except Exception as e:
                    content = f"Cannot read file due to error: {e}\n"
                out.write(content)
                out.write("\n\n")


if __name__ == '__main__':
    print("Generating project structure...")
    get_project_structure(PROJECT_ROOT, STRUCTURE_FILE, IGNORE_DIRS)
    print(f"Project structure saved to '{STRUCTURE_FILE}'.")

    print("Generating project images structure...")
    get_images_structure(PROJECT_ROOT, IMAGE_EXTENSIONS, IMAGES_STRUCTURE_FILE, IGNORE_DIRS)
    print(f"Images structure saved to '{IMAGES_STRUCTURE_FILE}'.")

    print("Exporting database schema...")
    if DATABASE_PATH.exists():
        export_database_schema(DATABASE_PATH, DATABASE_SCHEMA_FILE)
    else:
        print(f"Database not found at: {DATABASE_PATH}")

    specific_files = [
        DATABASE_SCHEMA_FILE,
        IMAGES_STRUCTURE_FILE,
        STRUCTURE_FILE,
        DB_DESCRIPTION_FILE
    ]

    print("Creating ZIP archive of the project...")
    create_zip_archive(
        root_dir=PROJECT_ROOT,
        archive_path=ARCHIVE_FILE,
        ignore_dirs=IGNORE_DIRS,
        ignore_files=IGNORE_FILES,
        ignore_ext=IGNORE_EXT,
        extra_files_to_add=specific_files
    )

    print("Creating all_codes.txt with all .py files...")
    ALL_CODES_FILE = STRUCTURE_DIR / 'all_codes.txt'
    create_all_codes_file(
        root_dir=PROJECT_ROOT,
        output_file=ALL_CODES_FILE,
        ignore_dirs=IGNORE_DIRS,
        ignore_files=IGNORE_FILES,
        ignore_ext=IGNORE_EXT,
        database_schema_file=DATABASE_SCHEMA_FILE
    )
    print(f"Codes file created: {ALL_CODES_FILE}")

    print("\nProcess finished successfully!")
    print(f"Archive: {ARCHIVE_FILE}")
    print(f"Project structure file: {STRUCTURE_FILE}")
    print(f"Images structure file: {IMAGES_STRUCTURE_FILE}")
    print(f"Database schema: {DATABASE_SCHEMA_FILE}")
    print(f"Database description: {DB_DESCRIPTION_FILE}")
    print(f"All codes: {ALL_CODES_FILE}")