from __future__ import annotations

import json
from dataclasses import dataclass, fields, field

import numpy as np
from numpy.typing import NDArray
from scipy.interpolate import CubicSpline

from holytools.abstract import Serializable
from xrdpattern.xrd.metadata import Metadata
from xrdpattern.xrd.experiment import PowderExperiment


# -------------------------------------------

@dataclass
class XrdPatternData(Serializable):
    two_theta_values : NDArray
    intensities : NDArray
    powder_experiment : PowderExperiment
    metadata: Metadata = field(default_factory=Metadata)

    @classmethod
    def make_unlabeled(cls, two_theta_values: list[float], intensities: list[float]) -> XrdPatternData:
        metadata = PowderExperiment.make_empty()
        two_theta_values, intensities = np.array(two_theta_values), np.array(intensities)
        return cls(two_theta_values=two_theta_values, intensities=intensities, powder_experiment=metadata)

    def to_dict(self):
        return {f.name: getattr(self, f.name) for f in fields(self)}

    def _get_uniform(self, start_val : float, stop_val : float, num_entries : int) -> (list[float], list[float]):
        start, end = self.two_theta_values[0], self.two_theta_values[-1]
        std_angles = np.linspace(start=start_val, stop=stop_val, num=num_entries)

        x = np.array(self.two_theta_values)
        y = np.array(self.intensities)
        y -= np.min(y)

        cs = CubicSpline(x, y)
        mask = (std_angles >= start) & (std_angles <= end)
        std_intensities = cs(std_angles)
        std_intensities = std_intensities * mask

        max_intensity = np.max(std_intensities)
        normalization_factor = max_intensity if max_intensity > 0 else 1
        std_intensities = std_intensities/normalization_factor

        return std_angles, std_intensities

    def to_str(self) -> str:
        the_dict = {'two_theta_values' : self.two_theta_values.tolist(),
                    'intensities' : self.intensities.tolist(),
                    'label' : self.powder_experiment.to_str(),
                    'metadata' : self.metadata.to_str()}

        return json.dumps(the_dict)

    @classmethod
    def from_str(cls, json_str: str) -> XrdPatternData:
        data = json.loads(json_str)
        two_theta_values = np.array(data['two_theta_values'])
        intensities = np.array(data['intensities'])
        label = PowderExperiment.from_str(data['label'])
        metadata = Metadata.from_str(data['metadata'])

        return cls(two_theta_values=two_theta_values, intensities=intensities, powder_experiment=label, metadata=metadata)


    # ---------------------------------------
    # properties

    def get_name(self) -> str:
        return self.metadata.filename

    def get_phase(self, phase_num : int) -> CrystalPhase:
        return self.powder_experiment.phases[phase_num]

    @property
    def primary_phase(self) -> CrystalPhase:
        return self.powder_experiment.primary_phase

    @property
    def startval(self):
        return self.two_theta_values[0]

    @property
    def endval(self):
        return self.two_theta_values[-1]

    @property
    def xray_info(self) -> XRayInfo:
        return self.powder_experiment.xray_info

    @property
    def is_simulated(self) -> bool:
        return self.powder_experiment.is_simulated

    def __eq__(self, other : XrdPatternData):
        for attr in fields(self):
            v1, v2 = getattr(self, attr.name), getattr(other, attr.name)
            if isinstance(v1, np.ndarray):
                is_ok = np.array_equal(v1, v2)
            elif isinstance(v1, PowderExperiment):
                objs_equal = [str(x)==str(y) for x,y in zip(v1.get_list_repr(), v2.get_list_repr())]
                is_ok = all(objs_equal)
            else:
                is_ok = v1 == v2

            if not is_ok:
                return False

        return True


if __name__ == '__main__':
    pass