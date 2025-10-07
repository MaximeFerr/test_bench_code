"""Utilities for running single-point SPIN measurements.

This module exposes a ``local_single_point`` helper that orchestrates the common
steps required to run a single-point test:

- loading VISA resource addresses from ``base-config.json``
- opening the HV power supply, Shield device, and any additional instruments
- applying standard device configuration and cleanup sequences

Callers provide callables to configure the Shield, initialise extra instruments,
performed tailored measurements, and optionally tweak the power supply setup.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Callable, Dict, Optional

import pyvisa

from comm_protocol.src import find_devices
from comm_protocol.src.Shield_Class import Shield_Device

BASE_CONFIG_PATH = Path(__file__).resolve().parent / "base-config.json"


ShieldConfigurator = Callable[[Shield_Device, Dict[str, object]], None]
InstrumentSetup = Callable[[pyvisa.ResourceManager, Dict[str, object]], Dict[str, object]]
MeasurementCallback = Callable[..., object]
PowerSupplySetup = Callable[[object, Dict[str, object]], None]


def local_single_point(
    *,
    source_voltage: float,
    shield_configurator: ShieldConfigurator,
    measurement_callback: MeasurementCallback,
    settle_time: float = 1.0,
    instrument_setup: Optional[InstrumentSetup] = None,
    power_supply_setup: Optional[PowerSupplySetup] = None,
) -> object:
    """Run a single-point measurement scenario.

    Parameters
    ----------
    source_voltage : float
        Voltage to apply on the HV power supply.
    shield_configurator : Callable
        Function that receives ``(shield, config)`` and applies the
        desired SPIN/Shield configuration.
    measurement_callback : Callable
        Function invoked after the hardware has been configured and
        the waveforms have settled. It receives ``config``, ``hv_supply``,
        ``shield`` and any extra instruments returned by ``instrument_setup``.
    settle_time : float, optional
        Delay in seconds before running the measurement callback to allow
        measurements to stabilise. Defaults to 1 second.
    instrument_setup : Callable, optional
        Function returning a dict of additional instrument handles.
    power_supply_setup : Callable, optional
        Function invoked after opening the power supply to adjust limits or modes.

    Returns
    -------
    object
        Whatever ``measurement_callback`` returns.
    """

    config = json.loads(BASE_CONFIG_PATH.read_text())

    rm = pyvisa.ResourceManager()
    hv_supply = None
    shield: Optional[Shield_Device] = None
    extra_instruments: Dict[str, object] = {}

    try:
        hv_address = config["HVpowerSupply"]
        hv_supply = rm.open_resource(hv_address, query_delay=0.5)
        hv_supply.timeout = 5000
        try:
            hv_supply.baud_rate = 9600
        except AttributeError:
            pass

        if power_supply_setup is not None:
            power_supply_setup(hv_supply, config)

        hv_supply.write("VOLT {:.6f}".format(source_voltage))
        time.sleep(0.2)
        hv_supply.write("OUTP 1")
        time.sleep(0.5)

        if instrument_setup is not None:
            extra_instruments = instrument_setup(rm, config)

        shield_vid = config.get("shield_vid", 0x2FE3)
        shield_pid = config.get("shield_pid", 0x0101)
        ports = find_devices.find_shield_device_ports(shield_vid, shield_pid)
        if not ports:
            raise RuntimeError("No Shield device detected. Check USB connections.")
        shield = Shield_Device(shield_port=ports[0], shield_type='TWIST')

        shield_configurator(shield, config)

        time.sleep(settle_time)

        result = measurement_callback(
            config=config,
            hv_supply=hv_supply,
            shield=shield,
            **extra_instruments,
        )
        return result

    finally:
        if shield is not None:
            try:
                shield.sendCommand("POWER_OFF")
            except Exception:
                pass
            try:
                shield.shield_serialObj.close()
            except Exception:
                pass

        for instrument in extra_instruments.values():
            try:
                instrument.close()
            except Exception:
                pass

        if hv_supply is not None:
            try:
                hv_supply.write("OUTP 0")
                hv_supply.write("VOLT 0")
            except Exception:
                pass
            try:
                hv_supply.close()
            except Exception:
                pass

        rm.close()
