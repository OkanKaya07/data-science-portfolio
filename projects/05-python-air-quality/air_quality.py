"""Typed, repeatable UCI air-quality ETL. Python standard library only."""
from __future__ import annotations
import argparse
import csv
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import io
import json
import logging
from pathlib import Path
import sqlite3
import urllib.request
import zipfile
from contextlib import closing

URL = 'https://archive.ics.uci.edu/static/public/360/air%2Bquality.zip'
FIELDS = {'CO(GT)': 'co_mg_m3', 'C6H6(GT)': 'benzene_ug_m3', 'NO2(GT)': 'no2_ug_m3', 'T': 'temperature_c', 'RH': 'humidity_pct'}
LOG = logging.getLogger(__name__)

@dataclass(frozen=True)
class Observation:
    timestamp: str
    co_mg_m3: float | None
    benzene_ug_m3: float | None
    no2_ug_m3: float | None
    temperature_c: float | None
    humidity_pct: float | None

def number(value: str) -> float | None:
    if not value.strip():
        return None
    parsed = float(value.replace(',', '.'))
    if parsed == -200:
        return None
    if not __import__('math').isfinite(parsed):
        raise ValueError('Nonfinite numeric measurement')
    return parsed

def parse(source: str) -> tuple[list[Observation], dict]:
    reader = csv.DictReader(io.StringIO(source), delimiter=';')
    required = {'Date', 'Time', *FIELDS}
    if not required.issubset(reader.fieldnames or []):
        raise ValueError(f'Missing source fields: {sorted(required-set(reader.fieldnames or []))}')
    rows, seen = [], set()
    audit = {'blank_lines': 0, 'duplicates': 0, 'missing_values': {v: 0 for v in FIELDS.values()}}
    for line, row in enumerate(reader, start=2):
        if not row['Date'].strip() and not row['Time'].strip():
            audit['blank_lines'] += 1
            continue
        try:
            stamp = datetime.strptime(row['Date']+' '+row['Time'], '%d/%m/%Y %H.%M.%S').isoformat()
            values = {dest: number(row[src]) for src, dest in FIELDS.items()}
        except (ValueError, TypeError, AttributeError) as error:
            raise ValueError(f'Invalid record at CSV line {line}: {error}') from error
        observation = Observation(timestamp=stamp, **values)
        if stamp in seen:
            # A duplicate timestamp could contain conflicting measurements. Fail rather than choose one.
            raise ValueError(f'Duplicate timestamp at CSV line {line}: {stamp}')
        seen.add(stamp)
        for key, value in values.items():
            audit['missing_values'][key] += value is None
        rows.append(observation)
    if not rows:
        raise ValueError('No observations found')
    rows.sort(key=lambda x: x.timestamp)
    audit.update(rows=len(rows), start=rows[0].timestamp, end=rows[-1].timestamp)
    return rows, audit

def load_database(rows: list[Observation], database: Path) -> None:
    """Atomic replacement: reruns do not append duplicates or leave a partial table."""
    with closing(sqlite3.connect(database)) as con:
        with con:
            con.execute('BEGIN')
            con.execute('DROP TABLE IF EXISTS observations_stage')
            con.execute('CREATE TABLE observations_stage (timestamp TEXT PRIMARY KEY, co_mg_m3 REAL, benzene_ug_m3 REAL, no2_ug_m3 REAL, temperature_c REAL, humidity_pct REAL)')
            con.executemany('INSERT INTO observations_stage VALUES (?,?,?,?,?,?)', [tuple(asdict(r).values()) for r in rows])
            con.execute('DROP TABLE IF EXISTS observations')
            con.execute('ALTER TABLE observations_stage RENAME TO observations')

def run(archive: Path, output: Path, min_hours: int = 18) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    if not archive.exists():
        archive.parent.mkdir(parents=True, exist_ok=True)
        temporary = archive.with_suffix('.part')
        try:
            with urllib.request.urlopen(URL, timeout=120) as response:
                temporary.write_bytes(response.read())
            with zipfile.ZipFile(temporary) as zipped:
                zipped.getinfo('AirQualityUCI.csv')
            temporary.replace(archive)
        finally:
            temporary.unlink(missing_ok=True)
    with zipfile.ZipFile(archive) as zipped:
        rows, audit = parse(zipped.read('AirQualityUCI.csv').decode('utf-8-sig'))
    load_database(rows, output/'air_quality.sqlite')
    with closing(sqlite3.connect(output/'air_quality.sqlite')) as con:
        records = con.execute('''SELECT substr(timestamp,1,10) day, COUNT(*) recorded_hours,
            COUNT(co_mg_m3) valid_co_hours, AVG(co_mg_m3) observed_co_mean_mg_m3,
            CASE WHEN COUNT(co_mg_m3)>=? THEN AVG(co_mg_m3) END qualified_co_mean_mg_m3,
            AVG(temperature_c) observed_temperature_mean_c
            FROM observations GROUP BY 1 ORDER BY 1''',(min_hours,))
        headers=[d[0] for d in records.description]
        with (output/'daily_summary.csv').open('w',newline='',encoding='utf-8') as file:
            writer=csv.writer(file);writer.writerow(headers);writer.writerows(records)
    audit.update(source_url=URL,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),min_valid_co_hours=min_hours)
    (output/'quality_report.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    LOG.info('Loaded %s observations from %s through %s',len(rows),audit['start'],audit['end'])
    return audit

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,default=Path('data/raw/air.zip'))
    parser.add_argument('--output',type=Path,default=Path('projects/05-python-air-quality/reports'))
    parser.add_argument('--min-hours',type=int,choices=range(1,25),default=18)
    args=parser.parse_args()
    logging.basicConfig(level=logging.INFO,format='%(levelname)s %(message)s')
    try:
        run(args.archive,args.output,args.min_hours)
    except (ValueError,OSError,zipfile.BadZipFile,sqlite3.Error) as error:
        parser.exit(1,f'ETL failed: {error}\n')

if __name__=='__main__':
    main()
