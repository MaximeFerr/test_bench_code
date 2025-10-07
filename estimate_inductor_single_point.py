#! python3
"""Estimate the initial inductance value from a single-point SPIN configuration."""

import time

import lib.Oscillo_v1b as osc_utils
from comm_protocol.src.Shield_Class import Shield_Device

from single_point_runner import local_single_point

# Default measurement parameters
DUTY_PWM = 0.485
FREQUENCY_PWM = 75_000
DEADTIME_NS = 300
INITIAL_PHASE_SHIFT = 135
DELTA_DUTY_INIT = 0.0
SOURCE_VOLTAGE = 10.0


def configure_shield(shield: Shield_Device, _config) -> None:
    """Apply the single-point PWM configuration to the SPIN board."""
    commands = [
        ("LEG", "LEG1", "ON"),
        ("LEG", "LEG2", "ON"),
        ("POWER_ON", None, None),
        ("DUTY", "LEG1", DUTY_PWM),
        ("DUTY", "LEG2", DUTY_PWM + DELTA_DUTY_INIT),
        ("FREQUENCY", "LEG1", FREQUENCY_PWM),
        ("DEAD_TIME_RISING", "LEG1", DEADTIME_NS),
        ("DEAD_TIME_RISING", "LEG2", DEADTIME_NS),
        ("DEAD_TIME_FALLING", "LEG1", DEADTIME_NS),
        ("DEAD_TIME_FALLING", "LEG2", DEADTIME_NS),
        ("PHASE_SHIFT", "LEG2", INITIAL_PHASE_SHIFT),
    ]

    for cmd, target, value in commands:
        if target is None:
            response = shield.sendCommand(cmd)
        else:
            response = shield.sendCommand(cmd, target, value)
        print(f"Shield → {cmd} {target or ''} {value or ''}: {response}")
        time.sleep(0.1)


def configure_power_supply(hv_supply, _config) -> None:
    """Apply a conservative current limit before enabling the output."""
    hv_supply.write("CURR 0.3")
    hv_supply.write("VOLT:MODE FIX")


def configure_oscilloscope(scope) -> None:
    """Prepare the oscilloscope to report Pslope on channel C2."""
    osc_utils.ConfigTrigger(scope)
    osc_utils.ConfigMeasure(scope)
    osc_utils.NewMeasure(scope, 1, {"type": "PSLOPE", "channel": 2})


def read_pslope(scope, retries: int = 5, delay: float = 0.5) -> float:
    """Poll the oscilloscope for the Pslope measurement, retrying if needed."""
    for _ in range(retries):
        value = osc_utils.GetMeasure(scope, 1)
        if value is not None:
            return float(value)
        print("Waiting for oscilloscope Pslope measurement...")
        time.sleep(delay)
    raise RuntimeError("Oscilloscope did not provide a valid Pslope measurement.")


def setup_scope(rm, config):
    scope = rm.open_resource(config["AddressOSCILLO"], query_delay=0.5, timeout=6000)
    configure_oscilloscope(scope)
    return {"scope": scope}


def measure_inductance(*, scope, **_):
    pslope = read_pslope(scope)
    estimated_L = SOURCE_VOLTAGE / pslope
    print(f"Measured Pslope: {pslope:.6f} (A/s)")
    print(f"Estimated inductance: {estimated_L:.6f} H")
    return estimated_L


def estimate_inductance() -> float:
    return local_single_point(
        source_voltage=SOURCE_VOLTAGE,
        shield_configurator=configure_shield,
        measurement_callback=measure_inductance,
        instrument_setup=setup_scope,
        power_supply_setup=configure_power_supply,
        settle_time=1.0,
    )


if __name__ == "__main__":
    estimate_inductance()
