"""Extract the source day.csv into typed JSON for the workbook builder."""
import csv
import io
import json
from pathlib import Path
import zipfile

root=Path(__file__).resolve().parents[2]
with zipfile.ZipFile(root/'data/raw/bike.zip') as zipped:
    name=next(n for n in zipped.namelist() if n.endswith('day.csv'))
    rows=list(csv.DictReader(io.StringIO(zipped.read(name).decode())))
    for row in rows:
        for key in row:
            if key!='dteday':row[key]=float(row[key]) if key in ['temp','atemp','hum','windspeed'] else int(row[key])
target=root/'data/cache/bike_daily.json';target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(json.dumps(rows),encoding='utf-8')
