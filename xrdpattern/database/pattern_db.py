from __future__ import annotations

import os.path
import os
from dataclasses import dataclass
from xrdpattern.pattern import XrdPattern, PatternReport
# -------------------------------------------


@dataclass
class XrdPatternDB:
    patterns : list[XrdPattern]
    num_data_files : int

    def save(self, path : str):
        is_occupied = os.path.isdir(path) or os.path.isfile(path)
        if is_occupied:
            raise ValueError(f'Path \"{path}\" is occupied by file/dir')
        os.makedirs(path, exist_ok=True)

        for pattern in self.patterns:
            fpath = os.path.join(path, pattern.get_name())
            pattern.save(fpath=fpath)

    def get_parsing_report(self) -> DatabaseReport:
        reports = [pattern.get_parsing_report() for pattern in self.patterns]
        database_health = DatabaseReport(num_data_files=self.num_data_files, pattern_reports=reports)
        pattern_healths = [pattern.get_parsing_report() for pattern in self.patterns]
        for report in pattern_healths:
            database_health.num_crit += report.has_critical()
            database_health.num_err += report.has_error()
            database_health.num_warn += report.has_warning()
        return database_health


@dataclass
class DatabaseReport:
    num_data_files : int
    pattern_reports: list[PatternReport]
    num_crit: int = 0
    num_err : int = 0
    num_warn : int = 0

    def get_str(self) -> str:
        num_failed = self.num_data_files-len(self.pattern_reports)
        summary_str = f'\n----- Finished creating database -----'
        if num_failed > 0:
            summary_str += f'\n{num_failed}/{self.num_data_files} patterns could not be parsed'
        else:
            summary_str += f'\nAll patterns were successfully parsed'
        summary_str += f'\n{self.num_crit}/{self.num_data_files} patterns had critical error(s)'
        summary_str += f'\n{self.num_err}/{self.num_data_files}  patterns had error(s)'
        summary_str += f'\n{self.num_warn}/{self.num_data_files}  patterns had warning(s)'

        individual_reports = '\n\nIndividual file reports:\n\n'
        for pattern_health in self.pattern_reports:
            individual_reports += f'{str(pattern_health)}\n\n'
        summary_str += f'\n\n----------------------------------------{individual_reports}'

        return summary_str