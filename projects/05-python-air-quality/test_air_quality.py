import importlib.util
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing

spec=importlib.util.spec_from_file_location('air_quality',Path(__file__).with_name('air_quality.py'))
aq=importlib.util.module_from_spec(spec);sys.modules[spec.name]=aq;spec.loader.exec_module(aq)
HEADER='Date;Time;CO(GT);C6H6(GT);NO2(GT);T;RH\n'
ROW='10/03/2004;18.00.00;2,6;-200;113;13,6;48,9\n'

class PipelineTests(unittest.TestCase):
    def test_decimal_and_missing_sentinel(self):
        rows,audit=aq.parse(HEADER+ROW)
        self.assertEqual(rows[0].co_mg_m3,2.6)
        self.assertIsNone(rows[0].benzene_ug_m3)
        self.assertEqual(audit['missing_values']['benzene_ug_m3'],1)

    def test_invalid_schema_and_dates_fail(self):
        for text in ['Date;Time\n',HEADER+ROW.replace('10/03/2004','32/03/2004')]:
            with self.assertRaises(ValueError):aq.parse(text)

    def test_duplicate_timestamp_fails(self):
        with self.assertRaisesRegex(ValueError,'Duplicate timestamp'):aq.parse(HEADER+ROW+ROW)

    def test_rerun_does_not_duplicate(self):
        rows,_=aq.parse(HEADER+ROW)
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            path=Path(directory)/'test.sqlite'
            aq.load_database(rows,path);aq.load_database(rows,path)
            with closing(sqlite3.connect(path)) as con:
                self.assertEqual(con.execute('SELECT COUNT(*) FROM observations').fetchone()[0],1)
                self.assertIsNone(con.execute('SELECT benzene_ug_m3 FROM observations').fetchone()[0])

    def test_nonfinite_values_fail(self):
        with self.assertRaises(ValueError):aq.number('NaN')

if __name__=='__main__':unittest.main()
