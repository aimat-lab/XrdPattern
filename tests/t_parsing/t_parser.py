import os.path

from xrdpattern.pattern import XrdPattern
from xrdpattern.database import PatternDB
from tests.base_tests import PatternBaseTest, ParserBaseTest


class TestParserPattern(PatternBaseTest):
    def get_fpath(self) -> str:
        return self.get_bruker_fpath()

    def test_obj_ok(self):
        self.assertIsInstance(self.pattern, XrdPattern)
        print(f'serialized pattern')
        print(f'{self.pattern.to_str()[:1000]} + {self.pattern.to_str()[-1000:]}')

    def test_report_ok(self):
        report = self.pattern.get_parsing_report(datafile_fpath=self.get_fpath())
        as_str = report.get_report_str()
        self.assertIsInstance(obj=as_str, cls=str)
        print(f'Parsing report: {as_str}')

    def test_metadata_ok(self):
        metadata = self.pattern.metadata
        properties = [metadata.anode_material, metadata.measurement_date]
        print(f'anode material {metadata.anode_material}')
        print(f'measurement date {metadata.measurement_date}')

        for prop in properties:
            self.assertIsNotNone(obj=prop)

        primary_wavelength = metadata.primary
        secondary_wavelength = metadata.secondary
        ratio = metadata.ratio
        print(f'prim, sec, ratio {primary_wavelength}, {secondary_wavelength}, {ratio}')

        for prop in [primary_wavelength, secondary_wavelength, ratio]:
            self.assertIsNotNone(obj=prop)

        print(f'name : {self.pattern.get_name()}')
        self.assertIsNotNone(obj=self.pattern.get_name())
        original_name = os.path.basename(self.get_fpath())
        self.assertIn(self.pattern.get_name(), original_name)

    def test_data_ok(self):
        raw_data = self.pattern.get_pattern_data(apply_standardization=False)
        std_data = self.pattern.get_pattern_data(apply_standardization=True)
        for data in [raw_data, std_data]:
            self.check_data_ok(*data)

    def save(self):
        self.pattern.save(fpath='/home/daniel/local/misc/examples/aimat.json')


class TestParseStoe(PatternBaseTest):
    def get_fpath(self) -> str:
        return self.get_stoe_fpath()

    def test_parse_stoe(self):
        pattern = XrdPattern.load(fpath=self.get_fpath())
        self.assertIsInstance(pattern, XrdPattern)
        print(f'serialized pattern')
        print(f'{pattern.to_str()[:1000]} + {pattern.to_str()[-1000:]}')


from unittest.mock import patch
class TestParserDatabase(ParserBaseTest):
    bruker_only_db = None
    all_example_db = None

    @patch('builtins.input', lambda *args, **kwargs : 'VERTICAL')
    def test_db_parsing_ok(self):
        with self.assertNoLogs(level=0):
            TestParserDatabase.bruker_only_db = PatternDB.load(datafolder_path=self.get_datafolder_fpath())
            TestParserDatabase.all_example_db = PatternDB.load(datafolder_path=self.get_example_dirpath())

        for db in [self.bruker_only_db, self.all_example_db]:
            self.assertIsInstance(db, PatternDB)


    def test_db_report_ok(self):
        for db in [self.bruker_only_db, self.all_example_db]:
            report = db.database_report
            as_str = report.get_str()
            print(f'Parsing report: {as_str[:300]}')

            self.assertIsInstance(obj=as_str, cls=str)
            self.assertTrue(len(report.pattern_reports) > 0)


if __name__ == "__main__":
    TestParserDatabase.execute_all(manual_mode=False)

    # PatternDB.load(datafolder_path=PatternBaseTest.get_example_folderpath())
