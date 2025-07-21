import sys
from dotenv import load_dotenv
import os
import json

load_dotenv()
PATH_TO_PROJECT = os.getenv("PATH_TO_PROJECT")
PATH_TO_DB = os.getenv("PATH_TO_DB")
sys.path.append(f"{PATH_TO_PROJECT}/korean")
from database.sqlite import create_db, get_rows

output_path = f"{PATH_TO_PROJECT}/korean/desklet/notes_output.json"

db = create_db(PATH_TO_DB)
query = "SELECT tags, flds, sfld, qfmt, afmt from notes, model_templates, models WHERE notes.model_id = models.id AND models.id = model_templates.model_id AND model_templates.id = 1 ORDER BY random() LIMIT 10;"
rows = get_rows(db, query)
db.close()

with open(output_path, "w") as f:
    json.dump([r for r in rows], f)
