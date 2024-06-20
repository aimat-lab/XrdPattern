import numpy as np
# from xrdpattern.core import PatternData
from gemmi import cif
from numpy.typing import NDArray

from xrdpattern.core import Label, PatternData


class CifParser:
    def extract_patterns(self, fpath : str) -> PatternData:
        label = Label.from_file(cif_fpath=fpath)

        doc = cif.read_file(fpath)
        if len(doc) != 1:
            raise ValueError("Could not find pattern data in .cif located at {fpath}")

        block = doc.sole_block()
        x,y = self.extract_pattern_from_block(block)
        pattern_data = PatternData(intensities=y, two_theta_values=x,label=label)

        return pattern_data

    @staticmethod
    def extract_pattern_from_block(block) -> tuple[NDArray, NDArray]:
        x, y = None, None

        xfields = ["_pd_proc_2theta_corrected", "_pd_meas_2theta_scan", "_pd_meas_2theta"]
        yfields = ["_pd_meas_counts_total", "_pd_meas_counts", "_pd_meas_intensity_total", "_pd_meas_intensity",
                   "_pd_proc_intensity_total", "_pd_proc_intensity_net"]

        loops_gen = (i.loop for i in block if i.loop is not None)
        for loop in loops_gen:
            if find_tags(xfields, loop.tags) or find_tags(yfields, loop.tags):
                for yfield in yfields:
                    y = get_values_as_array(block, yfield)
                    if y is not None:
                        break

        rmin = block.find_value("_pd_meas_2theta_range_min")
        rmax = block.find_value("_pd_meas_2theta_range_max")
        npt = block.find_value("_pd_meas_number_of_points")
        npt = cif.as_int(npt)

        if None in [rmin, rmax]:
            raise ValueError("Could not find 2theta range")
        if not npt == len(y):
            raise ValueError("Number of points in 2theta range does not match number of intensities")

        rmin = cif.as_number(rmin)
        rmax = cif.as_number(rmax)
        x = np.linspace(rmin, rmax, len(y)).tolist()
        y = np.array(y)

        return x,y


def find_tags(needles, haystack):
    for needle in needles:
        if needle in haystack:
            return True
    return False


def get_values_as_array(block, name, minlength = 2):
    column = block.find_values(name)
    if len(column) >= minlength:
        return list(map(cif.as_number, column))

    return None


if __name__ == "__main__":
    example_fpath = '/home/daniel/Drive/data/workspace/cod/1101016.cif'
    parser = CifParser()
    parser.extract_patterns(fpath=example_fpath)