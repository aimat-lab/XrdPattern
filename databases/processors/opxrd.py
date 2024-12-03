import os
from typing import Optional

from databases.tools.fileIO import read_file, safe_cif_read
from databases.tools.csv_label import get_powder_experiment
from holytools.devtools import ModuleInspector
from holytools.fsys import SaveManager
from holytools.logging.tools import log_execution
from xrdpattern.parsing import Orientation
from xrdpattern.pattern import PatternDB
from xrdpattern.xrd import PowderExperiment, XRayInfo, XrdAnode


# -------------------------------------------

class OpXRDProcessor:
    def __init__(self, root_dirpath : str):
        self.root_dirpath : str = root_dirpath
        self.raw_dirpath : str = os.path.join(root_dirpath, 'processed')
        self.processed_dirpath : str = os.path.join(root_dirpath, 'final')
        self.cu_xray : XRayInfo = XrdAnode.Cu.get_xray_info()

    # ---------------------------------------
    # Parsing individual contributions

    def parse_all(self):
        methods = ModuleInspector.get_methods(self)
        parse_methods = [m for m in methods if not m.__name__.endswith('all') and 'parse' in m.__name__]

        for mthd in parse_methods:
            print(f'mthd name = {mthd.__name__}')
            mthd()

    def process(self, dirname: str,
                selected_suffixes : Optional[list[str]] = None,
                use_cif_labels : bool = False,
                xray_info : Optional[XRayInfo] = None,
                csv_orientation : Optional[Orientation] = None,
                label_groups : bool = False):
        print(f'Started processing contributino {dirname}')
        data_dirpath = os.path.join(self.raw_dirpath, dirname, 'data')
        contrib_dirpath = os.path.join(self.raw_dirpath, dirname)
        pattern_db = PatternDB.load(dirpath=data_dirpath, suffixes=selected_suffixes, csv_orientation=csv_orientation)

        self.attach_metadata(pattern_db, dirname=dirname)
        self.attach_labels(pattern_db=pattern_db, contrib_dirpath=contrib_dirpath, use_cif_labels=use_cif_labels)
        if xray_info:
            pattern_db.set_xray(xray_info=xray_info)
        for p in pattern_db.patterns:
            p.metadata.remove_filename()
        pattern_db.exclude_critical()

        self.save(pattern_db, dirname=dirname, label_groups=label_groups)

    # ---------------------------------------
    # Parsing steps

    @log_execution
    def attach_metadata(self, pattern_db : PatternDB, dirname : str):
        form_dirpath = os.path.join(self.raw_dirpath, dirname, 'form.txt')
        with open(form_dirpath, "r") as file:
            lines = file.readlines()
        form_data = {}
        for line in lines:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                form_data[key] = value

        for p in pattern_db.patterns:
            p.metadata.contributor_name = form_data["name_of_advisor"]
            p.metadata.institution = form_data["contributing_institution"]


    def attach_labels(self, pattern_db : PatternDB, contrib_dirpath: str, use_cif_labels : bool):
        if use_cif_labels:
            self.attach_cif_labels(pattern_db)
        else:
            self.attach_csv_labels(pattern_db, contrib_dirpath=contrib_dirpath)

    @log_execution
    def attach_cif_labels(self, pattern_db : PatternDB):
        for fpath, patterns in pattern_db.fpath_dict.items():
            dirpath = os.path.dirname(fpath)
            cif_fnames = [fname for fname in os.listdir(dirpath) if SaveManager.get_suffix(fname) == 'cif']

            phases = []
            for fname in cif_fnames:
                cif_fpath = os.path.join(dirpath, fname)
                attached_cif_content = read_file(fpath=cif_fpath)
                crystal_phase = safe_cif_read(cif_content=attached_cif_content)
                phases.append(crystal_phase)2

            phases = [p for p in phases if not p is None]
            powder_experiment = PowderExperiment.from_multi_phase(phases=phases)
            for p in patterns:
                p.powder_experiment = powder_experiment


    @log_execution
    def attach_csv_labels(self, pattern_db : PatternDB, contrib_dirpath : str):
        csv_fpath = os.path.join(contrib_dirpath, 'labels.csv')
        if not os.path.isfile(csv_fpath):
            print(f'No labels available for contribution {os.path.basename(contrib_dirpath)}')
            return

        for p in pattern_db.patterns:
            if p.powder_experiment.is_nonempty():
                raise ValueError(f"Pattern {p.get_name()} is already labeled")

        for pattern_fpath, file_patterns in pattern_db.fpath_dict.items():
            powder_experiment = get_powder_experiment(pattern_fpath=pattern_fpath, contrib_dirpath=contrib_dirpath)

            for p in file_patterns:
                p.powder_experiment = powder_experiment


    @log_execution
    def save(self, pattern_db : PatternDB, dirname : str, label_groups : bool):
        out_dirpath = os.path.join(self.processed_dirpath, dirname)
        if not os.path.isdir(out_dirpath):
            os.makedirs(out_dirpath)
        pattern_db.save(dirpath=out_dirpath,label_groups=label_groups, force_overwrite=True)
