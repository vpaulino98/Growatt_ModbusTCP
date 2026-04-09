# MID-15000-25000TL3-X (Three-phase, 15-25kW)
MID_15000_25000TL3_X = {
    'name': 'MID-TL3-X Series',
    'description': 'Three-phase commercial inverter (15-25kW)',
    'notes': 'Uses 0-124, 125-249 register range. Three-phase output.',
    'input_registers': {
        # System Status
        0: {'name': 'inverter_status', 'scale': 1, 'unit': '', 'desc': '0=Waiting, 1=Normal, 3=Fault'},
        
        # PV Totals
        1: {'name': 'pv_total_power_high', 'scale': 1, 'unit': '', 'pair': 2},
        2: {'name': 'pv_total_power_low', 'scale': 1, 'unit': '', 'pair': 1, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # PV String 1
        3: {'name': 'pv1_voltage', 'scale': 0.1, 'unit': 'V'},
        4: {'name': 'pv1_current', 'scale': 0.1, 'unit': 'A'},
        5: {'name': 'pv1_power_high', 'scale': 1, 'unit': '', 'pair': 6},
        6: {'name': 'pv1_power_low', 'scale': 1, 'unit': '', 'pair': 5, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # PV String 2
        7: {'name': 'pv2_voltage', 'scale': 0.1, 'unit': 'V'},
        8: {'name': 'pv2_current', 'scale': 0.1, 'unit': 'A'},
        9: {'name': 'pv2_power_high', 'scale': 1, 'unit': '', 'pair': 10},
        10: {'name': 'pv2_power_low', 'scale': 1, 'unit': '', 'pair': 9, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # Output Power
        35: {'name': 'output_power_high', 'scale': 1, 'unit': '', 'pair': 36},
        36: {'name': 'output_power_low', 'scale': 1, 'unit': '', 'pair': 35, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # Grid Frequency
        37: {'name': 'grid_frequency', 'scale': 0.01, 'unit': 'Hz'},
        
        # Phase R (L1)
        38: {'name': 'grid_voltage_r', 'scale': 0.1, 'unit': 'V', 'desc': 'Phase R voltage'},
        39: {'name': 'grid_current_r', 'scale': 0.1, 'unit': 'A', 'desc': 'Phase R current'},
        40: {'name': 'grid_power_r_high', 'scale': 1, 'unit': '', 'pair': 41},
        41: {'name': 'grid_power_r_low', 'scale': 1, 'unit': '', 'pair': 40, 'combined_scale': 0.1, 'combined_unit': 'VA'},
        
        # Phase S (L2)
        42: {'name': 'grid_voltage_s', 'scale': 0.1, 'unit': 'V', 'desc': 'Phase S voltage'},
        43: {'name': 'grid_current_s', 'scale': 0.1, 'unit': 'A', 'desc': 'Phase S current'},
        44: {'name': 'grid_power_s_high', 'scale': 1, 'unit': '', 'pair': 45},
        45: {'name': 'grid_power_s_low', 'scale': 1, 'unit': '', 'pair': 44, 'combined_scale': 0.1, 'combined_unit': 'VA'},
        
        # Phase T (L3)
        46: {'name': 'grid_voltage_t', 'scale': 0.1, 'unit': 'V', 'desc': 'Phase T voltage'},
        47: {'name': 'grid_current_t', 'scale': 0.1, 'unit': 'A', 'desc': 'Phase T current'},
        48: {'name': 'grid_power_t_high', 'scale': 1, 'unit': '', 'pair': 49},
        49: {'name': 'grid_power_t_low', 'scale': 1, 'unit': '', 'pair': 48, 'combined_scale': 0.1, 'combined_unit': 'VA'},
        
        # Line voltages
        50: {'name': 'grid_voltage_rs', 'scale': 0.1, 'unit': 'V', 'desc': 'Line voltage R-S'},
        51: {'name': 'grid_voltage_st', 'scale': 0.1, 'unit': 'V', 'desc': 'Line voltage S-T'},
        52: {'name': 'grid_voltage_tr', 'scale': 0.1, 'unit': 'V', 'desc': 'Line voltage T-R'},
        
        # Energy
        53: {'name': 'energy_today_high', 'scale': 1, 'unit': '', 'pair': 54},
        54: {'name': 'energy_today_low', 'scale': 1, 'unit': '', 'pair': 53, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        55: {'name': 'energy_total_high', 'scale': 1, 'unit': '', 'pair': 56},
        56: {'name': 'energy_total_low', 'scale': 1, 'unit': '', 'pair': 55, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Power flow — confirmed responding in issue #240 scan
        3041: {'name': 'power_to_user_high', 'scale': 1, 'unit': '', 'pair': 3042, 'desc': 'Grid import power (HIGH word)'},
        3042: {'name': 'power_to_user_low', 'scale': 1, 'unit': '', 'pair': 3041, 'combined_scale': 0.1, 'combined_unit': 'W', 'desc': 'Grid import power (LOW word)'},
        3043: {'name': 'power_to_grid_high', 'scale': 1, 'unit': '', 'pair': 3044, 'desc': 'Grid export power (HIGH word)'},
        3044: {'name': 'power_to_grid_low', 'scale': 1, 'unit': '', 'pair': 3043, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True, 'desc': 'Grid export power (LOW word, signed)'},
        3045: {'name': 'power_to_load_high', 'scale': 1, 'unit': '', 'pair': 3046, 'desc': 'Load power (HIGH word)'},
        3046: {'name': 'power_to_load_low', 'scale': 1, 'unit': '', 'pair': 3045, 'combined_scale': 0.1, 'combined_unit': 'W', 'desc': 'Load power (LOW word)'},

        # Grid energy counters — confirmed responding in issue #240 scan
        3067: {'name': 'energy_to_user_today_high', 'scale': 1, 'unit': '', 'pair': 3068, 'desc': 'Grid import energy today (HIGH word)'},
        3068: {'name': 'energy_to_user_today_low', 'scale': 1, 'unit': '', 'pair': 3067, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Grid import energy today (LOW word)'},
        3069: {'name': 'energy_to_user_total_high', 'scale': 1, 'unit': '', 'pair': 3070, 'desc': 'Grid import energy total (HIGH word)'},
        3070: {'name': 'energy_to_user_total_low', 'scale': 1, 'unit': '', 'pair': 3069, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Grid import energy total (LOW word)'},
        3071: {'name': 'energy_to_grid_today_high', 'scale': 1, 'unit': '', 'pair': 3072, 'desc': 'Grid export energy today (HIGH word)'},
        3072: {'name': 'energy_to_grid_today_low', 'scale': 1, 'unit': '', 'pair': 3071, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Grid export energy today (LOW word)'},
        3073: {'name': 'energy_to_grid_total_high', 'scale': 1, 'unit': '', 'pair': 3074, 'desc': 'Grid export energy total (HIGH word)'},
        3074: {'name': 'energy_to_grid_total_low', 'scale': 1, 'unit': '', 'pair': 3073, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Grid export energy total (LOW word)'},
        3075: {'name': 'load_energy_today_high', 'scale': 1, 'unit': '', 'pair': 3076, 'desc': 'Load energy today (HIGH word)'},
        3076: {'name': 'load_energy_today_low', 'scale': 1, 'unit': '', 'pair': 3075, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Load energy today (LOW word)'},
        3077: {'name': 'load_energy_total_high', 'scale': 1, 'unit': '', 'pair': 3078, 'desc': 'Load energy total (HIGH word)'},
        3078: {'name': 'load_energy_total_low', 'scale': 1, 'unit': '', 'pair': 3077, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Load energy total (LOW word)'},

        # Temperatures
        93: {'name': 'inverter_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},
        94: {'name': 'ipm_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},
        95: {'name': 'boost_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},

        # Status
        100: {'name': 'power_factor', 'scale': 1, 'unit': ''},
        104: {'name': 'derating_mode', 'scale': 1, 'unit': ''},
        105: {'name': 'fault_code', 'scale': 1, 'unit': ''},
        112: {'name': 'warning_code', 'scale': 1, 'unit': ''},
    },
    'holding_registers': {
        0: {'name': 'on_off', 'scale': 1, 'unit': '', 'access': 'RW'},
        3: {'name': 'active_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW'},
        30: {'name': 'modbus_address', 'scale': 1, 'unit': '', 'access': 'RW'},
    }
}

# MID-15000-25000TL3-X V2.01 Protocol (legacy + VPP 2.01 registers)
MID_15000_25000TL3_X_V201 = {
    'name': 'MID-TL3-X Series (V2.01)',
    'description': 'Three-phase commercial inverter (15-25kW) with VPP Protocol V2.01',
    'notes': 'Combines legacy (0-124 range) with V2.01 (30000+ range). Overlapping values served at both addresses.',
    'input_registers': {
        # === Legacy REGISTERS (0-124 range) ===
        **MID_15000_25000TL3_X['input_registers'],

        # === V2.01 REGISTERS (31000+ range) ===
        # Status
        31000: {'name': 'equipment_status', 'scale': 1, 'unit': '', 'desc': 'Equipment running status'},
        31001: {'name': 'system_fault_word0', 'scale': 1, 'unit': '', 'desc': 'System fault word 0'},
        31002: {'name': 'system_fault_word1', 'scale': 1, 'unit': '', 'desc': 'System fault word 1'},
        31003: {'name': 'system_fault_word2', 'scale': 1, 'unit': '', 'desc': 'System fault word 2'},
        31004: {'name': 'grid_first_connected', 'scale': 1, 'unit': '', 'desc': 'Grid first connected status'},

        # PV Data
        31010: {'name': 'pv1_voltage_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'pv1_voltage'},
        31011: {'name': 'pv1_current_vpp', 'scale': 0.1, 'unit': 'A', 'maps_to': 'pv1_current'},
        31012: {'name': 'pv1_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31013, 'maps_to': 'pv1_power'},
        31013: {'name': 'pv1_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31012, 'combined_scale': 0.1, 'combined_unit': 'W'},
        31014: {'name': 'pv2_voltage_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'pv2_voltage'},
        31015: {'name': 'pv2_current_vpp', 'scale': 0.1, 'unit': 'A', 'maps_to': 'pv2_current'},
        31016: {'name': 'pv2_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31017, 'maps_to': 'pv2_power'},
        31017: {'name': 'pv2_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31016, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Total PV Power
        31018: {'name': 'pv_total_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31019, 'maps_to': 'pv_total_power'},
        31019: {'name': 'pv_total_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31018, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Three-Phase AC Output
        31100: {'name': 'ac_voltage_r_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'grid_voltage_r'},
        31101: {'name': 'ac_voltage_s_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'grid_voltage_s'},
        31102: {'name': 'ac_voltage_t_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'grid_voltage_t'},
        31103: {'name': 'ac_frequency_vpp', 'scale': 0.01, 'unit': 'Hz', 'maps_to': 'grid_frequency'},

        # Grid/Meter Power — signed (positive=export, negative=import)
        # maps_to triggers fallback for power_to_grid when 3044=0 (same pattern as MOD)
        31112: {'name': 'meter_power_high', 'scale': 1, 'unit': '', 'pair': 31113, 'desc': 'Meter power HIGH'},
        31113: {'name': 'meter_power_low', 'scale': 1, 'unit': '', 'pair': 31112, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True, 'maps_to': 'power_to_grid_low', 'desc': 'Meter power LOW — fallback for power_to_grid when 3044=0'},

        # Load Power — confirmed responding in issue #240 scan (31119=94 → 9.4W)
        31118: {'name': 'load_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31119, 'maps_to': 'power_to_load', 'desc': 'Load power HIGH (VPP)'},
        31119: {'name': 'load_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31118, 'combined_scale': 0.1, 'combined_unit': 'W', 'desc': 'Load power LOW (VPP)'},

        # Energy Data
        31120: {'name': 'energy_today_high_vpp', 'scale': 1, 'unit': '', 'pair': 31121, 'maps_to': 'energy_today'},
        31121: {'name': 'energy_today_low_vpp', 'scale': 1, 'unit': '', 'pair': 31120, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31122: {'name': 'energy_total_high_vpp', 'scale': 1, 'unit': '', 'pair': 31123, 'maps_to': 'energy_total'},
        31123: {'name': 'energy_total_low_vpp', 'scale': 1, 'unit': '', 'pair': 31122, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Temperatures
        31130: {'name': 'inverter_temp_vpp', 'scale': 0.1, 'unit': '°C', 'maps_to': 'inverter_temp', 'signed': True},
        31131: {'name': 'ipm_temp_vpp', 'scale': 0.1, 'unit': '°C', 'maps_to': 'ipm_temp', 'signed': True},
        31132: {'name': 'boost_temp_vpp', 'scale': 0.1, 'unit': '°C', 'maps_to': 'boost_temp', 'signed': True},

        # === BATTERY (VPP 31200+ range) — confirmed responding in issue #240 scan ===
        # Named without _vpp suffix so coordinator's fallback lookup finds them directly
        # (no competing 3000-range battery registers on MID)
        31200: {'name': 'battery_power_high', 'scale': 1, 'unit': '', 'pair': 31201, 'desc': 'Battery power HIGH'},
        31201: {'name': 'battery_power_low', 'scale': 1, 'unit': '', 'pair': 31200, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True, 'desc': 'Battery power (signed, positive=charging)'},

        # Battery charge/discharge energy (VPP)
        31202: {'name': 'charge_energy_today_vpp_high', 'scale': 1, 'unit': '', 'pair': 31203},
        31203: {'name': 'charge_energy_today_vpp_low', 'scale': 1, 'unit': '', 'pair': 31202, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31204: {'name': 'charge_energy_total_vpp_high', 'scale': 1, 'unit': '', 'pair': 31205},
        31205: {'name': 'charge_energy_total_vpp_low', 'scale': 1, 'unit': '', 'pair': 31204, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31206: {'name': 'discharge_energy_today_vpp_high', 'scale': 1, 'unit': '', 'pair': 31207},
        31207: {'name': 'discharge_energy_today_vpp_low', 'scale': 1, 'unit': '', 'pair': 31206, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31208: {'name': 'discharge_energy_total_vpp_high', 'scale': 1, 'unit': '', 'pair': 31209},
        31209: {'name': 'discharge_energy_total_vpp_low', 'scale': 1, 'unit': '', 'pair': 31208, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Battery state — confirmed responding in issue #240 scan
        # 31214=4048 → 404.8V, 31215/31216=0/148 → 14.8A, 31217=33 → 33% SOC
        31214: {'name': 'battery_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'Battery voltage (VPP)'},
        31215: {'name': 'battery_current_vpp_high', 'scale': 1, 'unit': '', 'pair': 31216},
        31216: {'name': 'battery_current_vpp_low', 'scale': 1, 'unit': '', 'pair': 31215, 'combined_scale': 0.1, 'combined_unit': 'A', 'signed': True, 'maps_to': 'battery_current'},
        31217: {'name': 'battery_soc', 'scale': 1, 'unit': '%', 'desc': 'Battery SOC (VPP)'},
        31218: {'name': 'battery_soh', 'scale': 1, 'unit': '%', 'desc': 'Battery state of health'},
        # 31222/31223=0/415 → 41.5°C battery temp
        31222: {'name': 'battery_temp_vpp_high', 'scale': 1, 'unit': '', 'pair': 31223},
        31223: {'name': 'battery_temp', 'scale': 0.1, 'unit': '°C', 'signed': True, 'desc': 'Battery temperature (VPP)'},
    },
    'holding_registers': {
        # === Legacy REGISTERS ===
        **MID_15000_25000TL3_X['holding_registers'],

        # === V2.01 REGISTERS (30000+ range) ===
        30000: {'name': 'dtc_code', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'Device Type Code: 3000 for MID', 'default': 5400},
        30099: {'name': 'protocol_version', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'VPP Protocol version (201 = V2.01)', 'default': 201},
        30100: {'name': 'control_authority', 'scale': 1, 'unit': '', 'access': 'RW'},
        30101: {'name': 'remote_onoff', 'scale': 1, 'unit': '', 'access': 'RW', 'maps_to': 'on_off'},
        30104: {'name': 'sys_year_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30105: {'name': 'sys_month_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30106: {'name': 'sys_day_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30107: {'name': 'sys_hour_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30108: {'name': 'sys_minute_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30109: {'name': 'sys_second_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30112: {'name': 'modbus_address_vpp', 'scale': 1, 'unit': '', 'access': 'RW', 'maps_to': 'modbus_address'},
        30114: {'name': 'active_power_rate_vpp', 'scale': 0.1, 'unit': '%', 'access': 'RW', 'maps_to': 'active_power_rate'},
        30200: {'name': 'export_limit_enable', 'scale': 1, 'unit': '', 'access': 'RW'},
        30201: {'name': 'export_limit_power_rate', 'scale': 0.1, 'unit': '%', 'access': 'RW'},
    }
}

# Export all MID profiles
MID_REGISTER_MAPS = {
    'MID_15000_25000TL3_X': MID_15000_25000TL3_X,
    'MID_15000_25000TL3_X_V201': MID_15000_25000TL3_X_V201,
}
