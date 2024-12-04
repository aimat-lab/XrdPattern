from __future__ import annotations

import logging
import os
from collections import Counter
from dataclasses import dataclass
from typing import Optional, Any

from matplotlib import pyplot as plt

from holytools.fsys import FsysNode
from holytools.logging import LoggerFactory
from holytools.userIO import TrackedCollection
from xrdpattern.parsing import MasterParser, Formats, Orientation
from xrdpattern.xrd import XRayInfo, XrdPatternData
from .db_report import DatabaseReport
from .pattern import XrdPattern

patterdb_logger = LoggerFactory.get_logger(name=__name__)
parser = MasterParser()

# -------------------------------------------

@dataclass
class PatternDB:
    patterns : list[XrdPattern]
    failed_files : list[str]
    fpath_dict: dict[str, list[XrdPattern]]
    name : str = ''

    # -------------------------------------------
    # save/load

    def save(self, dirpath : str, label_groups : bool = False, force_overwrite : bool = False):
        if os.path.isfile(dirpath):
            raise ValueError(f'Path \"{dirpath}\" is occupied by file')
        os.makedirs(dirpath, exist_ok=True)

        if label_groups:
            for j, patterns in enumerate(self.fpath_dict.values()):
                for k, p in enumerate(patterns):
                    fpath = os.path.join(dirpath, f'pattern_group_{j}_{k}.{Formats.aimat_suffix()}')
                    p.save(fpath=fpath, force_overwrite=force_overwrite)

        else:
            for j, pattern in enumerate(self.patterns):
                fpath = os.path.join(dirpath, f'pattern_{j}.{Formats.aimat_suffix()}')
                pattern.save(fpath=fpath, force_overwrite=force_overwrite)


    @classmethod
    def load(cls, dirpath : str,
             suffixes : Optional[list[str]] = None,
             csv_orientation : Optional[Orientation] = None) -> PatternDB:
        dirpath = os.path.normpath(path=dirpath)
        if not os.path.isdir(dirpath):
            raise ValueError(f"Given path {dirpath} is not a directory")

        data_fpaths = cls.get_xrd_fpaths(dirpath=dirpath, selected_suffixes=suffixes)
        if len(data_fpaths) == 0:
            raise ValueError(f"No data files matching suffixes {suffixes} found in directory {dirpath}")

        fpath_dict = {}
        failed_files = []
        patterns : list[XrdPattern] = []
        def extract(xrd_fpath : str) -> list[XrdPatternData]:
            return parser.extract(fpath=xrd_fpath, csv_orientation=csv_orientation)

        for fpath in TrackedCollection(data_fpaths):
            try:
                new_patterns = [XrdPattern(**info.to_dict()) for info in extract(fpath)]
                patterns += new_patterns
                fpath_dict[fpath] = new_patterns
            except Exception as e:
                failed_files.append(fpath)
                patterdb_logger.warning(msg=f"Could not import pattern from file {fpath}: \"{e}\"\n")

        return PatternDB(patterns=patterns, fpath_dict=fpath_dict, failed_files=failed_files)

    @staticmethod
    def get_xrd_fpaths(dirpath: str, selected_suffixes : Optional[list[str]]) -> list[str]:
        if selected_suffixes is None:
            selected_suffixes = Formats.get_all_suffixes()

        root_node = FsysNode(path=dirpath)
        xrd_file_nodes = root_node.get_file_subnodes(select_formats=selected_suffixes)
        data_fpaths = [node.get_path() for node in xrd_file_nodes]

        return data_fpaths

    def set_xray(self, xray_info : XRayInfo):
        for p in self.patterns:
            p.powder_experiment.xray_info = xray_info

    # -------------------------------------------
    # attributes

    def __eq__(self, other):
        if not isinstance(other, PatternDB):
            return False
        if len(self.patterns) != len(other.patterns):
            return False
        for self_pattern, other_pattern in zip(self.patterns, other.patterns):
            if self_pattern != other_pattern:
                return False
        return True

    def exclude_critical(self):
        noncritical_patterns = [pattern for pattern in self.patterns if not pattern.get_parsing_report().has_critical()]
        for fpath, extracted_patterns in self.fpath_dict.items():
            self.fpath_dict[fpath] = [p for p in extracted_patterns if not p.get_parsing_report().has_critical()]
        return PatternDB(patterns=noncritical_patterns, fpath_dict=self.fpath_dict, failed_files=self.failed_files)


    def get_database_report(self) -> DatabaseReport:
        return DatabaseReport(data_dirpath=self.name, failed_files=self.failed_files, fpath_dict=self.fpath_dict)








































    def plot_quantity(self, attr : str = 'crystal_structure.spacegroup', print_counts : bool = False):
        quantity_list = []
        for j,pattern in enumerate(self.patterns):
            try:
                spg = nested_getattr(pattern, attr)
                quantity_list.append(spg)
            except:
                patterdb_logger.log(msg=f'Could not extract attribute \"{attr}\" from pattern {pattern.get_info_as_str()}',
                                    level=logging.WARNING)
        if not quantity_list:
            raise ValueError(f'No data found for attribute {attr}')

        counts = Counter(quantity_list)
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)

        if print_counts:
            print(f'-> Count distribution of {attr} in Dataset:')
            for key, value in sorted_counts:
                print(f'- {key} : {value}')

        keys, values = zip(*sorted_counts)
        if len(keys) > 30:
            keys = keys[:30]
            values = values[:30]

        def attempt_round(val : Any):
            if type(val) == int:
                return val
            try:
                rounded_val = round(val,2)
            except:
                rounded_val = val
            return rounded_val

        rounded_keys = [str(attempt_round(key)) for key in keys]
        print(f'Number of data patterns with label {attr} = {len(quantity_list)}')

        plt.figure(figsize=(10, 5))
        plt.bar(rounded_keys, values)
        plt.xlabel(attr)
        plt.ylabel('Counts')
        plt.title(f'Count distribution of {attr} in Dataset {self.name}')
        plt.xticks(rotation=90)
        plt.show()


def nested_getattr(obj: object, attr_string):
    attr_names = attr_string.split('.')
    for name in attr_names:
        obj = getattr(obj, name)
    return obj
