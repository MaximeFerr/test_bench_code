#! python3
"""Estimate the winding resistance from single-point SPIN measurements."""

import time
from typing import Dict

from comm_protocol.src.Shield_Class import Shield_Device

from single_point_runner import local_single_point

# Test parameters
FREQUENCY_PWM = 75_000
DEADTIME_NS = 300
PHASE_SHIFT_DEG = 0
SOURCE_VOLTAGE = 0.2
CURRENT_LIMIT = 0.3

CASE_DEFINITIONS: Dict[str, Dict[str, float]] = {
    "leg1_active": {"leg1_duty": 1.0, "leg2_duty": 0.0},
    "leg2_active": {"leg1_duty": 0.0, "leg2_duty": 1.0},
}


def configure_shield(shield: Shield_Device, _config) -> None:
    commands = [
        ("LEG", "LEG1", "ON"),
        ("LEG", "LEG2", "ON"),
        ("POWER_ON", None, None),
        ("FREQUENCY", "LEG1", FREQUENCY_PWM),
        ("DEAD_TIME_RISING", "LEG1", DEADTIME_NS),
        ("DEAD_TIME_RISING", "LEG2", DEADTIME_NS),
        ("DEAD_TIME_FALLING", "LEG1", DEADTIME_NS),
        ("DEAD_TIME_FALLING", "LEG2", DEADTIME_NS),
        ("DUTY", "LEG1", 0.0),
        ("DUTY", "LEG2", 0.0),
        ("PHASE_SHIFT", "LEG2", PHASE_SHIFT_DEG),
    ]
    for cmd, target, value in commands:
        if target is None:
            response = shield.sendCommand(cmd)
        else:
            response = shield.sendCommand(cmd, target, value)
        print(f"Shield → {cmd} {target or ''} {value or ''}: {response}")
        time.sleep(0.1)


def configure_power_supply(hv_supply, _config) -> None:
    hv_supply.write(f"CURR {CURRENT_LIMIT}")
    hv_supply.write("VOLT:MODE FIX")


def setup_dmms(rm, config):
    voltage_dmm = rm.open_resource(config["DMMforVoltage"], query_delay=0.5, timeout=5000)
    current_dmm = rm.open_resource(config["DMMforCurrent"], query_delay=0.5, timeout=5000)

    for instrument, command in ((voltage_dmm, "CONF:VOLT:DC"), (current_dmm, "CONF:CURR:DC")):
        try:
            instrument.write(command)
        except Exception:
            pass

    return {"voltage_dmm": voltage_dmm, "current_dmm": current_dmm}


def measure_resistance(*, shield, voltage_dmm, current_dmm, **_):
    results = {}
    for name, duties in CASE_DEFINITIONS.items():
        shield.sendCommand("DUTY", "LEG1", duties["leg1_duty"])
        shield.sendCommand("DUTY", "LEG2", duties["leg2_duty"])
        # Trigger phase alignment even with static duty cycles
        shield.sendCommand("PHASE_SHIFT", "LEG2", PHASE_SHIFT_DEG)
        shield.sendCommand("PHASE_SHIFT", "LEG1", PHASE_SHIFT_DEG)
        time.sleep(0.5)

        try:
            voltage = float(voltage_dmm.query("MEAS:VOLT:DC?").strip())
        except Exception as exc:  # pragma: no cover - hardware dependent
            raise RuntimeError("Voltage DMM measurement failed") from exc

        try:
            current = float(current_dmm.query("MEAS:CURR:DC?").strip())
        except Exception as exc:  # pragma: no cover - hardware dependent
            raise RuntimeError("Current DMM measurement failed") from exc

        resistance = float("inf") if abs(current) < 1e-6 else voltage / current
        results[name] = {
            "voltage": voltage,
            "current": current,
            "resistance": resistance,
        }

        print(
            f"Case {name}: V={voltage:.6f} V, I={current:.6f} A, R={resistance:.6f} Ω"
        )

    shield.sendCommand("DUTY", "LEG1", 0.0)
    shield.sendCommand("DUTY", "LEG2", 0.0)

    return results


def estimate_resistance():
    return local_single_point(
        source_voltage=SOURCE_VOLTAGE,
        shield_configurator=configure_shield,
        measurement_callback=measure_resistance,
        instrument_setup=setup_dmms,
        power_supply_setup=configure_power_supply,
        settle_time=0.5,
    )


if __name__ == "__main__":
    estimate_resistance()
