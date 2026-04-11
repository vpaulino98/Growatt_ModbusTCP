# SPA Series - AC-Coupled Battery Storage (No PV MPPT Inputs)
# Based on SPA 3000TL BL + Ark 2.5L-A1 register scans (issue #249)
# Scan date: 2026-04 (day + night scans cross-verified)

from .sph_tl3 import SPH_TL3_3000_10000

SPA_3000_6000_TL_BL = {
    'name': 'SPA (AC Storage) 3-6kW',
    'description': 'AC-coupled battery storage inverter — no PV MPPT inputs (SPA 3000TL BL and similar)',
    'notes': (
        'Uses ONLY 1000-1124 register range. No solar DC inputs. '
        'Base range (0-124) and 3000+ range respond with zeros — not exceptions. '
        'Holding registers identical to SPH-TL3. '
        'Load power is at reg 1037/1038 (SPH-TL3 reg 1021/1022 is zero on SPA).'
    ),
    'input_registers': {
        # ============================================================================
        # STORAGE RANGE 1000-1124 (the ONLY range with real data on SPA)
        # ============================================================================

        # System Work Mode
        1000: {'name': 'system_work_mode', 'scale': 1, 'unit': '', 'desc': 'Work mode'},

        # Battery Discharge/Charge Power
        1009: {'name': 'discharge_power_high', 'scale': 1, 'unit': '', 'pair': 1010},
        1010: {'name': 'discharge_power_low', 'scale': 1, 'unit': '', 'pair': 1009,
               'combined_scale': 0.1, 'combined_unit': 'W'},
        1011: {'name': 'charge_power_high', 'scale': 1, 'unit': '', 'pair': 1012},
        1012: {'name': 'charge_power_low', 'scale': 1, 'unit': '', 'pair': 1011,
               'combined_scale': 0.1, 'combined_unit': 'W'},

        # Battery State
        1013: {'name': 'battery_voltage', 'scale': 0.1, 'unit': 'V'},
        1014: {'name': 'battery_soc', 'scale': 1, 'unit': '%'},
        1040: {'name': 'battery_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},
        1041: {'name': 'battery_type', 'scale': 1, 'unit': ''},

        # Power Flow
        # NOTE: SPH-TL3 maps power_to_load at 1021/1022 — those registers are zero on SPA.
        #       Load power on SPA is at 1037/1038 (mapped here as power_to_load).
        1029: {'name': 'power_to_grid_high', 'scale': 1, 'unit': '', 'pair': 1030},
        1030: {'name': 'power_to_grid_low', 'scale': 1, 'unit': '', 'pair': 1029,
               'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},
        1037: {'name': 'power_to_load_high', 'scale': 1, 'unit': '', 'pair': 1038},
        1038: {'name': 'power_to_load_low', 'scale': 1, 'unit': '', 'pair': 1037,
               'combined_scale': 0.1, 'combined_unit': 'W'},

        # AC Grid Voltage
        # Reg 1105 (input FC04) = ~21575 raw → ×0.01 = 215.75V on UK 230V grid.
        # Constant between day/night scans — consistent with mains voltage.
        # NOTE: Tentative — user confirmation pending. Not to be confused with
        #       holding reg 1105 (FC03) = time_period_2_enable, a separate register space.
        1105: {'name': 'ac_voltage', 'scale': 0.01, 'unit': 'V',
               'desc': 'Grid/AC voltage (SPA input reg 1105, scale ×0.01; confirmed ~216V on 230V grid)'},

        # Energy Breakdown (all registers confirmed from day + night cross-scan analysis)
        1044: {'name': 'energy_to_user_today_high', 'scale': 1, 'unit': '', 'pair': 1045},
        1045: {'name': 'energy_to_user_today_low', 'scale': 1, 'unit': '', 'pair': 1044,
               'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1046: {'name': 'energy_to_user_total_high', 'scale': 1, 'unit': '', 'pair': 1047},
        1047: {'name': 'energy_to_user_total_low', 'scale': 1, 'unit': '', 'pair': 1046,
               'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1048: {'name': 'energy_to_grid_today_high', 'scale': 1, 'unit': '', 'pair': 1049},
        1049: {'name': 'energy_to_grid_today_low', 'scale': 1, 'unit': '', 'pair': 1048,
               'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1050: {'name': 'energy_to_grid_total_high', 'scale': 1, 'unit': '', 'pair': 1051},
        1051: {'name': 'energy_to_grid_total_low', 'scale': 1, 'unit': '', 'pair': 1050,
               'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1052: {'name': 'discharge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 1053},
        1053: {'name': 'discharge_energy_today_low', 'scale': 1, 'unit': '', 'pair': 1052,
               'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1054: {'name': 'discharge_energy_total_high', 'scale': 1, 'unit': '', 'pair': 1055},
        1055: {'name': 'discharge_energy_total_low', 'scale': 1, 'unit': '', 'pair': 1054,
               'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1056: {'name': 'charge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 1057},
        1057: {'name': 'charge_energy_today_low', 'scale': 1, 'unit': '', 'pair': 1056,
               'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1058: {'name': 'charge_energy_total_high', 'scale': 1, 'unit': '', 'pair': 1059},
        1059: {'name': 'charge_energy_total_low', 'scale': 1, 'unit': '', 'pair': 1058,
               'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1060: {'name': 'load_energy_today_high', 'scale': 1, 'unit': '', 'pair': 1061},
        1061: {'name': 'load_energy_today_low', 'scale': 1, 'unit': '', 'pair': 1060,
               'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1062: {'name': 'load_energy_total_high', 'scale': 1, 'unit': '', 'pair': 1063},
        1063: {'name': 'load_energy_total_low', 'scale': 1, 'unit': '', 'pair': 1062,
               'combined_scale': 0.1, 'combined_unit': 'kWh'},
    },
    'holding_registers': {
        # Confirmed identical to SPH-TL3 from entity values in scan:
        # priority_mode, discharge_stopped_soc, charge_power_rate, time_period_1/2/3
        **SPH_TL3_3000_10000['holding_registers'],
    },
}

# Export all SPA profiles
SPA_REGISTER_MAPS = {
    'SPA_3000_6000_TL_BL': SPA_3000_6000_TL_BL,
}
