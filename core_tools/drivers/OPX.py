"""
Very early version of driver for interacting with QM OPX. Using code from the OPX website and from Damaz & Christians drivers.

adapted from kitkat code from anderson lab
"""

from time import sleep, time
from typing import Dict, List
import json
import numpy as np
import ctypes  # only for DLL-based instrument
import time
import qcodes as qc
from qcodes.utils.validators import Numbers, Arrays
from qm.qua import *
from pathlib import Path

from qm import QuantumMachinesManager
from qm.qua import *
from qm import SimulationConfig
from qm import _Program
from functools import partial

import qcodes  # to get the db_location, should be possible without importing everything
from qcodes import (
    Instrument,
    VisaInstrument,
    Parameter,
    ManualParameter,
    MultiParameter,
    validators as vals,
    ParameterWithSetpoints,
)
from qcodes import ChannelList, InstrumentChannel


def parameter_lookup(opx_driver, command):
    def fun(*args, **kwargs):
        return getattr(getattr(opx_driver, 'qm'), command)(*args, **kwargs)
    return fun


class OPX(Instrument):
    """
    Very early version of driver for interacting with QM OPX. 
    """

    def __init__(self, config: Dict, connect_dict: Dict, name: str = "OPX", **kwargs) -> None:
        """
        Args:
            name: Name to use internally in QCoDeS
        """
        super().__init__(name, **kwargs)

        self.set_config(config=config)
        self.connect_dict = connect_dict
        self._connect()
        self.result_handles = None
        channels = ChannelList(self, 'QuantumElements', QuantumElement,
                               snapshotable=True)
        self.add_submodule("channels", channels)
        for qe in self.config['elements'].keys():
            channel = QuantumElement(self, qe)
            self.channels.append(channel)
            setattr(self, qe, channel)

    def execute_prog(self, prog):
        self.job = self.qm.execute(prog)
        self.result_handels = self.job.result_handles

    def set_config(self, config):
        self.config = config

    def _connect(self):
        begin_time = time.time()
        self.QMm = QuantumMachinesManager(host=self.connect_dict['qop_ip'],port=self.connect_dict['opx_port'],cluster_name=self.connect_dict['cluster_name'])
        self.QMm.close_all_quantum_machines()
        self.qm = self.QMm.open_qm(self.config)
        idn = {"vendor": "Quantum Machines", "model": "OPX"}
        idn.update(self.QMm.version_dict())
        t = time.time() - (begin_time or self._t0)

        con_msg = (
            "Connected to: {vendor} {model}, client ver.(qm-qua) = {qm-qua} , server ver.(QOP) ={QOP} "
            "in {t:.2f}s".format(t=t, **idn)
        )
        print(con_msg)
        print(self.QMm.version())
        self.log.info(f"Connected to instrument: {idn}")

    def clear_all_job_results(self):
        """Alias for QuantumMachinesManager.clear_all_job_results().
        Deletes cache of measurement results on server computer.
        """
        self.QMm.clear_all_job_results()

    def update_config(self):
        self.QMm.close_all_quantum_machines()
        self.qm = self.QMm.open_qm(self.config)

    def save_config(self, data_folder_path=None, filename=None):
        if data_folder_path == None:
            Path(data_folder_path).mkdir(parents=True, exist_ok=True)
            data_folder_path = str(qcodes.config.core.db_location)[:-3]+"\\"
        if filename == None:
            timestamp = int(time.time()*1e6)
            # should think of an appropriate file extension.. json?
            filename = f"{timestamp:d}_OPX_config"
        self.qm.save_config_to_file(data_folder_path+filename)


class QuantumElement(InstrumentChannel):
    def __init__(self, parent, name):
        self.opx_driver = parent
        self.qename = name
        super().__init__(parent, name)
        self.config = self.opx_driver.qm.get_config()

        self.add_parameter(name='IF_frequency',
                           label='IF Frequency',
                           unit='Hz',
                           set_cmd=partial(parameter_lookup(
                               self.opx_driver, 'set_intermediate_frequency'), self.qename),
                           initial_value=int(
                               self.config['elements'][self.qename]['intermediate_frequency']),
                           set_parser=float,
                           vals=vals.Numbers(-400e6, 400e6))
        #since there are N input and M outputs we still need to think of a clever way to encode that.
        # self.add_parameter(name='input_DC_offset',
        #                    label='Input DC Offset',
        #                    unit='V',
        #                    set_cmd=partial(parameter_lookup(
        #                        self.opx_driver, 'set_input_dc_offset_by_element'), self.qename),
        #                    get_cmd=partial(parameter_lookup(
        #                        self.opx_driver, 'get_input_dc_offset_by_element'), self.qename),
        #                    set_parser=float,
        #                    get_parser=float,
        #                    vals=vals.Numbers(-0.5, 0.5-2**-16))

        # self.add_parameter(name='output_DC_offset',
        #                    label='Output DC Offset',
        #                    unit='V',
        #                    set_cmd=partial(parameter_lookup(
        #                        self.opx_driver, 'set_output_dc_offset_by_element'), self.qename),
        #                    get_cmd=partial(parameter_lookup(
        #                        self.opx_driver, 'get_output_dc_offset_by_element'), self.qename),
        #                    set_parser=float,
        #                    get_parser=float,
        #                    vals=vals.Numbers(-0.5, 0.5-2**-16))

        self.add_parameter(name='smearing',
                           label='Smearing',
                           unit='ns',
                           get_cmd=partial(parameter_lookup(
                               self.opx_driver, 'get_smearing'), self.qename),
                           get_parser=float)

        self.add_parameter(name='time_of_flight',
                           label='Time of Flight',
                           unit='ns',
                           get_cmd=partial(parameter_lookup(
                               self.opx_driver, 'get_time_of_flight'), self.qename),
                           get_parser=float)

        #would be nice to do this a little cleaner, but is making yet another layer of channels the way to go?
        #that way we could also add things like length of course..
        for operation in self.config['elements'][self.qename]['operations'].keys():
            self.add_parameter(name=f'{operation}_amplitude',
                    label=f'{operation} Amplitude Scaling',
                    unit='',
                    set_parser=float,
                    vals=vals.Numbers(-2, 2-2**-16))



