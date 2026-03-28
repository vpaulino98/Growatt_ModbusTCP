"""
SPE Series Profiles - Single-Phase Hybrid Solar Inverters (8-12kW)

The SPE 8000-12000 ES is a single-phase hybrid inverter with battery storage,
dual MPPT trackers, and grid-tied peak shaving capability. It supports parallel
operation for capacity expansion up to 108kW.

Uses the same off-grid protocol as SPF (registers 0-97) for sensor data.
Identified via Issue #212 register scan analysis — nighttime data perfectly
matches SPF register layout across 15+ registers including battery voltage
(53.67V at ×0.01), SOC (97%), AC voltages (230.8V, 231.0V), frequencies
(49.99Hz, 50.02Hz), temperatures, and a fully consistent power balance.

Key characteristics:
- 8-12kW capacity, single-phase hybrid
- Dual MPPT trackers (PV1 + PV2), max PV input 550VDC
- Two AC input terminals with integrated transfer switch
- Grid-tied with peak shaving capability
- Parallel operation support (up to 108kW)
- Dual outputs for smart load management

Battery Power Sign Convention:
Same as SPF — uses INVERTED sign convention (positive=discharge, negative=charge).
Negative scale (-0.1) on registers 77-78 converts to standard convention.
"""

from .spf import SPF_3000_6000_ES_PLUS

SPE_8000_12000_ES = {
    'name': 'SPE 8000-12000 ES',
    'description': 'Single-phase hybrid inverter with battery storage (8-12kW)',
    'notes': 'Uses SPF off-grid protocol (0-97 range). Identified from Issue #212 scan. Needs daytime validation.',
    # NOTE: offgrid_protocol refers to the REGISTER LAYOUT (SPF-style 0-97),
    # not the inverter's grid capability. The SPE supports grid-tied operation
    # with peak shaving. This flag prevents reading VPP registers (30000+)
    # which return garbage data on this device.
    'offgrid_protocol': True,
    'input_registers': {
        **SPF_3000_6000_ES_PLUS['input_registers'],
        # SPE-specific overrides or additions can go here
        # once daytime scan confirms additional registers
    },
    'holding_registers': {
        **SPF_3000_6000_ES_PLUS['holding_registers'],
        # SPE may have different control register layout
        # Holding registers need validation with user
    }
}

# Export register maps for import by __init__.py
SPE_REGISTER_MAPS = {
    'SPE_8000_12000_ES': SPE_8000_12000_ES,
}
