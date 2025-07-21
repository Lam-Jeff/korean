import sys
from dotenv import load_dotenv
import os
import logging
import sqlite3
import time
import uuid
import pandas as pd
import random

load_dotenv()
sys.path.append(f"{os.getenv('PATH_TO_PROJECT')}/korean")
from utils.dictionary import search_word_in_dictionary, search_example

logging.basicConfig(level=logging.INFO)


def create_db(path_to_db):
    connection = sqlite3.connect(path_to_db)
    return connection


def create_triggers(connection):
    cursor = connection.cursor()

    # Triggers for notes table
    cursor.execute(
        "CREATE TRIGGER IF NOT EXISTS log_insert_note AFTER INSERT ON notes BEGIN INSERT INTO logs (action, target_type, target_id, details) VALUES ('add_note','note',NEW.id,json_object('model_id', NEW.model_id,'flds', NEW.flds,'tags', NEW.tags));END;"
    )
    cursor.execute(
        "CREATE TRIGGER IF NOT EXISTS log_update_note AFTER UPDATE ON notes BEGIN INSERT INTO logs (action, target_type, target_id, details) VALUES ('edit_note','note',NEW.id,json_object('old_flds', OLD.flds,'new_flds', NEW.flds,'old_tags', OLD.tags,'new_tags', NEW.tags));END;"
    )
    cursor.execute(
        "CREATE TRIGGER IF NOT EXISTS log_delete_note AFTER DELETE ON notes BEGIN INSERT INTO logs (action, target_type, target_id, details) VALUES ('delete_note', 'note', OLD.id, json_object('flds', OLD.flds, 'tags', OLD.tags)); END;"
    )

    # Triggers for cards table
    cursor.execute(
        "CREATE TRIGGER IF NOT EXISTS log_insert_card AFTER INSERT ON cards BEGIN INSERT INTO logs (action, target_type, target_id, details) VALUES ('add_card', 'card', NEW.id, json_object('note_id', NEW.note_id, 'type', NEW.type, 'ords', NEW.ords)); END;"
    )

    cursor.execute(
        "CREATE TRIGGER IF NOT EXISTS log_update_card AFTER UPDATE ON cards BEGIN INSERT INTO logs (action, target_type, target_id, details) VALUES ('edit_card', 'card', NEW.id, json_object('old_reps', OLD.reps, 'new_reps', NEW.reps, 'old_flags', OLD.flags, 'new_flags', NEW.flags)); END;"
    )

    cursor.execute(
        "CREATE TRIGGER IF NOT EXISTS log_delete_card AFTER DELETE ON cards BEGIN INSERT INTO logs (action, target_type, target_id, details) VALUES ('delete_card', 'card', OLD.id, json_object('note_id', OLD.note_id, 'type', OLD.type, 'ords', OLD.ords)); END;"
    )


def create_tables(connection):
    cursor = connection.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY,guid TEXT, model_id INTEGER, mod INTEGER, tags TEXT, \
                                               flds TEXT,sfld TEXT, flags INTEGER, FOREIGN KEY(model_id) REFERENCES models(id))"
    )
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS cards (id INTEGER PRIMARY KEY, note_id INTEGER, mod INTEGER, type INTEGER, flags INTEGER, ords INTEGER, reps INTEGER, FOREIGN KEY(note_id) REFERENCES notes(id))"
    )

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS models (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)"
    )

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS model_fields (id INTEGER PRIMARY KEY, model_id INTEGER, name TEXT, ord INTEGER, FOREIGN KEY(model_id) REFERENCES models(id))"
    )

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS model_templates (id INTEGER PRIMARY KEY, model_id INTEGER, name TEXT, qfmt TEXT, afmt TEXT, FOREIGN KEY(model_id) REFERENCES models(id))"
    )

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT,  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, action TEXT NOT NULL, target_type TEXT NOT NULL, target_id INTEGER NOT NULL, details TEXT, success BOOLEAN DEFAULT 1)"
    )


def add_models(connection):
    cursor = connection.cursor()

    cursor.execute("INSERT INTO models (name) VALUES ('Korean Vocabulary');")
    cursor.execute(
        "INSERT OR IGNORE INTO model_fields (id, model_id, name, ord) VALUES (1, 1, 'Mot', 0),(2, 1, 'Traduction', 1),(3, 1, 'Exemple', 2);"
    )
    cursor.execute(
        "INSERT OR IGNORE INTO model_templates (id, model_id, name, qfmt, afmt) VALUES (1, 1, 'Mot → Traduction', '{{Mot}}', '{{FrontSide}}<hr>{{Traduction}}<br>{{Example}}'),(2, 1, 'Traduction → Mot', '{{Traduction}}', '{{FrontSide}}<hr>{{Mot}}<br>{{Example}}'), (3, 1, 'Mot -> Traduction', '{{Mot}}', '{{Traduction}}<br>{{Example}}<br>{{Comment}}');"
    )


def insert_row_notes(connection, data):
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM notes")
    id_list = cursor.fetchall()
    now = int(time.time())
    note_id = int(time.time() * 1000)
    while note_id in id_list:
        note_id += 1
    model_id = 1

    word = data["word"]
    translation = data["trans_word"]
    example = data["example"]
    comment = data["definition"]

    flds = "\x1f".join([word, translation, example, comment])
    sfld = word
    guid = str(uuid.uuid4())

    cursor.execute(
        """
    INSERT INTO notes(id, guid, model_id, mod, tags, flds, sfld, flags) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (note_id, guid, model_id, now, "Korean Vocabulary", flds, sfld, 0),
    )

    connection.commit()


def get_rows(connection, query):
    cursor = connection.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    return rows


def initialize_db(db):
    KOREAN_DICT_API_KEY = os.getenv("KOREAN_DICT_API_KEY")

    PATH_TO_PROJECT = os.getenv("PATH_TO_PROJECT")
    KOREAN_DICT_MAIN_URL = "https://krdict.korean.go.kr/api/search"  # 50_000 tokens/day
    # https://www.reddit.com/r/Korean/comments/rxvxz6/top_6000_topik_korean_vocabulary_word_list/
    excel_file = pd.read_excel(
        f"{PATH_TO_PROJECT}/korean/data/Korean_vocabular_TOPIK.xlsx"
    )
    data_list = []

    create_tables(db)
    create_triggers(db)
    add_models(db)

    for (
        _,
        row,
    ) in excel_file.iterrows():
        time.sleep(random.randint(1, 3))
        data = search_word_in_dictionary(
            row["Word"], KOREAN_DICT_API_KEY, KOREAN_DICT_MAIN_URL
        )

        example = search_example(row["Word"], KOREAN_DICT_API_KEY, KOREAN_DICT_MAIN_URL)

        if data:
            data["alt_def"] = row["English"]
            data["wiki_link"] = row["Wiktionary Link"]
            data["example"] = example
        else:
            data = {
                "word": row["Word"],
                "definition": "",
                "pos": "",
                "target_code": "",
                "trans_word": "",
                "alt_def": row["English"],
                "wiki_link": row["Wiktionary Link"],
                "wordreference_link": row["Wordreference Link"],
                "example": example,
            }
        data_list.append(data)
        insert_row_notes(db, data)

    df = pd.DataFrame(data_list)
    df.to_csv("data/notes.csv", encoding="utf-8", index=False)
    db.close()


PATH_TO_DB = os.getenv("PATH_TO_DB")
db = create_db(PATH_TO_DB)
try:
    rows = get_rows(db, "SELECT * from notes LIMIT 1;")
except sqlite3.OperationalError:
    rows = None
if rows is None:
    initialize_db(db)
