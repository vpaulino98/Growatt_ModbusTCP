# Release Notes

<a href="https://www.buymeacoffee.com/0xAHA" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

---

## v0.6.8b1

> **Beta release** — MOD GEN4 TOU reversion fix + extended schedule support for MOD and SPH.
> Field-test recommended before deploying to production. See verification steps below.

### Changes at a Glance

- **MOD GEN4 — TOU reversion root cause fixed:** Register 3049 ("Allow Grid Charge") was
  missing from the integration. On GEN4 hardware this register is a prerequisite gate —
  without it enabled, the firmware silently discards TOU writes after each cloud sync
  cycle. A new **"Allow Grid Charge"** select entity is now exposed under the Battery device.
- **MOD GEN4 — TOU slots 5–9 added:** GEN4 hardware supports 9 time slots
  (registers 3038–3059, with a gap at 3046–3049 for EMS controls). Only slots 1–4 were
  previously implemented. Slots 5–9 (registers 3050–3059) are now fully supported.
- **MOD GEN4 — Atomic FC16 writes for TOU:** Start and end registers for each TOU slot
  are now written together in a single Modbus FC16 transaction, eliminating the window
  where the inverter could see a partially-updated schedule.
- **SPH GEN3 — Extended time periods:** Battery First extended slots 4–6 (registers
  1017–1025) and Grid First extended slots 4–9 (registers 1026–1034 and 1080–1088) are
  now exposed as time picker and enable select entities.
- **New control guide:** `docs/CONTROLS.md` replaces the WIT-only `WIT_CONTROL_GUIDE.md`
  with comprehensive per-model instructions, SVG diagrams, and automation examples for
  MOD, SPH, WIT, and SPF.

---

### MOD GEN4 — How to Use the New TOU Control

> **Read this before configuring TOU on a MOD GEN4 inverter.**

#### Why TOU was reverting

Growatt's GEN4 firmware implements a software gate on all TOU register writes.
Register 3049 ("Allow Grid Charge") must be set to `1 (Enabled)` before the inverter
will accept and persist TOU schedule changes. When it is `0 (Disabled)`, the firmware
accepts the Modbus write without error but reapplies its own defaults on the next
firmware tick — typically within 30–90 seconds.

This gate is documented in the `wills106/homeassistant-solax-modbus` Growatt plugin,
which successfully manages TOU on the same hardware. Our integration previously had no
awareness of this register.

#### Step 1 — Enable Allow Grid Charge (one-time)

In Home Assistant, open the **Battery** device for your inverter and locate the new
**"Allow Grid Charge"** select entity. Set it to **Enabled**.

To verify the write was accepted, check the entity state after the next poll cycle
(~30 seconds). It should remain "Enabled".

You can also verify using the diagnostic service:

```yaml
service: growatt_modbus.read_register
data:
  register_type: holding
  register_address: 3049
  count: 1
target:
  device_id: YOUR_DEVICE_ID
```

The response should be `1`. If it immediately reverts to `0`, the ShineWiFi dongle cloud
sync may be resetting it — disable cloud sync in the dongle's web UI if your firmware
supports it.

#### Step 2 — Configure TOU Periods (9 slots)

All 9 TOU slots are now available. For each slot you want active:

1. Set **TOU Period N Start** (time picker entity)
2. Set **TOU Period N End** (time picker entity)
3. Set **TOU Period N Priority** → `Load Priority`, `Battery Priority`, or `Grid Priority`
4. Set **TOU Period N Enable** → `Enabled`

Slots 1–4 use registers 3038–3045 (same as before). Slots 5–9 use registers 3050–3059
(new). Leave unused slots Disabled.

> **Note on the register gap:** Registers 3046–3049 are EMS controls, not TOU slots.
> The jump from slot 4 (ends at 3045) to slot 5 (starts at 3050) is intentional.

#### Step 3 — Verify persistence

After setting a TOU period, wait 60–90 seconds and re-read the start register to confirm
the value held. Use debug logging to confirm:

```yaml
logger:
  logs:
    custom_components.growatt_modbus: debug
```

Look for `[MOD TOU] periods 1-4 start: ...` log lines — if the values match what you
wrote, TOU is working. If they revert, re-check Step 1 (register 3049).

#### Slots 5–9 register verification

Before relying on slots 5–9, confirm your inverter hardware responds to those registers:

```yaml
service: growatt_modbus.read_register
data:
  register_type: holding
  register_address: 3050
  count: 10
target:
  device_id: YOUR_DEVICE_ID
```

If the inverter returns data (not a Modbus exception), slots 5–9 are supported.

#### Atomic writes — what changed internally

Previous versions wrote TOU start and end registers independently (two separate FC06
writes). This created a brief window where the inverter held a valid start time but a
stale end time, which could cause TOU reversion on sensitive firmware builds.

Version 0.6.8b1 writes both registers together using a single Modbus FC16
(write multiple registers) transaction — the same method used by the Solax Modbus
integration and by our own WIT VPP control path. There is no change to entity behaviour
or the HA UI — the improvement is internal.

---

### SPH GEN3 — Extended Time Periods

SPH GEN3 inverters support up to 9 Battery First time windows and 9 Grid First time
windows in hardware. Previously only 3 AC charge periods (registers 1100–1108) were
exposed.

**New entities (all under the Battery device):**

| Entity group | Registers | Slots |
|---|---|---|
| Battery First time periods | 1017–1025 | Slots 4–6 |
| Grid First time periods | 1026–1034 | Slots 4–6 |
| Grid First time periods | 1080–1088 | Slots 7–9 |

Each slot provides:
- A **start time** picker entity
- An **end time** picker entity
- An **enable** select entity (`Disabled` / `Enabled`)

**How to use:**

Set the global **Priority Mode** (register 1044) to `Battery First` or `Grid First` to
select which set of time slots is active. Then configure individual windows using the
time picker entities for the relevant slot group.

> **Hardware validation note:** These registers are documented in the Growatt protocol
> specification and confirmed present in the Solax Modbus Growatt plugin for
> `HYBRID | GEN3` models. If your specific SPH model does not respond to these registers
> (i.e., the entities appear but always read 0 and writes are not accepted), please open
> an issue with your register scanner CSV.

> **SPH HU note:** SPH 8000–10000 TL-HU uses a different register architecture where
> battery management holding registers (1044, 1070–1108) return Modbus exceptions.
> The extended time period registers (1017–1088) have not been validated on HU hardware.
> HU users should leave these entities unconfigured until hardware confirmation is available.

---

### New and Updated Entities

**MOD GEN4 (TL3-XH profile only):**

| Entity | Type | Register | New? |
|--------|------|----------|------|
| Allow Grid Charge | Select | 3049 | New |
| TOU Period 5 Start / End | Time | 3050, 3051 | New |
| TOU Period 5 Priority | Select | 3050 (bits) | New |
| TOU Period 5 Enable | Select | 3050 (bit 15) | New |
| TOU Period 6–9 (×4) | Time + Select ×2 | 3052–3059 | New |

**SPH GEN3 (3000–10000 TL profiles):**

| Entity group | Type | Registers | New? |
|---|---|---|---|
| Batt First Period 4–6 Start/End | Time (×6) | 1017–1025 | New |
| Batt First Period 4–6 Enable | Select (×3) | 1019, 1022, 1025 | New |
| Grid First Period 4–6 Start/End | Time (×6) | 1026–1034 | New |
| Grid First Period 4–6 Enable | Select (×3) | 1028, 1031, 1034 | New |
| Grid First Period 7–9 Start/End | Time (×6) | 1080–1088 | New |
| Grid First Period 7–9 Enable | Select (×3) | 1082, 1085, 1088 | New |

---

### Files Changed

| File | Change |
|------|--------|
| `profiles/mod.py` | Added registers 3049 and 3050–3059 to MOD_6000_15000TL3_XH holding_registers |
| `profiles/sph.py` | Added registers 1017–1034 and 1080–1088 to SPH_3000_6000 and SPH_7000_10000 |
| `const.py` | Extended MOD_TOU_PERIODS to 9 entries; added allow_grid_charge and SPH extended periods to WRITABLE_REGISTERS |
| `growatt_modbus.py` | Added GrowattData fields and coordinator reads for all new registers |
| `select.py` | Added GrowattModAllowGridChargeSelect class |
| `time.py` | Replaced dual single-register writes with atomic FC16 pair writes for GrowattModTouTime |
| `docs/CONTROLS.md` | New comprehensive control guide covering all model families |
| `docs/images/` | New SVG diagrams: tou-register-map, mod-tou-setup-flow, sph-time-periods, control-model-comparison |

---

## v0.6.7

Issues: #231 · #226 · #228

### Changes at a Glance

- **Entity ID regression fixed (#231):** v0.6.6's sub-device change caused entity IDs to grow a double prefix (e.g., `sensor.growatt_modbus_grid_growatt_modbus_energy_to_grid_today`). IDs are now correct and short. **All existing entity IDs are automatically migrated on first load — no manual action needed**, but automations/dashboards using the old bugged IDs will need updating.
- **WIT battery current no longer drops to 0 A when the 8000-range block read fails intermittently (#226)** — critical registers are now retried individually after a failed block read.
- **MOD HU (MOD 12-KTL3-HU, MOD TL3-XH) improvements (#228):**
  - `pv1_energy_today`, `pv2_energy_today`, and `pv_energy_total` sensors now work (registers were missing from MOD profile)
  - `charge_stopped_soc`, `discharge_stopped_soc`, `charge_power_rate`, and `ac_charge_enable` controls added to MOD profile
  - Battery power now sourced from VPP range (31200/31201) — more reliable than the intermittent 3000-range charge/discharge registers
  - DTC code 5401 (MOD 12-KTL3-HU) added to auto-detection — fresh installs now select the correct Hybrid profile automatically

---

### ⚠️ Important Upgrade Note — Entity ID Changes (#231)

**This release changes entity IDs for all sensors, controls, and binary sensors.**

#### Background

v0.6.6 introduced sub-devices (Solar, Grid, Load, Battery) so entities could be logically grouped in the Home Assistant device list. When an entity belongs to a sub-device, HA generates its entity ID by combining the sub-device slug with the entity name slug. This was unintentional at the time: because entity `_attr_name` still included the integration prefix ("Growatt Modbus …"), HA created IDs with a double prefix — for example:

```text
sensor.growatt_modbus_grid_growatt_modbus_energy_to_grid_today
                         ↑ sub-device slug   ↑ entity name slug (still had prefix)
```

#### What the fix does

Entity classes now set `has_entity_name = True` and use only the **short name** (e.g., "Energy to Grid Today"). HA then composes:

```text
{domain}.{device_slug}_{short_name_slug}
sensor.growatt_modbus_grid_energy_to_grid_today
```

#### Automatic migration

The integration migrates all existing entity IDs on first load using the entity registry (`unique_id` is the stable anchor — the entity's internal identity never changes, only its ID string). You will see log entries like:

```text
v0.6.7 entity ID migration: sensor.growatt_modbus_grid_growatt_modbus_energy_to_grid_today → sensor.growatt_modbus_grid_energy_to_grid_today
```

#### What you need to do

**For most users: nothing.** HA will automatically update entity references in the Energy Dashboard and Lovelace cards that use entity IDs directly.

**Check and update manually:**

- Automations or scripts that reference entity IDs by string (not entity picker)
- External integrations or Node-RED flows using the old IDs
- Any custom Lovelace cards that hardcode entity IDs rather than using the entity picker

#### New entity ID pattern (examples)

| Entity | Old ID (v0.6.6 bugged) | New ID (v0.6.7) |
| ------ | ---------------------- | --------------- |
| Energy to Grid Today | `sensor.growatt_modbus_grid_growatt_modbus_energy_to_grid_today` | `sensor.growatt_modbus_grid_energy_to_grid_today` |
| Battery SoC | `sensor.growatt_modbus_battery_growatt_modbus_battery_soc` | `sensor.growatt_modbus_battery_battery_soc` |
| PV Energy Today | `sensor.growatt_modbus_solar_growatt_modbus_energy_today` | `sensor.growatt_modbus_solar_energy_today` |
| House Consumption | `sensor.growatt_modbus_load_growatt_modbus_house_consumption` | `sensor.growatt_modbus_load_house_consumption` |
| Inverter Status | `sensor.growatt_modbus_growatt_modbus_inverter_status` | `sensor.growatt_modbus_inverter_status` |

> **Note:** If your integration name is not "Growatt Modbus" (e.g., you renamed it during setup), substitute your actual device name slug in the examples above.

---

### 🔧 Fix — WIT Battery Current Drops to 0 A on Intermittent Block Read Failure (#226)

WIT inverters read battery registers from the 8000–8999 range in a single block. If that block read fails (intermittent RS485/TCP instability), all 8000-range registers are absent from the cache for that cycle. `battery_current` (register 8035) resolves to `None or 0.0 = 0.0`, so the entity shows 0 A — even when the battery is actively charging or discharging.

**Fix (`growatt_modbus.py`):** After any failed 8000-range block read, the five most critical registers (8034 battery voltage, 8035 battery current, 8093–8095 battery SoC / charge state) are retried individually. If a single-register read succeeds, that value is placed in the cache and used for the cycle. A warning log is emitted on block failure; per-register retry results are logged at DEBUG level.

---

### 🔧 Fix — MOD HU: PV String Energy Sensors Always 0 (#228)

`pv1_energy_today`, `pv2_energy_today`, and `pv_energy_total` were absent from the MOD TL3-XH hybrid profile. The corresponding registers (59/60, 63/64, 91/92) are in the base 0–124 scan range and respond correctly on MOD HU hardware (confirmed: 9.2 kWh, 10.4 kWh, 3445 kWh).

**Fix (`profiles/mod.py`):** Registers 59/60, 63/64, and 91/92 added to `MOD_6000_15000TL3_XH` `input_registers`.

---

### 🔧 Fix — MOD HU: Battery Power Intermittently Shows 0 (#228)

The 3000-range charge/discharge registers (3178–3181) used as the primary battery power source on MOD HU are unreliable — they intermittently return 0 during the same poll cycle in which `battery_power` at VPP registers 31200/31201 shows the correct value (+1130 W charging in scan #228-2).

**Fix (`profiles/mod.py`):** Registers 31200/31201 renamed from `battery_power_vpp_high/low` to `battery_power_high/low`. With the `_vpp` suffix removed, the coordinator's standard fallback chain finds these registers as the primary signed battery power source. Charge/discharge power entities are then derived from the sign of `battery_power` — positive = charging, negative = discharging — consistent with the standard convention used by all other profiles.

---

### New — MOD HU: Charge/Discharge SOC Controls (#228)

The following controls now appear on MOD Hybrid installs. All four holding registers were confirmed responding in scan #228:

| Control | Register | Description |
| ------- | -------- | ----------- |
| Discharge Stopped SoC | 1071 | Minimum SoC before battery stops discharging |
| Charge Power Rate | 1090 | Battery charge power rate limit (0–100%) |
| Charge Stopped SoC | 1091 | SoC level at which battery stops charging |
| AC Charge Enable | 1092 | Allow charging from the grid (AC source) |

---

### New — Auto-Detection: DTC Code 5401 (#228)

DTC code 5401 (reported by MOD 12-KTL3-HU hardware) was not in the detection map. Fresh installs fell back to heuristic detection and selected the grid-tied MOD profile instead of the Hybrid profile.

**Fix (`auto_detection.py`):** DTC 5401 now maps to `mod_6000_15000tl3_xh_v201` (same as DTC 5400).

---

## v0.6.6

Issues: #203 · #204 · #18 · #131 · #206 · #212 · #214 · #224 · #226

### Summary

- Energy sensors no longer show 0 or corrupt totals when the inverter is offline or sleeping at night — energy totals are now persisted across HA restarts
- WIT battery current fixed (had shown 0 since ~v0.5.4)
- MIN TL-XH startup Modbus warning spam and `via_device` error eliminated
- Control entities (`control_authority`, VPP export limit) now gated on live hardware probe — no longer appear on hardware that doesn't support them
- WIT: disabling control authority no longer silently resets export limit mode
- TL-XH / MOD / WIT `serial_number` sensor entity now shows correct VPP serial from registers 3001–3005 (was showing garbled data from legacy registers)
- SPE 8000-12000 ES profile added
- Write verification with automatic retry on all control writes; cloud override detection with persistent HA notification
- MOD TL3-XH TOU schedule controls (4 time periods)
- SPF battery power and energy sensors fixed (were showing 0 due to voltage guard and offline classification issues)
- Universal Register Scanner: VPP control ranges and MOD holding ranges added

---

### 🔧 Fix — Energy Sensors Show 0 at Night / After HA Restart (Issues #206, re-fix)

Two further root causes found after the v0.6.6b2 fix for issue #206:

1. **Empty register response not treated as failure** (`growatt_modbus.py`): When the RS485-to-TCP adapter is online but the inverter is sleeping, some adapters return a valid TCP frame with an empty register list. This passed the non-None check, set `_inverter_online = True`, and all sensor values defaulted to `0.0`. Empty and short-count responses are now rejected as read failures, correctly triggering offline behaviour.

2. **Energy retention not persisted across HA restarts** (`coordinator.py`): `_retained_lifetime_totals` and `_retained_daily_totals` were in-memory dicts, cleared on every restart. After a nighttime HA restart, there was no retained baseline to compare against when the dormant inverter returned zeros. These dicts are now persisted to HA storage (`.storage/growatt_modbus.<entry_id>_energy_totals`) — lifetime totals always restored; daily totals restored only if saved on the same calendar day.

3. **Wrong field names in debounce reset** (`coordinator.py`): The wakeup debounce was assigning to `data.battery_charge_today` / `data.battery_discharge_today` (non-existent fields). Corrected to `charge_energy_today` / `discharge_energy_today`.

4. **Battery energy fields missing from midnight reset** (`coordinator.py`): Both midnight reset paths now zero `charge_energy_today`, `discharge_energy_today`, `ac_charge_energy_today`, `ac_discharge_energy_today`, `op_discharge_energy_today`.

---

### 🔧 Fix — Energy Totals Dropping to Zero on Dormant/Offline Inverters (Issue #206)

`total_increasing` energy sensors returned `0` when the inverter was dormant at night or truly offline, causing phantom counter resets in the HA Energy Dashboard.

**Two root causes:**

1. **Dormant inverter:** Stays powered (battery/grid) and responds to Modbus but returns `0` for all production registers. Connection succeeds → `_inverter_online = True` → sensors report zeros.
2. **Truly offline inverter:** Coordinator returned cached data with `last_update_success = True` → entities stayed "available" → HA recorded stale flatlines as real data.

**Fix:**

- **`available = False` when offline:** Sensor entities check `coordinator.is_online`. All entities go unavailable when the inverter stops responding — statistics engine ignores unavailable states.
- **Dormant-inverter retention:** `_protect_energy_totals()` tracks last known non-zero values. When hardware reports `0` but a non-zero was previously seen, the retained value is substituted. Daily retention clears at midnight.

---

### 🔧 Fix — WIT Battery Current Always Shows 0 (Issue #226)

WIT's `battery_current` register is at address 8035 (8000–8124 range). Battery range detection only scored VPP (≥31000) and fallback (1000–3999) addresses — 8035 was never scored, range resolved as `'vpp'`, filter `addr >= 31000` excluded register 8035 → `battery_current = 0`.

**Fix** (`growatt_modbus.py`): 8000–8999 addresses now count as VPP-tier in `_detect_battery_register_range()`. `_find_register_by_name_with_fallback()` also checks the 8000-range as a secondary fallback when the primary range filter returns empty. This also restores battery power scale auto-detection which requires `battery_current != 0`.

The 20% power overestimation noted in the same issue is not yet addressed — register scan data needed to confirm root cause.

---

### 🔧 Fix — MIN TL-XH: Startup Warning Spam + via_device Error (Issue #224)

**A) Startup Modbus warnings:** MIN TL-XH receives `ExceptionResponse(exception_code=1)` for optional VPP registers (31000+) that don't exist on its firmware. These were already suppressed after the first attempt via `_failed_optional_ranges`, but the first-attempt log was at WARNING level. A new `log_errors` parameter on `read_input_registers()` downgrades first-attempt errors to DEBUG for optional register ranges.

**B) `via_device` race condition (HA 2025.12+):** Sub-devices reference `via_device = (DOMAIN, f"{entry_id}_inverter")`. The parent device could be missing from the registry when sub-device sensors registered, causing "referencing a non-existing via_device" errors. Fixed by explicitly pre-creating the parent inverter device in `__init__.py` using `device_registry.async_get_or_create()` before `async_forward_entry_setups()`.

---

### 🔧 Fix — Control Authority Selector Shown on Unsupported Hardware (Issue #224)

`control_authority` (register 30100) appeared as a select entity on MIN TL-XH, MIN TL-X, and other profiles where the hardware does not implement the VPP 2.01 control register range. Any write silently failed with Illegal Function.

**Fix:** The entity is now gated on a live hardware probe — same pattern as `vpp_export_limit_enable`. A `vpp_control_authority_available` flag is set only when register 30100 returns a valid response at startup. If unresponsive, the entity is not created and any pre-existing stale entity is removed from the entity registry on reload.

---

### 🔧 Fix — TL-XH / MOD / WIT Serial Number Entity Shows Incorrect Value

The `serial_number` sensor entity on VPP-range models read from holding registers 9–13 (legacy base range), which on VPP firmware does not contain the serial number — producing garbled output (e.g. "AL1.0ZAba").

VPP-range models store the serial number in holding registers 3001–3005 (10 ASCII chars, one pair per register). After the legacy read, affected profiles now attempt a second read of that range. If the result is a valid Growatt-format serial (≥4 chars, first two letters), it overrides; otherwise the legacy value is kept as fallback.

**Models affected:** All profiles with `TL_XH`, `MOD_`, or `WIT_` in the register map name. Note: the HA Devices & Services serial was already correct via the coordinator's separate read path — only the sensor entity was wrong.

---

### 🔧 Fix — WIT: Disabling Control Authority Resets Export Limit Mode (Issue #203)

Disabling `control_authority` (register 30100 = 0) transiently resets register 122 (`export_limit_mode`) to 0 as a WIT hardware side-effect. Older firmware does not auto-restore the value, silently clearing the export limit configuration.

**Fix** (`select.py`, `coordinator.py`): Register 122 is read and saved before writing `control_authority = Disabled`. When `control_authority = Enabled` is written and verified, the saved value is restored after a 300ms delay. WIT profiles only.

---

### ✨ New — SPE 8000-12000 ES Profile (Issue #212)

Added support for the **SPE 8000-12000 ES** single-phase hybrid inverter. Register scan analysis confirmed it uses the same Modbus register protocol as SPF (registers 0–97), despite being grid-tied with peak shaving capability. Features: dual MPPT, battery storage, peak shaving, parallel operation (up to 108kW), dual outputs.

Auto-detection via model name patterns (SPE8000, SPE10000, SPE12000). Manual selection available as "SPE (8-12kW)".

---

### ✨ New — Write Verification & Cloud Override Detection (Issue #214)

All control writes now include **read-back verification** with up to 3 retries. If a verified write is later found to have reverted on the next poll cycle (e.g. overwritten by ShineWiFi dongle), a **persistent notification** appears in HA explaining the issue. A setup warning is also shown when configuring a battery-enabled inverter with a cloud dongle detected.

---

### 🔧 Fix — Stale Time Period `number` Entities After Upgrade (Issue #214)

After upgrading from pre-v0.6.4, old `number` platform `time_period_*_start/end` entities remained alongside the new `time` platform entities. Entity registry migration in `__init__.py` removes the stale entities automatically on HA restart.

---

### 🔧 Fix — VPP Export Limit Controls Appear on Non-VPP Inverters

MIN TL-X and other non-VPP inverters showed `VPP Export Limit Enable` and `VPP Export Limit Power Rate` controls even though the hardware does not support registers 30200–30201.

**Fix:** Entity creation is gated on a `vpp_export_limit_available` flag set only when those registers respond. Stale entities are removed on reload.

---

### ✨ New — MOD TL3-XH TOU Schedule Controls (Issue #131)

MOD Hybrid users can now set Time-of-Use schedule periods from Home Assistant: 4 × time period start (HH:MM), 4 × end, 4 × priority (Load/Battery/Grid), 4 × enable. Uses holding registers 3038–3045 with bit-packed encoding (`bit15=enable, bit13-14=priority, bit8-12=hour, bit0-7=minute`).

---

### 🔧 Fix — SPF Battery Power and Energy Sensors Showing Zero (Issues #204, #18)

Three root causes fixed:

1. **Offline behaviour classification:** `battery_charge_total`, `battery_discharge_total`, `ac_charge_energy_total`, and related sensors were not correctly classified in `SENSOR_TYPES`, causing them to drop to 0 when offline instead of going unavailable.
2. **AC input / load power offline behaviour:** `ac_input_power`, `ac_apparent_power`, and `load_power` were not classified as `power` sensors, causing them to go unavailable when they should hold `0` while offline.
3. **Battery power zeroed at SOC > 0:** The 10V voltage guard (to prevent garbage readings from a disconnected battery) also blocked power readings from connected batteries reporting 0V in bypass/standby. The guard now requires **both** voltage `< 10V` **and** SOC `< 5%` before zeroing battery power.

---

### ✨ New — Universal Scanner: VPP Control Ranges + MOD Holding Ranges

Scanner now covers VPP control holding registers (30100–30499, individually enabled via `scan_vpp_control`) and MOD TL3-XH FC04 holding ranges including TOU registers 3038–3045 (`scan_mod_extended`).

---

## v0.6.4

- #204 · #214

### 🔧 Fix — Time Period Controls Show HH:MM Time Picker Instead of Raw Numbers (Issue #214)

**SPH** inverter users with time period controls (e.g., SPH 3600) reported the start/end time displays showing values like `1.536` and `5.632` instead of readable times. These correspond to 06:00 and 22:00. Any attempted writes were sending incorrect values to the inverter hardware.

**Root cause:** The inverter stores time in a **hex-packed byte format** — `hours × 256 + minutes` — not the HHMM decimal format the code assumed. 06:00 encodes as `0x0600 = 1536` and 22:00 as `0x1600 = 5632`. The previous `NumberEntity` implementation displayed the raw integer directly (showing `1536`) and wrote user-entered values without conversion (writing `600` for "06:00" produced `0x0258` = 02h 88m — invalid time).

**Fix:**

- Replaced the 6 time period start/end `NumberEntity` controls with a new `TimeEntity` platform (`time.py`)
- `TimeEntity` provides a native **HH:MM time picker** in the Home Assistant UI
- Decode: `raw → (hours = raw >> 8, minutes = raw & 0xFF) → datetime.time(hours, minutes)`
- Encode: `datetime.time(h, m) → (h << 8) | m → register write`
- Added `Platform.TIME` to `__init__.py` platform list
- Number entities no longer created for `time_period_*_start/end` controls (to avoid duplicates)

**Impact:** Time period enable controls (`time_period_*_enable`) are unchanged — they remain Select entities (Enabled/Disabled).

---

### 🔧 Fix — SPF 5000/6000 ES Battery Entities Showing Zero Since v0.6.0 (Issue #204)

**SPF 5000 ES** and **SPF 6000 ES Plus** users reported all battery entities (voltage, SOC, power, temperature) showing 0 after upgrading from v0.5.9. Direct register reads confirmed the data was present — e.g., register 18 returned 48.73V — but the HA entity showed 0.0V.

**Root cause:** Commit `e26a870` (v0.6.0) introduced `_detect_battery_register_range()` to resolve an ambiguity in models that expose battery data at both VPP (31000+) and fallback (1000–3999) addresses. The scoring logic awards points only for addresses in those two ranges. SPF uses the legacy base range (registers 0–97), so neither score incremented — both stayed 0 — and the code defaulted to `'fallback'`. The subsequent `_find_register_by_name_with_fallback()` then filtered for `1000 ≤ addr < 4000`, which excluded SPF's register 17 (`battery_voltage`), returning `None`. All battery values silently fell back to 0.

**Fix:** Added `'legacy'` range handling to both methods in `growatt_modbus.py`. When `offgrid_protocol=True` (set in all SPF profiles), `_detect_battery_register_range()` immediately returns `'legacy'` without running the scoring loop. `_find_register_by_name_with_fallback()` then accepts any address below 1000 for `'legacy'` range — matching SPF's register space correctly.

---

## v0.6.3

- #174 · #207 · #209 · #210 · #211

### 🔧 Fix — SPH TL3 Energy Today Missing PV3 String (Issue #211)

**SPH TL3 10000** (and other 3-MPPT models) showed `Energy Today` roughly **1/3 lower than expected** after the v0.5.0 upgrade.

**Root cause:** The v0.5.0 fix for Issue #172 changed `energy_today` to use per-MPPT DC energy registers (pv1+pv2) instead of AC output register 53-54. However, the profile and coordinator never included **PV string 3** (registers 67-68, `Epv3_today`) in the sum — so on 3-string inverters the PV3 contribution was silently dropped.

**Fix:**

- Added `pv3_energy_today_high/low` (registers 67-68) to `profiles/sph_tl3.py`
- Added `pv3_energy_today` field to `GrowattData` dataclass
- Coordinator now reads PV3 energy and includes it in the `energy_today` sum when PV3 is connected

**Impact:** 2-string models are unaffected (`pv3_connected = False` gates the addition).

---

### 🔧 Fix — SPH TL3 Grid Import Energy Mirrors Export (Issues #209, #211)

**SPH TL3** users with `Invert Grid Power` enabled reported that `Grid Import Energy Today` showed the same values as grid export energy — effectively mirroring it.

**Root cause:** The v0.5.1 fix for Issue #183 introduced a code path where, when `invert_grid_power=True` and a hardware energy register is available, the code reads from `energy_to_grid_today` (export) instead of `energy_to_user_today` (import). This was based on the assumption that CT clamp orientation also swaps the hardware energy accumulators.

**Why the assumption is wrong:** SPH TL3's energy registers (1044-1051) are accumulated by the inverter's **internal bidirectional power meter**, independent of CT clamp direction. `energy_to_user_today` always correctly measures grid import regardless of CT orientation — only real-time power registers need CT inversion.

**Fix:** Removed the CT-orientation swap for hardware energy registers in `sensor.py`. When hardware import registers are available, they are always used directly. The `invert_grid_power` flag continues to apply correctly to all real-time power sensors.

---

### 🔧 Fix — SPH 3-6kW and 7-10kW V2.01 Missing Power Flow Registers (Issue #207)

**SPH 3600** (and all SPH 3-10kW V2.01 protocol models) showed **incorrect grid import/export direction** and **Power to User / Power to Load always 0**.

**Root cause:** The `SPH_3000_6000_V201` and `SPH_7000_10000_V201` profiles were missing the storage-range power flow registers (1015-1038) and grid import energy registers (1044-1047). Without them, `power_to_user`, `power_to_grid`, and `power_to_load` stayed at 0, causing the fallback calculation `(solar + discharge) − (load + charge)` to produce wrong grid direction signs.

**Fix:** Added the following registers to both V201 profiles in `profiles/sph.py`, per Growatt Modbus RTU V1.20 protocol:

| Register | Name | Description |
| --- | --- | --- |
| 1021-1022 | `power_to_user` | AC power to user total (grid import power) |
| 1029-1030 | `power_to_grid` | AC power to grid total (signed: positive=export) |
| 1037-1038 | `power_to_load` | INV power to local load total |
| 1044-1045 | `energy_to_user_today` | Grid import energy today |
| 1046-1047 | `energy_to_user_total` | Grid import energy total |

---

### 🔧 Fix — SPF Battery Power Sign Correction During PV Charging (Issue #174)

**SPF 6000 ES Plus** intermittently showed battery as **discharging when it was actually charging** from solar (status=5, PV Charge).

**Root cause:** SPF hardware occasionally transmits a positive raw value for the battery power register during PV charging. After applying the required sign inversion (`combined_scale=-0.1`), the result becomes negative — misidentified as discharging. Battery current (register 68) cannot be used for validation as it only measures during AC charging.

**Fix:** Added `_validate_spf_battery_power_sign()` method in `growatt_modbus.py`. When `offgrid_protocol=True`, the inverter status code is checked after the hardware sign inversion. If the status indicates charging (codes 5-10) but battery power is negative, or discharging (code 2) but power is positive, the sign is corrected and a warning is logged. A 10W threshold prevents noise correction. Ambiguous status 12 (PV Charge+Discharge) is skipped.

---

### 🔧 Fix — SPH TL3 Missing Controls: AC Charge, Time Periods, Priority Mode (Issue #210)

**SPH 10000TL3 BH-UP** (and all SPH TL3 3-10kW models) were missing the **AC Charge**, **Time Period**, and **Discharge/Charge Rate** control entities in Home Assistant. Additionally, **Priority Mode** changes silently failed to write.

**Root cause — two bugs in `profiles/sph_tl3.py`:**

1. **Missing holding registers:** The base profile only defined 3 holding registers (`on_off`, `system_enable`, `priority`). The integration creates control entities only for registers present in the profile, so 14 registers (1070–1071, 1090–1092, 1100–1108) were absent → no entities created.

2. **Wrong register name:** Register 1044 was named `priority` instead of `priority_mode`. All control write paths resolve registers by name — `SELECT_DEFINITIONS` uses the key `priority_mode`, so no holding register was found at write time → silently dropped.

**Fix:** Replaced the `holding_registers` block in `profiles/sph_tl3.py` with the full 18-register set (matching SPH 7-10kW single-phase), adding the correct name and full metadata for each register. The `SPH_TL3_3000_10000_V201` profile inherits these automatically via Python dict unpacking.

**Controls now available for SPH TL3:**

| Register | Entity | Description |
| --- | --- | --- |
| 1044 | Priority Mode | Load First / Battery First / Grid First |
| 1070 | Discharge Power Rate | % limit on battery discharge |
| 1071 | Discharge Stop SOC | SOC% at which discharge halts |
| 1090 | Charge Power Rate | % limit on battery charge |
| 1091 | Charge Stop SOC | SOC% at which charge halts |
| 1092 | AC Charge Enable | Enable/disable charging from grid |
| 1100–1108 | Time Periods 1–3 | Start/end/enable for timed charge windows |

---

## v0.6.2

### 🔧 Fix — MIN TL-XH Battery Energy Totals Showing Zero (Issue #191)

Three battery energy sensors were always reporting 0 for **MIN TL-XH 3000-10000 V2.01** inverters after the v0.6.1 upgrade.

**Sensors affected:** Battery Charge Total, Battery Discharge Total, AC Charge Energy Total

**Root cause:** The `MIN_TL_XH_3000_10000_V201` profile defined battery energy *today* registers (3125–3130) but was missing the corresponding *total* registers. The coordinator searched for register names `charge_energy_total_low`, `discharge_energy_total_low`, and `ac_charge_energy_total_low` — none existed in the profile — and fell back to the `GrowattData` defaults of `0.0`. Because `hasattr()` still returned `True` (the field exists in the dataclass), sensors appeared in HA but perpetually showed 0.

**Fix:** Added the missing registers to `profiles/tl_xh.py`, confirmed against real hardware scan:

| Registers | Sensor | Confirmed Value |
| --- | --- | --- |
| 3127 / 3128 | Battery Discharge Total | 481.5 kWh |
| 3131 / 3132 | Battery Charge Total | 528.9 kWh |
| 3133 / 3134 | AC Charge Energy Today | ~0 kWh (grid→battery today) |
| 3135 / 3136 | AC Charge Energy Total | 37.4 kWh (grid→battery lifetime) |

The `ac_charge_energy_total` register (3135/3136) tracks exclusively grid→battery charging, matching the Growatt server "Batterieladung aus Stromnetz" lifetime value.

---

### 🔧 Fix — Energy Sensors Show Unavailable When Inverter is Offline (Issue #206)

Energy sensors (device class `energy`, state class `total_increasing`) previously retained their last value when the inverter went offline at night. When the inverter came back online in the morning, Home Assistant's energy statistics briefly saw the previous day's retained value followed by the new day's value, creating artificial spikes or outliers in the energy dashboard.

**Fix:** Energy sensors now report `unavailable` instead of retaining stale values when the inverter is offline. Home Assistant correctly handles unavailable periods in energy statistics — no data gap is recorded, and the dashboard picks up cleanly from the next valid reading.

**Affected sensors:** All energy sensors (energy today, energy total, grid import/export energy, battery charge/discharge energy, AC charge energy) across all inverter models.

**Before:** Inverter goes offline at 22:00 → sensors retain e.g. 12.5 kWh all night → inverter wakes at 06:00 showing 0.1 kWh → HA records a large negative spike to correct the total.

**After:** Inverter goes offline at 22:00 → sensors show `unavailable` → inverter wakes at 06:00 showing 0.1 kWh → HA records normally with no outlier.

---

### 🔧 Fix — Battery Power Garbage Values When Battery Disconnected (Issue #205)

On SPF off-grid inverters with a disconnected or fully depleted battery (voltage = 0V), the battery power registers contained garbage values that were being interpreted as valid signed 32-bit readings. This caused the battery power sensor to show absurd values (e.g. **101 MW**) instead of 0W.

**Root cause:** With battery voltage at 0V, register 77 (battery_power_high) = 50000, register 78 (battery_power_low) = 0. Combined as signed 32-bit: −1,018,167,296. Scaled by −0.1: +101,816,729.6 W.

**Fix:** Added a voltage threshold check — if battery voltage is below 10V, battery power is forced to 0W regardless of register values. Affected models: SPF series and potentially other models with battery storage when the battery is physically absent.

---

### 🆕 MOD TL3-XH — Battery Sensors Added (Issue #131)

The **MOD 10000TL3-XH** (VPP V2.01, DTC 5400) profile now exposes complete battery monitoring from the 3125–3185 and 31218 register ranges. Previously these registers were either absent from the profile or incorrectly mapped (`ac_charge_energy_total` was misidentified as `battery_bms_temp` at register 3136, which would have shown 530.5°C).

**New sensors for MOD TL3-XH:**

| Registers | Sensor | Scale | Confirmed at Scan |
| --- | --- | --- | --- |
| 3125 / 3126 | Battery Discharge Today | ×0.1 kWh | 6.3 kWh |
| 3127 / 3128 | Battery Discharge Total | ×0.1 kWh | 1216.9 kWh |
| 3129 / 3130 | Battery Charge Today | ×0.1 kWh | 4.3 kWh |
| 3131 / 3132 | Battery Charge Total | ×0.1 kWh | 1389.0 kWh |
| 3133 / 3134 | AC Charge Energy Today | ×0.1 kWh | 4.0 kWh |
| 3135 / 3136 | AC Charge Energy Total | ×0.1 kWh | 530.5 kWh |
| 3169 | Battery Voltage | ×0.01 V | 72.83 V |
| 3170 | Battery Current | ×0.1 A | 0.0 A |
| 3171 | Battery SOC | ×1 % | 10% (confirmed at scan) |
| 3175 / 3176 | Battery Temp | ×0.1 °C | 45.4°C |
| 3178 / 3179 | Battery Discharge Power | ×0.1 W | 5.0 W |
| 3180 / 3181 | Battery Charge Power | ×0.1 W | 0.0 W |
| 31218 | Battery SOH | ×1 % | 100% |

Register scan was conducted at night (SOC=10% confirmed), validating register 3171=10 as SOC and 31218=100 as State of Health.

**Bug fix (same PR):** Register 3136 was previously mapped as `battery_bms_temp` — a copy-paste error from a nearby temperature register. The raw value of 5305 × 0.1 = 530.5 kWh is clearly an energy value, not a temperature. Corrected to `ac_charge_energy_total_low`.

**Battery control (MOD):** Battery control holding registers have not yet been confirmed for MOD hardware. Register scan showed the SPH-style 1000–1124 range returns all zeros, and VPP control (30099=0) is not available. Control is deferred to a follow-up release pending hardware confirmation. See [docs/CONTROL.md](docs/CONTROL.md) for details.

---

### 🎛️ Inverter Control — SPH, SPF, WIT

This release documents and validates the full control entity stack for SPH, SPF, and WIT inverter families. These controls were already implemented in the codebase; this release confirms their status, adds documentation, and ensures all are correctly exposed in Home Assistant.

**Control is profile-gated:** entities are only instantiated when the corresponding holding registers are present in the active profile. No controls appear for models without confirmed registers.

#### SPH Hybrid (3–10kW) — Persistent Writes

| Entity | Type | Register | Options / Range |
| --- | --- | --- | --- |
| Priority Mode | Select | 1044 | Load First / Battery First / Grid First |
| AC Charge Enable | Select | 1092 | Disabled / Enabled |
| Discharge Power Rate | Number | 1070 | 0–100 % |
| Discharge Stop SOC | Number | 1071 | 0–100 % |
| Charge Power Rate | Number | 1090 | 0–100 % |
| Charge Stop SOC | Number | 1091 | 0–100 % |
| Time Period 1–3 Start/End/Enable | Number/Select | 1100–1108 | HHMM / Enabled-Disabled |
| System Enable | Select | 1008 | Disabled / Enabled *(HU models only)* |

#### SPF Off-Grid (3–6kW) — Persistent Writes

| Entity | Type | Register | Options / Range |
| --- | --- | --- | --- |
| Output Priority | Select | 1 | SBU / SOL / UTI / SUB |
| Charge Priority | Select | 2 | CSO / SNU / OSO |
| AC Input Mode | Select | 8 | APL / UPS / GEN |
| Battery Type | Select | 39 | AGM / Flooded / User / Lithium / User 2 |
| AC Charge Current | Number | 38 | 0–80 A |
| Generator Charge Current | Number | 83 | 0–80 A |
| Battery→Utility SOC | Number | 37 | 0–100 % (Lithium) |
| Utility→Battery SOC | Number | 95 | 0–100 % (Lithium) |

#### WIT Commercial Hybrid (4–15kW) — VPP Time-Limited Overrides

| Entity | Type | Register | Options / Range |
| --- | --- | --- | --- |
| Work Mode | Select | 202 | Standby / Charge / Discharge |
| Active Power Rate | Number | 201 | 0–100 % |
| Export Limit (W) | Number | 203 | 0–20000 W |
| Control Authority | Select | 30100 | Disabled / Enabled |
| VPP Export Limit Enable | Select | 30200 | Disabled / Enabled |
| VPP Export Limit Rate | Number | 30201 | −100–+100 % |
| Remote Power Control | Select | 30407 | Disabled / Enabled |
| Remote Control Duration | Number | 30408 | 0–1440 min |
| Remote Charge/Discharge Power | Number | 30409 | −100–+100 % |

WIT commands are time-limited. The inverter reverts to its TOU schedule when the duration expires. See [docs/WIT_CONTROL_GUIDE.md](WIT_CONTROL_GUIDE.md) for the full VPP protocol explanation.

📖 **[Full control documentation →](docs/CONTROL.md)**

---

### Model and Sensor Availability Summary

| Model | Battery Sensors | Battery Control | Control Method | Notes |
| --- | --- | --- | --- | --- |
| **SPH 3–6kW** | Yes | Yes | Persistent writes | Registers 1044, 1070–1108 |
| **SPH 7–10kW** | Yes | Yes | Persistent writes | Same register range as 3–6kW |
| **SPH/SPM HU 8–10kW** | Yes + BMS | Yes | Persistent writes | Adds BMS sensors, system_enable (1008) |
| **SPF 3–6kW ES PLUS** | Yes (limited) | Yes | Persistent writes | No battery temp; current only during AC charge |
| **WIT 4–15kW** | Yes | Yes (timed) | VPP overrides | Time-limited; base mode is read-only |
| **MOD 10000TL3-XH** | Yes (new) | No (pending) | — | Control registers not yet confirmed |
| **MIN TL-XH 3–10kW** | Yes (fixed) | No | — | No battery control registers |
| **MIN 3–10kW** | No | No | — | Grid-tied, no battery |
| **MIC 0.6–3.3kW** | No | No | — | Grid-tied micro inverter |

---

## v0.6.1

## 🔧 Critical Fix - MIN TL-XH Solar and Grid-Import Energy Calculations

This release fixes critical energy calculation issues for **MIN TL-XH 3000-10000 V2.01** inverters that were introduced in v0.5.1.

### What Was Fixed:

**Problem 1: Grid Import Energy Showing Zero or Null**

After upgrading from v0.4.9 to v0.5.1+, MIN TL-XH users reported:
- Grid import energy became null/zero after update
- Grid power visible but grid import energy was 0
- Energy dashboard showed no grid import despite actually importing from grid

**Root Cause:**
Version 0.5.1 (commit df333cb) fixed SPH-TL3 grid import energy by using hardware register `energy_to_user_today/total`. However, the code incorrectly assumed this register means "grid import" for ALL inverter models.

The `energy_to_user` register has **different meanings** on different inverter series:
- **SPH family**: `energy_to_user` = Grid IMPORT energy (energy FROM grid TO load)
- **MIN TL-XH family**: `energy_to_user` = Forward active energy (NOT grid import)

This caused MIN TL-XH to use the wrong register (3067-3068) for grid import, resulting in null/zero values.

**Problem 2: Battery Discharge Counted as Solar Production**

MIN TL-XH users reported:
- Solar energy showing higher values than expected
- Battery discharge energy being counted as solar production
- Home energy calculations incorrect due to inflated solar values

**Root Cause:**
The `energy_today` register (3049-3050) on MIN TL-XH represents total system AC output and includes battery discharge. When battery was discharging, this energy was incorrectly counted as solar production.

### The Fix:

**1. Restrict `energy_to_user` Hardware Register to SPH Family Only**

Modified grid import energy calculation to only treat `energy_to_user` as grid import for SPH family profiles:

```python
is_sph_family = inverter_series.startswith("sph_")
has_hardware_import = hasattr(data, "energy_from_grid_today") or (
    is_sph_family and hasattr(data, "energy_to_user_today")
)
```

This ensures MIN TL-XH no longer uses the wrong register for grid import calculations.

**2. Derive MIN TL-XH Solar Energy from Energy Balance**

For MIN TL-XH inverters, calculate true PV-only energy from energy balance terms:

```python
pv_energy_today = load_energy + battery_charge + grid_export
                  - grid_import - battery_discharge
```

This ensures:
- Battery discharge is NOT counted as solar production
- Solar energy reflects actual PV generation only
- Energy balance is mathematically correct

### Impact:

**Grid Import Energy:**
- ✅ MIN TL-XH now correctly calculates grid import energy
- ✅ No longer uses wrong `energy_to_user` register
- ✅ Grid import values are accurate and stable
- ✅ SPH family continues to work correctly with `energy_to_user` register

**Solar Energy Production:**
- ✅ Battery discharge no longer counted as solar
- ✅ Solar energy shows accurate PV-only generation
- ✅ Home energy calculations now correct
- ✅ Energy balance mathematically accurate

### Affected Versions:

- **Broken**: v0.5.1 through v0.6.0 (grid import null/zero, battery counted as solar)
- **Working**: v0.4.9 and earlier (used calculated import, but had battery discharge issue)
- **Fixed**: v0.6.1 (both issues resolved)

### Affected Models:

- MIN TL-XH 3000-10000 V2.01 (all models in this series)

### Migration Notes:

- **No action required** - Updates apply automatically on restart
- Grid import energy will immediately show correct values
- Solar energy will decrease to accurate PV-only values (excluding battery discharge)
- Historical data remains unchanged (new calculations start from restart)

### Technical Details:

**Files Changed:**
- `custom_components/growatt_modbus/sensor.py`:
  - Restricted `energy_to_user` to SPH family only (lines 1227, 1258)
  - Added MIN TL-XH energy balance calculation (lines 1295-1308)

**Related Issues:**
- Fixes user report: Grid import null after v0.4.9 update
- Fixes user report: Battery discharge counted as solar energy
- Related to Issue #183 (SPH-TL3 grid energy fix that caused this regression)

---

# Release Notes - v0.6.0

## 🔧 Fix - Battery Power Inversion for VPP Protocol Registers

This release fixes battery power sign interpretation issues where charge/discharge values appeared inverted on inverters using VPP Protocol V2.01 registers.

### What Was Fixed:

- Battery power registers now correctly interpret signed 16-bit values
- Fixed battery power showing inverted signs (positive when should be negative)
- Added proper register range detection (VPP vs fallback) to ensure consistent battery data
- Improved fallback register detection with score-based approach

### Impact:

- ✅ SPH, SPM, and MIN TL-XH inverters now show correct battery power signs
- ✅ Battery calculations (V×I) now match power register readings
- ✅ Consistent battery data from detected register range

---

# Release Notes - v0.5.8

## 🔧 Fix - Battery Power Sign Interpretation for VPP Protocol Registers

This release fixes battery power inversion issues where battery charge/discharge power values were showing with incorrect signs (positive when should be negative, or vice versa) on inverters using VPP Protocol V2.01 registers.

### What Was Fixed:

**Problem:**
Users with SPH, SPM, and MIN TL-XH inverters using VPP protocol registers reported battery power values showing with inverted signs:
- Battery power showing large positive values (e.g., 56353W) when actually discharging at -918.3W
- Charge/discharge direction appearing backwards in Home Assistant
- Battery power calculations not matching voltage × current

**Root Cause:**
Battery power registers in VPP protocol (31200-31209) use **signed 16-bit values**, but were being interpreted as unsigned integers. This caused:
- Negative discharge values to wrap around to large positive numbers
- Sign bit (0x8000) not being recognized
- Example: -9183 (0xDC31) read as 56353 instead

**Technical Details:**
The existing `_get_register_value()` method already had correct signed conversion logic (lines 664-668 for 32-bit, 682-686 for 16-bit), but only when the register definition includes `'signed': True`. VPP battery power registers were missing this attribute.

### The Fix:

**Added `'signed': True` to VPP battery power registers:**

1. **SPH profiles** (register 31203):
   - `battery_charge_power_low` now marked as signed

2. **TL_XH profiles** (registers 31205, 31209):
   - `charge_power_low` now marked as signed
   - `discharge_power_low` now marked as signed

3. **MIN TL-XH profiles** (registers 31205, 31209):
   - `charge_power_low` now marked as signed
   - `discharge_power_low` now marked as signed

**Updated register descriptions:**
```python
# Before:
31205: {'name': 'charge_power_low', 'desc': 'Battery charge power (unsigned, positive=charging)'}

# After:
31205: {'name': 'charge_power_low', 'signed': True, 'desc': 'Battery charge power (signed: positive=charging, negative=discharging)'}
```

### VPP vs Fallback Register Range Detection

Additionally, this release includes improved battery register fallback detection to ensure consistent data across all battery sensors.

**The Challenge:**
Inverters may support multiple register ranges for battery data:
- **VPP registers** (31200-31299): Modern VPP Protocol V2.01 with signed values
- **Fallback registers** (3000-3999): Legacy range with unsigned/different conventions

Previous implementation would try both ranges independently for each sensor, which could:
- Mix VPP and fallback values across different sensors
- Not distinguish between "legitimately zero" vs "wrong register range"
- Cause inconsistent battery power calculations

**The Solution:**
- Detect which register range is active (VPP vs fallback) **once per session**
- Check multiple key battery sensors (voltage, SOC, power, energy) for non-zero values
- Use score-based detection: whichever range has more non-zero values wins
- Use the detected range **consistently** for ALL battery sensors
- Default to fallback if both ranges are zero (more universal)

This ensures:
- Proper sign interpretation based on register range (VPP=signed, fallback=may vary)
- Consistent data source across all battery sensors
- No mixing of VPP and fallback register data
- Correct handling of legitimate zero values

### Impact:

- ✅ **SPH inverters**: Battery power now shows correct sign (VPP registers properly signed)
- ✅ **MIN TL-XH inverters**: Battery power direction correct (VPP registers properly signed)
- ✅ **All VPP-enabled profiles**: Consistent battery data from detected register range
- ✅ **Fallback registers**: Still work correctly when VPP registers unavailable
- ✅ **Battery calculations**: V×I now matches power register readings

### Affected Models:

**Fixed by VPP register signing:**
- SPH 3-6kW, 7-10kW (VPP Protocol V2.01)
- SPM series
- MIN TL-XH 3000-10000 (VPP Protocol V2.01)
- MOD TL3-XH series

**Improved by register range detection:**
- All models with both VPP and fallback battery registers

### Code Changes:

**Profiles** (`sph.py`, `tl_xh.py`):
- Added `'signed': True` to battery power registers 31203, 31205, 31209
- Updated register descriptions to clarify sign conventions

**Core Logic** (`growatt_modbus.py`):
- Added `_battery_register_range` detection logic
- Score-based detection across multiple battery sensors
- Consistent range usage via `_get_register_value_with_fallback()`

### Files Changed:

- `custom_components/growatt_modbus/profiles/sph.py`: Signed battery power registers
- `custom_components/growatt_modbus/profiles/tl_xh.py`: Signed battery power registers
- `custom_components/growatt_modbus/growatt_modbus.py`: VPP vs fallback range detection

---

## 🔧 Fix - WIT Sensors No Longer Appear on Non-WIT Profiles

This release fixes a sensor visibility issue where **WIT-specific sensors** (`battery_soh` and `battery_voltage_bms`) incorrectly appeared on non-WIT inverter profiles, showing confusing 0 values.

### What Was Fixed:

**Problem:**
Users with non-WIT inverters (MIN TL-XH, SPH, MOD, etc.) reported seeing WIT-only battery sensors that always showed 0:
- Battery State of Health (SOH): 0%
- Battery Voltage BMS: 0V

These sensors are only valid for **WIT series inverters** (WIT 4-15kW), which have specialized battery management registers.

**Root Cause:**
The `battery_soh` and `battery_voltage_bms` attributes were defined in the `GrowattData` dataclass with default values of 0.0. This meant `hasattr(data, 'battery_soh')` always returned `True`, causing Home Assistant to create sensors for all inverter profiles regardless of whether they actually support these registers.

**Evidence:**
- MIN TL-XH profile: No registers 8094 (battery_soh) or 8095 (battery_voltage_bms)
- SPH TL3 profile: No WIT battery registers
- WIT profile: Has registers 8094 and 8095 ✅

### The Fix:

**Changed sensor creation logic:**

1. **Removed from dataclass defaults**: `battery_soh` and `battery_voltage_bms` no longer have default 0.0 values in `GrowattData`

2. **Set dynamically only**: These attributes are now only created via `setattr()` when:
   - The profile has the corresponding registers (8094, 8095)
   - The registers have valid data

3. **Matches BMS sensor pattern**: This follows the same approach used for other advanced sensors like `bms_soh`, `bms_constant_volt`, etc.

### Impact:

- ✅ **WIT inverters** (WIT 4-15kW): Sensors still created normally (registers exist)
- ✅ **MIN TL-XH inverters**: WIT sensors no longer appear (eliminated confusion)
- ✅ **SPH, MOD, TL-XH**: No WIT sensors (cleaner sensor list)
- ✅ **No user confusion**: Only see sensors your inverter actually supports

### Code Changes:

**Lines 216-217** (`growatt_modbus.py`):
```python
# Before:
battery_soh: float = 0.0          # % (State of Health - WIT)
battery_voltage_bms: float = 0.0  # V (BMS voltage reading - WIT)

# After:
# battery_soh and battery_voltage_bms are WIT-only - set dynamically if register exists
```

**Lines 1724-1737** (`growatt_modbus.py`):
```python
# Changed from direct assignment to conditional setattr:
if addr:
    value = self._get_register_value(addr)
    if value is not None:
        setattr(data, 'battery_soh', value)  # Only set if register exists
```

### Affected Models:

**Benefit from this fix** (cleaner sensor list):
- MIN TL-XH 3000-10000
- SPH 3-6kW, 7-10kW, SPH-TL3
- MOD 6000-15000TL3-XH
- MIC, MIN, MID, TL-XH series
- SPF off-grid series

**Still see these sensors** (as intended):
- WIT 4000-15000TL3 (only series with these registers)

### Migration Notes:

- **No action required** - Updates apply automatically on restart
- WIT sensors will disappear from non-WIT inverters
- No impact on actual functionality, only sensor visibility
- Historical data unaffected

### Files Changed:

- `custom_components/growatt_modbus/growatt_modbus.py`: Updated GrowattData dataclass and battery data reading logic
- `custom_components/growatt_modbus/manifest.json`: Version bumped to 0.5.8
- `README.md`: Version badge updated to 0.5.8

---

# Release Notes - v0.5.7

## 🔧 Critical Fix - MIN TL-XH Battery Registers Corrected (Issue #191)

This release fixes a critical battery sensor issue for **MIN TL-XH 3000-10000 V2.01** inverters where all battery sensors (voltage, current, SOC, temperature) showed zero or incorrect values.

### What Was Fixed:

**Problem:**
MIN TL-XH users with battery storage (e.g., MIN-4600TL-XH with ARK battery) reported zero values for all battery sensors:
- Battery voltage: 0V (should be ~212V)
- Battery current: 0A
- Battery SOC: 0% (should be actual percentage like 54%)
- Battery temperature: 0°C (should be actual temp like 21.2°C)

**Root Cause:**
The MIN TL-XH V2.01 profile was using VPP Protocol registers (31200+ range) for battery state, based on the official Growatt VPP Protocol V2.01 specification. However, user scan data proved that MIN TL-XH inverters **do NOT use the VPP 31200+ range** for battery state - they use the **3000+ range** (similar to MOD series layout).

**Evidence from user register scan:**
- VPP range (31200-31222): **ALL ZEROS** ❌
  - 31214 battery_voltage: 0
  - 31215 battery_current: 0
  - 31217 battery_soc: 0
  - 31222 battery_temp: 0

- 3000+ range: **HAS BATTERY DATA** ✅
  - 3169: 21194 → 211.94V (scale 0.01)
  - 3170: battery current (scale 0.1)
  - 3171: 54 → 54% SOC
  - 3176: 212 → 21.2°C battery temp (scale 0.1)

### The Fix:

**For MIN_TL_XH_3000_10000_V201 profile:**

1. **Added PRIMARY battery state registers** at 3169-3176 (3000+ range):
   - 3169: battery_voltage (scale 0.01, note different scale than VPP!)
   - 3170: battery_current (scale 0.1, signed)
   - 3171: battery_soc (scale 1)
   - 3176: battery_temp (scale 0.1, signed)

2. **Renamed VPP 31200+ battery registers** with `_vpp` suffix:
   - 31214: battery_voltage_vpp (not used on MIN TL-XH)
   - 31215: battery_current_vpp (not used on MIN TL-XH)
   - 31217: battery_soc_vpp (not used on MIN TL-XH)
   - 31222: battery_temp_vpp (not used on MIN TL-XH)

3. **Important scale difference**: Battery voltage uses scale **0.01** in 3000+ range vs **0.1** in VPP range!

### Impact:

- ✅ **MIN TL-XH with battery**: All battery sensors now show correct values
- ✅ Battery voltage shows actual voltage (e.g., 211.94V instead of 0V)
- ✅ Battery SOC shows actual percentage (e.g., 54% instead of 0%)
- ✅ Battery temperature shows actual temp (e.g., 21.2°C instead of 0°C)
- ✅ MIN TL-XH now uses MOD-like register layout for battery state

### Affected Models:

- MIN TL-XH 3000-10000 V2.01 with battery storage (e.g., MIN-4600TL-XH with ARK battery)

### Technical Background:

The VPP registers were originally added in November 2025 based on the **official Growatt VPP Communication Protocol V2.01 specification** (dated 2024.9.20), which documented the 31200+ range for battery information. The protocol specification was assumed to apply to all V2.01 inverters including MIN TL-XH.

However, user feedback proved this assumption was **incorrect for MIN TL-XH** - these inverters follow the MOD series register layout (3000+ range) for battery state, not the VPP protocol layout. This is a case where real-world hardware behavior differs from the protocol specification.

### Files Changed:

- `custom_components/growatt_modbus/profiles/tl_xh.py`:
  - MIN_TL_XH_3000_10000_V201: Added registers 3169-3176 as primary battery state
  - Renamed VPP registers 31214/31215/31217/31222 with _vpp suffix
- `custom_components/growatt_modbus/manifest.json`: Version bumped to 0.5.7
- `README.md`: Version badge updated to 0.5.7

### Migration Notes:

- **No action required** - Updates apply automatically on restart
- Battery sensors will immediately show correct values
- If you previously had 0V/0%/0°C, values will now reflect actual battery state
- Historical data remains unchanged (new readings start from restart)

### Related Issues:

- Fixes #191 - MIN TL-XH battery sensors showing zero
- User-confirmed: 3000+ range contains correct battery data, VPP range returns zeros

---

# Release Notes - v0.5.6

## 🔧 Critical Fix - SPH Battery SOC Register Priority (Issue #185)

This release fixes a critical battery SOC (State of Charge) reading issue for **SPH 3-6kW and 7-10kW V2.01** inverters where the SOC sensor disappeared or showed 0% after upgrading to v0.5.4+.

### What Was Fixed:

**Problem:**
After upgrading to v0.5.4+, some SPH users reported that battery SOC disappeared or showed 0% instead of the actual value:
- Battery SOC sensor showing 0% despite battery being charged (e.g., should be 100%)
- Register 17 (legacy) returns incorrect value (0%)
- Register 31217 (VPP range) contains the correct SOC value
- The integration was reading register 17 first due to register lookup priority

**Root Cause:**
The `_find_register_by_name('battery_soc')` function searches input registers in insertion order and returns the first name match. Even though register 1086 was added in v0.5.5 as an "override" for standard SPH V201 models:
1. Register 17 (inherited from base profile) with name='battery_soc' was found **first**
2. Register 1086 with name='battery_soc' was never reached
3. Register 31217 with maps_to='battery_soc' was never reached
4. Result: Integration read register 17 (shows 0%) instead of register 31217 (correct value)

### The Fix:

**For SPH 3-6kW and 7-10kW V2.01 profiles:**

1. **Renamed register 17** to `battery_soc_legacy` (prevents name match)
2. **Removed register 1086** (BMS SOC) from standard SPH V201 profiles
   - Register 1086 is only valid for HU models with Battery Management System
   - Standard SPH 3-6kW/7-10kW models don't have BMS, so register 1086 may not respond
3. **Uses register 31217** (VPP range) as primary SOC source via `maps_to='battery_soc'`
   - User-confirmed working in Issue #185
   - Matches VPP Protocol V2.01 specification

### Impact:

- ✅ **SPH 3-6kW V2.01**: Battery SOC now reads from register 31217 (correct value)
- ✅ **SPH 7-10kW V2.01**: Battery SOC now reads from register 31217 (correct value)
- ✅ Register priority fixed: 31217 (VPP) instead of 17 (legacy 0%)
- ✅ HU models unaffected (still use register 1086 BMS SOC)

### Affected Models:

- SPH 3000-6000 V2.01 (standard, non-HU)
- SPH 7000-10000 V2.01 (standard, non-HU)

### Files Changed:

- `custom_components/growatt_modbus/profiles/sph.py`:
  - SPH_3000_6000_V201: Renamed register 17, removed register 1086
  - SPH_7000_10000_V201: Renamed register 17, removed register 1086
- `custom_components/growatt_modbus/manifest.json`: Version bumped to 0.5.6
- `README.md`: Version badge updated to 0.5.6

### Migration Notes:

- **No action required** - Updates apply automatically on restart
- Battery SOC sensor will immediately show correct percentage
- If you previously had 0% SOC, it will now show actual battery charge level
- Historical data remains unchanged (new readings start from restart)

### Related Issues:

- Fixes #185 - SPH3-6k battery SOC showing 0% after upgrade
- User-confirmed: Register 31217 contains correct SOC value

---

# Release Notes - v0.5.5

## 🔧 Bug Fix - SPH 7-10kW Battery Sensor Fixes

This release applies the same battery sensor fixes from v0.5.1 (SPH 3-6kW) to the **SPH 7-10kW V2.01** profile, ensuring consistent and accurate battery monitoring across all SPH models.

### What Was Fixed:

**Problem:** SPH 7-10kW V2.01 users were experiencing the same battery sensor issues that were fixed for SPH 3-6kW in v0.5.1, but the fixes were never applied to the 7-10kW profile:
- Battery SOC showing 0% instead of actual value (e.g., should be 85%)
- Battery energy registers showing incorrect values
- AC charge energy sensor potentially showing garbage values

**Root Cause:**
The battery sensor fixes from v0.5.1 (commit 9c71de7) were only applied to SPH_3000_6000_V201 but not to SPH_7000_10000_V201, leaving 7-10kW users with the same issues.

### The Fix:

Applied all three fixes to **SPH_7000_10000_V201** profile:

**1. Battery SOC Fix:**
- Added register 1086 for battery_soc (BMS value)
- Overrides inherited register 17 which shows 0
- Provides correct SOC reading from battery management system

**2. Battery Energy Registers Fix:**
- Changed registers 31202-31203 from `battery_charge_power` to `battery_discharge_today` (energy)
- Added registers 31204-31205 for `battery_charge_total` (kWh)
- Added registers 31206-31207 for `battery_charge_today` (kWh)
- Added registers 31208-31209 for `battery_discharge_total` (kWh)
- Matches VPP Protocol V2.01 specification and real-world register data

**3. AC Charge Energy Fix:**
- Added register 115 for `ac_charge_energy_total`
- Prevents incorrect 32-bit pairing of registers 31220-31221
- Avoids garbage values like 70M+ kWh

### Impact:

- ✅ **SPH 7-10kW** battery SOC now shows correct percentage (was 0%)
- ✅ Battery energy tracking now accurate (charge/discharge today & total)
- ✅ AC charge energy sensor shows correct values
- ✅ **Full parity** with SPH 3-6kW fixes from v0.5.1

### Affected Models:

- SPH 7000-10000 V2.01 (single-phase hybrid with VPP protocol)

### Files Changed:

- `custom_components/growatt_modbus/profiles/sph.py`:
  - Line ~579: Added register 1086 (battery_soc from BMS)
  - Lines ~667-675: Fixed battery energy registers 31202-31209
  - Line ~686: Added register 115 (ac_charge_energy_total)

### Migration Notes:

- **No action required** - Updates apply automatically on restart
- Battery sensors will show correct values immediately
- Historical data remains unchanged (new readings start from restart)

---

# Release Notes - v0.5.4

## 🔧 Bug Fix & Enhancement - Register Scan Improvements (Issue #184)

This release improves the diagnostic register scan service to provide better visibility and reduce confusion when troubleshooting profile selection issues.

### What Was Fixed:

**Problem:** Users manually selecting a profile (e.g., "MIN TL-XH") would run the register scan service and see only the auto-detected profile (e.g., "MOD series") in the CSV output. This caused confusion because:
- The CSV only showed "Suggested Profile Key: mod_6000_15000tl3_xh" (auto-detected)
- It didn't show what profile the user had actually selected and was using
- Users thought the suggested profile was what they had configured

**Impact:**
- User's system was actually working correctly with the selected profile
- But they couldn't see this in the diagnostic output
- Led to confusion and unnecessary troubleshooting

### What's New:

#### 1. Currently Configured Profile Display

The register scan CSV now shows **both** the selected profile AND the auto-detected profile:

```csv
SCAN METADATA
Connection Type,TCP
Slave ID,1

CURRENTLY CONFIGURED PROFILE
Selected Profile,MIN TL-XH 3000-10000
Selected Profile Key,min_tl_xh_3000_10000_v201

DETECTION ANALYSIS
Detected Model,MOD Series 6000-15000TL3-XH
Suggested Profile Key,mod_6000_15000tl3_xh
```

This makes it clear:
- ✅ What profile you have configured and are currently using
- ✅ What profile the auto-detection suggests
- ✅ Whether there's a mismatch between selected and detected

#### 2. Current Entity Values Section

The register scan now includes a comprehensive snapshot of all current entity values from Home Assistant:

```csv
CURRENT ENTITY VALUES FROM INTEGRATION
Entity Name,Current Value
ac_current,5.234
ac_frequency,50.020
ac_power,1234.567
ac_voltage,230.123
battery_charge_power,0.000
battery_current,2.345
battery_power,567.890
battery_soc,85.000
battery_temp,None (unavailable)
battery_voltage,51.234
energy_today,12.345
grid_power,1234.567
house_consumption,567.890
pv1_current,6.789
pv1_power,1234.567
pv1_voltage,182.345
...
```

Features:
- ✅ Shows **all** entity values including zeros and unavailable
- ✅ Clearly marks unavailable values as "None (unavailable)"
- ✅ Alphabetically sorted for easy lookup
- ✅ Formatted for readability (floats to 3 decimals)

Benefits for debugging:
- Compare raw register values vs. processed entity values
- See complete snapshot of integration state at scan time
- Identify which values are zero vs. missing vs. unavailable
- Verify entity processing and calculations

### Files Changed:
- `custom_components/growatt_modbus/diagnostic.py`:
  - Added imports for profile display name functions
  - Extract currently selected profile from coordinator
  - Extract all current entity values from coordinator data
  - Display both sections in CSV before detection analysis

### Migration Notes:
- **No action required** - Enhancement is automatic
- Works when register scan finds a matching integration (same connection)
- If no integration found, shows detection analysis only (as before)

---

# Release Notes - v0.5.3

## 🔧 Bug Fix - Missing Battery BMS Temperature Register (Issue #184)

This release fixes an issue where register 3136 (battery BMS temperature) was undefined in MOD and MIN TL-XH profiles, causing incorrect sensor values in Home Assistant.

### What Was Fixed:

**Problem:** Users reported seeing duplicate/incorrect battery sensors:
- "Battery charging from mains power: **36.60 kWh**" (incorrect - actually a temperature!)
- "Boost Temperature: 0.0°C" (incorrect - register 95 reads 0)
- Missing battery BMS temperature sensor

**Root Cause:**
- Register 3136 was **not defined** in MOD 6000-15000TL3-XH and MIN TL-XH profiles
- Raw value: 366 (36.6 with ×0.1 scale)
- Integration misinterpreted this as **energy data** (36.60 kWh) instead of **temperature** (36.6°C)
- Register is in the 3000+ extended range used by both MOD and MIN profiles

**Additional Issue:**
- User had MIN 3000 TL-XH (single-phase) but auto-detection selected MOD profile (three-phase)
- Phase S/T registers all showed 0, confirming single-phase inverter
- Wrong profile caused incorrect register mappings and missing/duplicate sensors

**The Fix:**

Added missing battery BMS temperature register to both profiles:

1. **MOD 6000-15000TL3-XH Profile** (`profiles/mod.py`):
   - Register 96: `temp_sensor_1` (36.6°C - additional BMS/battery temperature)
   - Register 97: `temp_sensor_2` (32.7°C - matches Growatt server Boost Temp)
   - Register 3136: `battery_bms_temp` (36.6°C - battery BMS/module temperature)

2. **MIN TL-XH 3000-10000 Profile** (`profiles/tl_xh.py`):
   - Register 3136: `battery_bms_temp` (36.6°C - battery BMS/module temperature)

**Why Both Profiles:**
- Register 3136 is in the **3000+ extended range** shared by both MOD and MIN inverters
- Registers 96-97 are MOD-specific (0-124 base range, not used by MIN)
- Fix benefits both actual MOD users and users who should be using MIN profile

**Impact:**
- ✅ New sensor: "Battery BMS Temp" showing correct temperature (36.6°C)
- ✅ Removes incorrect "Battery charging from mains power: 36.60 kWh" sensor
- ✅ Properly identifies temperature vs energy data
- ✅ Fixes duplicate sensor issues for MOD/MIN TL-XH users

### 📋 Action Required:

**For users with MIN 3000 TL-XH inverters:**

1. **Update to v0.5.3**
2. **Reconfigure to correct profile:**
   - Go to: Settings → Devices & Services → Growatt
   - Click **Configure** on your inverter
   - Change profile to: **MIN TL-XH 3000-10000 (V2.01)**
   - Save and restart Home Assistant

3. **Verify after restart:**
   - ✅ "Battery BMS Temp" sensor appears (~36.6°C)
   - ❌ Incorrect "36.60 kWh" sensor removed
   - ✅ Battery power sensors still work correctly
   - ✅ Three-phase sensors (Phase S/T) hidden

**For users with actual MOD inverters:**
- Simply update to v0.5.3 and restart
- New temperature sensors will appear automatically

### Technical Details:

**Register Analysis from Scan (2026-03-09 14:12:43):**
- Register 96 (base range): 366 raw = 36.6°C
- Register 97 (base range): 327 raw = 32.7°C (matches Growatt server)
- Register 3136 (extended): 366 raw = 36.6°C
- Battery charging: 2.14kW (Growatt server), 1626W (register 3181) ✓ correct
- Phase S/T registers: All 0 → Single-phase → MIN profile needed

**Files Changed:**
- `custom_components/growatt_modbus/profiles/mod.py` (lines 77-78, 123)
- `custom_components/growatt_modbus/profiles/tl_xh.py` (line 312)

**Affected Models:**
- MOD 6000-15000TL3-XH (three-phase hybrid)
- MIN TL-XH 3000-10000 (single-phase hybrid)
- Any inverter using these profiles with battery BMS temperature at register 3136

**Detection Improvement Needed:**
- Auto-detection currently selects MOD for MIN inverters
- Future improvement: Check phase S/T registers to distinguish single vs three-phase

---

# Release Notes - v0.5.2

## 🔧 Critical Bug Fix - Integration Initialization Failure (Issue #188)

This release fixes a critical bug where the integration fails to initialize on inverters that don't support extended register ranges added in v0.5.0.

### What Was Fixed:

**Problem:** After upgrading to v0.5.*, some users reported:
- Integration stuck in "Initializing" state with constant retrying
- Error in logs: `ExceptionResponse(dev_id=1, function_code=132, exception_code=4)`
- Error message: `Modbus error reading input registers 3000-3078`
- Downgrading to v0.4.8 resolves the issue

**Root Cause:**
- In v0.5.0, registers 3071-3078 were added to SPH V2.01 profiles for load energy and grid export energy metrics
- These registers are in the MIN/MOD range (3000-3124) which not all inverters support
- When reading the 3000 range, inverters without these registers return Modbus exception code 4 (Slave Device Failure)
- The code treated this as a **fatal error** and aborted initialization by returning `None`
- This was inconsistent with how other register ranges (storage 1000-1124, business 875-999) handle failures

**The Fix:**

Changed 3000 range register read failure handling from fatal to graceful degradation:

1. **Non-Fatal Error Handling:**
   - Changed from `logger.error()` + `return None` to `logger.warning()` + continue
   - Matches the pattern used for storage and business register ranges
   - Allows initialization to complete even if extended registers aren't available

2. **Graceful Degradation:**
   - Inverters **with** extended registers: Get full data including load energy metrics
   - Inverters **without** extended registers: Work normally with core functionality
   - No user intervention required - automatic compatibility

**Impact:**
- ✅ Integration initializes successfully on all inverter models
- ✅ Fixes "stuck in Initializing" issue reported in #188
- ✅ Backward compatible with inverters lacking extended register support
- ✅ Forward compatible - still provides enhanced data when registers are available
- ✅ No configuration changes needed

### 📋 Action Required:

**For users experiencing initialization failures:**

1. **Update to v0.5.2**
2. **Restart Home Assistant**
3. **Verify integration initializes successfully:**
   - Integration should complete initialization within 30 seconds
   - No more "Initializing" stuck state
   - All supported sensors should appear and update normally

**No configuration changes needed** - fix is automatic after upgrade.

### Technical Details:

**Files Changed:**
- `custom_components/growatt_modbus/growatt_modbus.py:824-825`

**What Changed:**
- Modified `_read_registers()` method to handle 3000 range read failures gracefully
- Changed error handling from fatal (return None) to warning (continue)
- Inverters report Modbus exception code 4 when unsupported registers are requested
- Integration now continues with available data instead of aborting

**Affected Models:**
- All inverter models that don't support registers 3071-3078 (load energy, grid export in MIN/MOD range)
- Primarily affects inverters without VPP V2.01 protocol extended register support
- Fixes compatibility regression introduced in v0.5.0

## 🚀 Enhancement - MIC Auto-Detection Fix for Waveshare Adapters (Issue #187)

This release fixes auto-detection timeouts for MIC micro inverters when using Waveshare RS485-to-ETH adapters.

### What Was Fixed:

**Problem:** MIC 3000TLX users with Waveshare RS485-ETH adapters reported:
- Integration hangs at "off-grid inverter warning" screen during setup
- Setup takes ~10 minutes instead of completing immediately
- Logs show: `No response received after 3 retries` when reading register 30000
- Integration eventually times out and fails to initialize

**Root Cause:**
- MIC micro inverters use **legacy V3.05 protocol** (registers 0-179 only)
- Auto-detection was attempting to read VPP 2.01 register 30000 before checking legacy registers
- MIC doesn't support register 30000, causing long timeout with Waveshare adapters
- Legacy register detection (which includes MIC) only ran AFTER the VPP timeout

**The Fix:**

Added **early legacy register detection** before attempting VPP register reads:

1. **Quick Legacy Check (Step 1.5):**
   - Try reading register 3 (PV1 voltage) - exists in most legacy protocols
   - If register 3 responds, check if register 3003 is absent
   - Register 3 present + register 3003 absent = MIC series (0-179 range only)

2. **Skip VPP Detection:**
   - Once MIC is detected via legacy registers, skip reading register 30000
   - Prevents long timeout on unsupported VPP registers
   - Detection completes in <1 second instead of ~10 minutes

3. **Detection Order Updated:**
   - Step 1: OffGrid DTC (registers 34/43) - SPF detection
   - **Step 1.5: Legacy register check (NEW) - MIC detection**
   - Step 2: VPP DTC (register 30000) - V2.01 inverters
   - Step 3: Model name read
   - Step 4: Register probing (fallback)

**Impact:**
- ✅ MIC inverters detected immediately via legacy registers
- ✅ No timeout on unsupported VPP register 30000
- ✅ Setup completes in <1 second instead of ~10 minutes
- ✅ Works with all RS485-to-TCP adapters including Waveshare
- ✅ No impact on other inverter models

### 📋 Waveshare RS485-to-ETH Configuration

For users with Waveshare RS485-to-ETH adapters, use these settings:

**Connection Parameters:**
- **Baud Rate:** 9600
- **Data Bits:** 8
- **Parity:** None
- **Stop Bits:** 1
- **Port:** 502 (Modbus TCP standard)
- **Reset:** Off
- **Link:** On
- **Index:** Off
- **RFC2217 (Similar):** On

These settings are now documented in the README for reference.

### Technical Details:

**Files Changed:**
- `custom_components/growatt_modbus/auto_detection.py:923-945`
- `README.md:118-131` (added Waveshare configuration guide)

**Detection Logic:**
```python
# Before: VPP DTC read first → timeout on MIC
1. OffGrid DTC → VPP DTC → Model name → Register probing

# After: Legacy check before VPP → instant MIC detection
1. OffGrid DTC → Legacy check (MIC) → VPP DTC → Model name → Register probing
```

**Affected Models:**
- MIC 600-3300TL-X series (all micro inverters using 0-179 register range)
- Any legacy inverter using V3.05 protocol without VPP 2.01 support
- Particularly affects users with Waveshare RS485-to-ETH adapters

---

# Release Notes - v0.5.1

## 🔧 Bug Fixes - SPH Battery & Grid Energy Sensors

This release fixes critical sensor issues for SPH inverters including battery sensor inaccuracies and grid energy calculation errors.

### What Was Fixed:

**Problem:** SPH 3-6kW V2.01 users reporting incorrect battery sensor values (Issue #185):
- Battery SOC showing 0% instead of actual value (e.g., 31%)
- AC Charge Energy Total showing garbage value (70,516,736 kWh)
- Battery charge/discharge energy sensors showing incorrect or missing values

**Root Cause:**
- Register 17 (inherited from base profile) returns 0 for SOC on V2.01 inverters
- Correct SOC value is available in register 1086 (BMS register) but wasn't configured
- Battery energy registers in VPP range (31202-31209) were incorrectly mapped
- AC Charge Energy Total used wrong 32-bit register pairing (31220-31221)

**The Fix:**

1. **Added Correct Battery SOC Register:**
   - Added register 1086 for `battery_soc` in SPH 3-6kW V2.01 profile
   - Overrides inherited register 17 which returns 0
   - Provides accurate SOC value directly from BMS

2. **Fixed Battery Energy Register Mappings:**
   - Changed registers 31202-31203 from power to discharge_today energy
   - Added registers 31204-31205 for battery_charge_total
   - Added registers 31206-31207 for battery_charge_today
   - Added registers 31208-31209 for battery_discharge_total
   - All battery energy tracking now accurate

3. **Fixed AC Charge Energy Total:**
   - Removed incorrect 32-bit pairing of registers 31220-31221
   - Added register 115 for `ac_charge_energy_total`
   - Prevents garbage value of 70,516,736 kWh

**Impact:**
- ✅ Battery SOC now shows correct value (e.g., 31% instead of 0%)
- ✅ AC Charge Energy Total shows realistic value (e.g., 7.8 kWh instead of 70M kWh)
- ✅ Battery charge/discharge energy sensors now accurate
- ✅ Complete battery monitoring for SPH 3-6kW V2.01 users

---

## 🔧 Bug Fix - SPH-TL3 Grid Import Energy Calculation (Issue #183)

This release fixes incorrect grid import energy values for SPH-TL3 inverters where the energy sensor would show decreasing values or incorrect totals.

### What Was Fixed:

**Problem:** SPH-TL3 users reporting incorrect grid import energy:
- Grid import energy showing values that decrease when solar production starts
- Calculated values significantly different from actual grid consumption
- Energy meters not reflecting true grid import

**Root Cause:**
- SPH-TL3 has hardware registers for grid import energy (energy_to_user_today at 1044-1045 and energy_to_user_total at 1046-1047)
- Code was checking for energy_from_grid_today/total which don't exist on SPH-TL3
- This caused fallback to calculation: `import = load - solar + export`
- Calculation was **incorrect for hybrid inverters** because `solar` (energy_today) includes both PV generation AND battery discharge
- When solar production increased, calculated import energy would decrease (mathematically incorrect)

**The Fix:**

Modified sensor.py to check for energy_to_user_today/total registers and use them directly when available:

1. **Added Hardware Register Support:**
   - Check for registers 1044-1045 (`energy_to_user_today`) for daily grid import
   - Check for registers 1046-1047 (`energy_to_user_total`) for total grid import
   - Use hardware meter readings directly instead of calculation

2. **Improved CT Clamp Handling:**
   - Normal orientation + hardware register: use energy_to_user directly
   - CT clamp backwards + hardware register: use energy_to_grid (swapped)
   - No hardware register available: fall back to calculation (MIN series, etc.)

3. **Accurate Grid Import Tracking:**
   - Values now come directly from hardware meter
   - No dependency on PV production or battery discharge calculations
   - Grid import energy never decreases incorrectly

**Impact:**
- ✅ SPH-TL3 grid import energy now accurate from hardware registers
- ✅ Values stable and don't decrease when solar production starts
- ✅ Proper handling of CT clamp orientation (normal vs backwards)
- ✅ Fallback calculation still works for inverters without hardware registers
- ✅ Fixes issue #183

### 📋 Action Required for SPH Users:

**For SPH 3-6kW V2.01 inverters:**

1. **Update to v0.5.1**
2. **Restart Home Assistant**
3. **Verify sensors show correct values:**
   - Battery SOC should show actual percentage (not 0%)
   - AC Charge Energy Total should be realistic (not millions of kWh)
   - Battery energy today/total sensors should update properly

**For SPH-TL3 inverters:**

1. **Update to v0.5.1**
2. **Restart Home Assistant**
3. **Verify grid import energy:**
   - Grid import energy should be stable and accurate
   - Values should not decrease when solar production increases
   - Energy readings should match your actual grid consumption

**No configuration changes needed** - fixes are automatic after upgrade.

### Technical Details:

**Files Changed:**
- `custom_components/growatt_modbus/profiles/sph.py` (SPH 3-6kW battery sensors)
- `custom_components/growatt_modbus/sensor.py` (SPH-TL3 grid energy calculation)

**SPH 3-6kW Battery Fix - Registers Added/Modified:**
- 1086: `battery_soc` (overrides register 17)
- 115: `ac_charge_energy_total` (replaces incorrect 31220-31221 pair)
- 31202-31203: `battery_discharge_today` (was incorrectly mapped as power)
- 31204-31205: `battery_charge_total` (newly added)
- 31206-31207: `battery_charge_today` (newly added)
- 31208-31209: `battery_discharge_total` (newly added)

**SPH-TL3 Grid Energy Fix - Registers Used:**
- 1044-1045: `energy_to_user_today` (daily grid import from hardware meter)
- 1046-1047: `energy_to_user_total` (total grid import from hardware meter)
- Fallback calculation for inverters without hardware registers (MIN series, etc.)

**Affected Models:**
- **Battery sensor fix:** SPH 3000-6000 (V2.01 protocol only)
- **Grid energy fix:** SPH-TL3 (all versions with hardware meter registers)
- Does not affect SPH 7-10kW or other SPH models

---

## ⚠️ Known Issue - MIC-1000TL-X Profile Selection (Issue #130)

Some MIC-1000TL-X inverters (firmware "PV 1000") may show zero values for AC power, energy today, energy total, AC current, and AC frequency when using the "MIC 600-3300TL-X (V2.01)" profile.

### Problem:

MIC-1000TL-X inverters can have **two different register layouts**:

1. **Standard layout** (0-179 range): AC data at registers 11-12, 26-27
2. **Hybrid MIN layout** (0-124 + 3000-3124 range): AC data at registers 3028-3029, 3049-3050

If you selected "MIC 600-3300TL-X (V2.01)" but your inverter uses the hybrid MIN layout, the integration will read the wrong registers and show zeros.

### Solution:

1. Go to **Settings → Devices & Services → Integrations**
2. Find your **Growatt Modbus** integration
3. Click **Configure**
4. Change **Inverter Series** to: **MIC 1000-6000TL-X (MIN range)**
5. Click **Submit**
6. Restart Home Assistant

After restart, all sensors should show correct values.

### How to Identify if You Need This:

- **Inverter model:** MIC-1000TL-X (or similar MIC models 1-3.3kW)
- **Firmware:** "PV 1000" or similar
- **Symptoms:** AC power = 0, Energy today = 0, but PV power shows correct values
- **Profile needed:** MIC 1000-6000TL-X (MIN range)

**Note:** The profile name says "1000-6000" but works for all MIC inverters (including MIC-1000TL-X) that use the hybrid MIN register layout. The auto-detection should select this automatically, but if you manually selected a profile, you may need to change it.

---

# Release Notes - v0.5.0

## 🔧 Critical Bug Fix - Diagnostic DTC Detection

This release fixes a critical bug in the diagnostic scanner that caused incorrect profile suggestions for VPP 2.01 inverters.

### What Was Fixed:

**Problem:** Diagnostic scanner incorrectly overriding DTC-based detection with register-based detection:
- DTC code would correctly identify inverter model (e.g., DTC 3501 = SPH 3-6kW)
- Register-based detection would then override with wrong model (e.g., SPH 8-10kW HU)
- Users ended up with wrong profile selection, causing missing or incorrect sensors

**Root Cause:**
- Diagnostic scanner performed DTC detection first
- Then continued to register-based detection logic
- Register-based detection would override correct DTC mapping
- Example: SPH 3-6kW V2.01 has storage range (1000+) which triggered HU detection

**The Fix:**
- Added early exit after successful DTC detection
- Register-based detection now only runs if DTC detection fails
- DTC detection takes priority as most reliable method

**Impact:**
- ✅ DTC 3501 (SPH 3-6kW) now correctly suggests `sph_3000_6000_v201` instead of `sph_8000_10000_hu`
- ✅ All VPP 2.01 inverters with valid DTC codes get correct profile suggestions
- ✅ Battery sensors work correctly with proper profile

### 📋 Action Required for Existing Users:

If you previously ran the diagnostic scanner and it suggested the **wrong profile**, you need to update your configuration:

**Symptoms of wrong profile:**
- Missing battery sensors
- Incorrect power readings
- Diagnostic showed different model than what you selected

**How to Fix:**

1. **Update to v0.5.0**
2. **Re-run diagnostic scanner** (it will now show correct profile)
3. **Update your integration configuration:**
   - Go to: **Settings → Devices & Services → Integrations**
   - Find **Growatt Modbus** integration
   - Click **Configure**
   - Change **Inverter Series** to match diagnostic suggestion
   - Click **Submit**
4. **Restart Home Assistant**

**Common Corrections:**
- DTC 3501/3502: Change from `SPH 8-10kW HU` → `SPH 3-6kW (V2.01)`
- DTC 3501/3502: Change from `SPH 7-10kW` → `SPH 3-6kW (V2.01)`

### Technical Details:

**File Changed:** `diagnostic.py`

**Code Added:**
```python
# If DTC detected model, skip other detection logic
if detection["confidence"] == "Very High":
    return detection
```

This ensures DTC-based detection (confidence = "Very High") takes priority and prevents register-based detection from overriding the correct profile.

**Affected DTC Codes:**
- 3501, 3502, 3735 (SPH/SPA 3-6kW)
- 3601, 3725 (SPH/SPA TL3)
- 5100 (TL-XH)
- 5200, 5201 (MIN/MIC)
- 5400 (MOD-XH/MID-XH)
- 5603, 5601, 5800 (WIT/WIS)

---

# Release Notes - v0.4.9

## 🔧 Bug Fixes + ✨ New Features + 🎯 WIT/SPH Enhancements

This release combines all improvements from beta versions (v0.4.9b1-b4) plus additional bug fixes.

**Fixed:**
- Battery power sign inversion for VPP protocol registers (1013-1014 swapped)
- Missing energy and battery registers in SPH V2.01 profiles (Issue #176)
- Multiple inverters on same IP rejected with "already configured" (Issue #179)
- SPH TL3 Energy Today showing AC output instead of PV production (Issue #172)

**Added:**
- Multi-register write support for advanced Modbus operations
- WIT VPP battery control entities and services (PR #171)
- WIT VPP export limitation controls (30200/30201 registers, PR #175)
- WIT VPP V2.03 register definitions (TOU schedule, SOC limits, system time)
- Grid power sensor improvement using power_to_user register (PR #170)
- Register scan now includes holding registers in CSV output
- New `get_register_data` service for programmatic register reads

---

## What's New in v0.4.9:

### 1. 🔋 Fixed Battery Power Sign for VPP Protocol Registers

**Problem:** VPP protocol inverters (WIT, SPH V2.01) showing inverted battery power signs:
- Battery charging (power should be positive) showed negative values
- Battery discharging (power should be negative) showed positive values
- Caused confusion in energy monitoring and automation

**Root Cause:**
- VPP protocol stores battery power in registers 1013-1014 in **swapped order**
- Register 1013: Low word (W)
- Register 1014: High word (kW)
- Integration was reading them as 1014+1013 (reversed), causing sign inversion

**The Fix:**
- Registers 1013-1014 now read in correct order for VPP protocol profiles
- Battery power signs now match physical behavior:
  - **Positive = Charging** (power going INTO battery)
  - **Negative = Discharging** (power coming OUT of battery)
- Affects: WIT, SPH V2.01, and other VPP protocol inverters

**Impact:**
- ✅ Battery power values now show correct sign
- ✅ Automation triggers work as expected
- ✅ Energy flow visualization accurate

### 2. 🔋 Added Missing Registers to SPH V2.01 Profiles (Issue #176)

**Added to SPH V2.01:**
- Battery registers: SOC, voltage, current, power, temperature, discharge limits
- Energy registers: Battery charge/discharge energy (today & total)
- Complete battery monitoring for SPH inverters using VPP protocol

**Impact:**
- ✅ SPH V2.01 users now have full battery monitoring
- ✅ Battery charge/discharge energy tracking available
- ✅ Complete parity with SPH TL3 legacy profile features

### 3. 🔧 Fixed Unique ID Collision for Multiple Inverters (Issue #179)

**Problem:** Multiple inverters on same IP (different ports) could not be configured:
- Common with Modbus proxy/gateway setups
- Second inverter rejected: "This inverter is already configured"

**Root Cause:**
- TCP unique ID format was: `{host}_{slave_id}` (ignored port number)
- Multiple inverters on same IP with different ports generated identical unique IDs

**The Fix:**
- Changed TCP unique ID format to: `{host}:{port}_{slave_id}`
- Example: `192.168.168.4:5021_1` vs `192.168.168.4:5022_1`

**Impact:**
- ✅ Multiple inverters on same IP with different ports now supported
- ✅ Modbus proxy/gateway setups work correctly
- ✅ Still prevents true duplicates (same IP+port+slave_id)

### 4. 🔧 Fixed SPH TL3 Energy Today (Issue #172)

**Problem:** SPH TL3 "Energy Today" showing AC output instead of true PV production:
- DC-coupled battery charging excluded from total
- Reported values significantly lower than actual solar production

**The Fix:**
- Added per-MPPT PV energy registers (59-60, 63-64, 91-92) to SPH TL3 profile
- Energy Today now calculated as: **PV1 + PV2** (true solar production)
- Same fix previously applied to WIT profile in v0.4.7

**Impact:**
- ✅ Energy Today shows accurate total PV production
- ✅ Values include DC-coupled battery charging
- ✅ Consistent with WIT behavior

### 5. ✨ Multi-Register Write Support (PR #168)

**Added:** Ability to write multiple registers in a single Modbus transaction
- New `write_multiple_registers` method in GrowattModbus class
- Improved error reporting with detailed Modbus exception handling
- Atomic multi-register writes for complex settings

**Use Cases:**
- Setting TOU schedules (multiple time/power registers)
- Batch configuration updates
- Advanced inverter programming

### 6. 🎯 WIT VPP Battery Control Enhancements (PR #171)

**Added:**
- WIT VPP battery control entities (charge/discharge power, duration)
- Service handlers for programmatic battery control
- Remote control enable/disable functionality
- Integration with VPP protocol time-limited overrides

**New Entities:**
- Remote Power Control Enable (register 30407)
- Remote Charging Time (register 30408, duration in minutes)
- Remote Charge/Discharge Power (register 30409, -100% to +100%)

### 7. 🎯 WIT VPP Export Limitation (PR #175)

**Added:**
- VPP export limitation control registers (30200/30201)
- Enable/disable export limiting
- Set maximum export power to grid

**Use Cases:**
- Comply with grid connection agreements
- Prevent export during peak pricing
- Dynamic export control based on conditions

### 8. 📊 WIT VPP V2.03 Register Additions (PR #169)

**Added:**
- TOU (Time of Use) schedule registers
- SOC (State of Charge) limit registers
- System time registers
- Enhanced VPP protocol support

### 9. 🔌 Grid Power Sensor Improvement (PR #170)

**Changed:** Grid power calculation now uses `power_to_user` register
- More accurate grid import/export measurements
- Better handling of CT clamp configurations
- Improved power flow calculations

### 10. 🛠️ Enhanced Services and Diagnostics

**Added:**
- `get_register_data` service for programmatic register reads
- Holding registers now included in register scan CSV output
- Better integration with automation and scripts

---

## Migration Notes:

**No action required** - This is a bug fix and enhancement release.

**For VPP Protocol Users (WIT, SPH V2.01):**
- Battery power signs will flip after upgrade (this is the fix - values are now correct)
- **Positive = Charging**, **Negative = Discharging**
- Update any automations that relied on the incorrect sign behavior

**For SPH TL3 Users:**
- Energy Today values will increase (now showing true PV production)
- Dashboard graphs may show a step change (expected - previous values were too low)

**For SPH V2.01 Users:**
- Battery sensors will now appear after upgrade
- Full battery monitoring now available

**For Multi-Inverter Setups (Issue #179):**
- If you couldn't add a second inverter on same IP, try adding it again after upgrade
- Both inverters will now configure successfully

**For WIT Users:**
- New battery control and export limitation features available
- See PR documentation for usage examples
- Rate limiting (30s cooldown) applies to control writes

---

## Files Changed:

Core functionality:
- `custom_components/growatt_modbus/growatt_modbus.py` - Battery power sign fix, multi-register write support, enhanced services
- `custom_components/growatt_modbus/config_flow.py` - Updated TCP unique_id format
- `custom_components/growatt_modbus/services.yaml` - Added get_register_data service
- `custom_components/growatt_modbus/select.py` - VPP export limitation
- `custom_components/growatt_modbus/diagnostic.py` - Enhanced register scanning

Profile updates:
- `custom_components/growatt_modbus/profiles/sph_tl3.py` - Added per-MPPT energy registers
- `custom_components/growatt_modbus/profiles/sph_v201.py` - Added battery and energy registers
- `custom_components/growatt_modbus/profiles/wit.py` - VPP control registers, export limitation

Version bump:
- `custom_components/growatt_modbus/manifest.json` - Version 0.4.9
- `README.md` - Version badge updated to 0.4.9
- `RELEASENOTES.md` - Updated with v0.4.9 changes

---

# Release Notes - v0.4.9b4 (Pre-Release)

## 🔧 Bug Fix - Multiple Inverters on Same IP

**Fixed (Issue #179):**
- Multiple inverters on the same IP address (different ports) could not be configured
- Integration rejected second inverter with "This inverter is already configured"
- Common scenario with Modbus proxies/gateways exposing multiple inverters

---

### What's Fixed in v0.4.9b4:

#### 🔧 Fixed Unique ID Collision for Same-IP Multi-Inverter Setups (Issue #179)

**Problem:** Users with multiple inverters behind a Modbus proxy or gateway (same IP, different ports) could only configure one inverter. The second would fail with "This inverter is already configured."

**Root Cause:**
- TCP unique ID format was: `{host}_{slave_id}`
- Ignored the port number completely
- Multiple inverters on same IP with different ports generated identical unique IDs

**User Case (Issue #179):**
- Setup: 2 inverters → Waveshare → evcc → ModbusProxy
- SPH 10k TL3 BH-UP: `192.168.168.4:5021` (slave 1)
- MOD 10k TL3-XH: `192.168.168.4:5022` (slave 1)
- Both generated unique_id: `192.168.168.4_1` ❌ **COLLISION!**
- Only first inverter could be added

**The Fix:**

Changed TCP unique ID format to include port number:
- **Old format:** `{host}_{slave_id}` (e.g., `192.168.168.4_1`)
- **New format:** `{host}:{port}_{slave_id}` (e.g., `192.168.168.4:5021_1`)

**Impact:**
- ✅ Multiple inverters on same IP with different ports now supported
- ✅ Common Modbus proxy/gateway setups now work correctly
- ✅ Still prevents true duplicates (same IP+port+slave_id)
- ✅ Serial connections unchanged

**Example - Now Works:**
```
Configuration:
  SPH 10k TL3:  192.168.168.4:5021 slave_id=1 → unique_id: 192.168.168.4:5021_1 ✅
  MOD 10k TL3:  192.168.168.4:5022 slave_id=1 → unique_id: 192.168.168.4:5022_1 ✅

Still Blocks Duplicates:
  First:   192.168.168.4:502 slave_id=1 → unique_id: 192.168.168.4:502_1 ✅ (allowed)
  Second:  192.168.168.4:502 slave_id=1 → unique_id: 192.168.168.4:502_1 ❌ (blocked - true duplicate)
```

---

### Migration Notes:

**No action required for existing single-inverter setups** - unique IDs will update automatically.

**For Multi-Inverter Setups (Issue #179):**
- If you previously couldn't add a second inverter on the same IP:
  1. Upgrade to v0.4.9b4
  2. Try adding the second inverter again
  3. Both inverters will now configure successfully

**Technical Note:**
- Existing integrations will get new unique IDs on next restart
- Home Assistant handles unique ID changes automatically
- No need to remove/re-add existing integrations

---

### Files Changed:
- `custom_components/growatt_modbus/config_flow.py` - Updated TCP unique_id format to include port
- `custom_components/growatt_modbus/manifest.json` - Version bump to 0.4.9b4
- `README.md` - Version badge updated to 0.4.9b4
- `RELEASENOTES.md` - Updated with v0.4.9b4 changes

---

# Release Notes - v0.4.9b3 (Pre-Release)

## 🔧 Bug Fix - SPH TL3 Energy Today Incorrect Values

**Fixed (Issue #172):**
- SPH TL3 "Energy Today" sensor showing AC output energy instead of true PV solar production
- On hybrid inverters with batteries, DC-coupled battery charging was excluded from the total

---

### What's Fixed in v0.4.9b3:

#### 🔧 Fixed SPH TL3 Energy Today Calculation (Issue #172)

**Problem:** SPH TL3 users reported "Energy Today" showing significantly lower values than actual solar production. For example, a user producing ~8.1 kWh saw only 1.5-2.6 kWh reported.

**Root Cause:**
- Registers 53-54 (`energy_today`) on SPH TL3 measure **total AC output energy** (what goes to grid/loads)
- On hybrid inverters with batteries, energy that goes directly from PV to battery via DC coupling **bypasses the AC side** and is NOT counted in registers 53-54
- This means the "Energy Today" sensor was underreporting by the amount of DC-coupled battery charging

**User Case:**
- SPH TL3 inverter with battery
- Register 54 = 15 → 1.5 kWh (AC output only)
- Registers 60 (PV1) + 64 (PV2) = actual total PV production (~8.1 kWh)
- Difference = energy going directly to battery via DC coupling

**The Fix:**

1. **Added Per-MPPT PV Energy Registers to SPH TL3 Profile:**
   - 59-60: `pv1_energy_today` (PV string 1 DC energy production)
   - 63-64: `pv2_energy_today` (PV string 2 DC energy production)
   - 91-92: `pv_energy_total` (lifetime total PV energy from all MPPTs)

2. **Automatic Calculation:**
   - Existing code already sums PV1 + PV2 when per-MPPT registers are available
   - `energy_today` now calculated as: **PV1 + PV2** (true solar production)
   - Same approach already working correctly for WIT profile (Issue #146 fix in v0.4.7)

**Impact:**
- Energy Today now shows accurate total PV production (DC input from solar panels)
- Values include energy going to battery via DC coupling (previously excluded)
- Energy Total (lifetime) now uses PV energy total register for accuracy
- Other inverter profiles unaffected (backwards compatible)

**Example - Before vs After:**
```
Before (v0.4.9b1):
  Energy Today: 1.5 kWh  (AC output only, missing DC battery charging)

After (v0.4.9b3):
  Energy Today: 8.1 kWh  (PV1 + PV2 = true solar production)
```

---

### Migration Notes:

**No action required** - Fix is automatic after upgrade.

**For SPH TL3 Users:**
- "Energy Today" will now show higher (correct) values that include DC battery charging
- Dashboard energy graphs may show a one-time step change after upgrade - this is expected
- Previous values excluded DC-coupled battery charging (incorrect), new values are PV-only production (correct)

---

### Files Changed:
- `custom_components/growatt_modbus/profiles/sph_tl3.py` - Added per-MPPT PV energy registers (59-60, 63-64, 91-92)
- `custom_components/growatt_modbus/manifest.json` - Version bump to 0.4.9b3
- `README.md` - Version badge updated to 0.4.9b3
- `RELEASENOTES.md` - Updated with v0.4.9b3 changes

---

# Release Notes - v0.4.8

## 🔧 Bug Fix - MIC-1000TL-X Auto-Detection

**Fixed (Issue #130):**
- MIC-1000TL-X inverters incorrectly auto-detected as MIN series
- Manual MIC profile selection showed incorrect/missing values

---

### What's Fixed in v0.4.8:

#### 🔍 Improved MIC vs MIN Detection (Issue #130)

**Problem:**
- DTC code 5200 is shared by both MIC and MIN inverter series
- Previous logic tested for 3000+ register range to distinguish models
- Some MIC-1000TL-X inverters use MIN register layout (hybrid design) but are physically MIC hardware
- This caused incorrect auto-detection and wrong sensor values

**Root Cause:**
- MIC-1000TL-X (2500-6000W range) can use either:
  - Standard MIC layout: 0-179 registers only
  - Hybrid layout: 0-124 + 3000-3124 (MIN addressing) BUT with MIC features
- Previous detection tested register 3003 (MIN PV1 voltage)
- If found → assumed MIN series ❌
- If not found → assumed MIC series ✅

**User Case:**
- MIC-1000TL-X with firmware "PV 1000"
- Has data in BOTH 0-124 AND 3000-3124 ranges (hybrid layout)
- Previous detection saw 3000+ range → incorrectly selected MIN profile
- MIN profile missing MIC-specific per-MPPT energy registers (59-62)
- Result: Wrong/missing sensor values

**The Fix:**

1. **Hardware-Level Detection:**
   - MIC inverters have per-MPPT energy tracking capability (registers 59-62)
   - MIN inverters do NOT have these registers (not a firmware feature - hardware difference)
   - Now test registers 59-62 FIRST before checking register range

2. **New Detection Logic for DTC 5200:**
   ```
   Step 1: Read registers 59-62 (PV1/PV2 per-MPPT energy)

   Step 2: Validate if values are plausible energy data:
           - MIC hardware: registers contain valid energy values (high word 0-100)
           - MIN hardware: registers return garbage/system values (e.g., 5200 = DTC code)
           - Check: high word < 100 (rejects invalid data like DTC codes)

   Step 3: If valid energy data found in registers 59-62:
           → MIC hardware detected
           → Check if uses MIN layout (3000+ range)
           → If yes: Use new MIC_2500_6000TL_X_MIN_RANGE profile
           → If no: Use standard MIC_600_3300TL_X_V201 profile

   Step 4: If registers 59-62 empty or invalid:
           → MIN hardware (no per-MPPT capability or garbage data)
           → Use MIN_3000_6000TL_X_V201 profile
   ```

3. **New MIC Profile Created:**
   - Profile: `MIC_2500_6000TL_X_MIN_RANGE`
   - Supports hybrid MIC inverters using MIN register addressing
   - Combines:
     - MIN 0-124 register range (basic data)
     - MIN 3000-3124 register range (AC power, energy)
     - MIC per-MPPT registers 59-62 (PV1/PV2 energy tracking)
   - Provides complete sensor coverage for these hybrid models

**Impact:**
- ✅ MIC-1000TL-X correctly auto-detected regardless of register layout
- ✅ All sensors show correct values
- ✅ Per-MPPT energy tracking available for MIC users
- ✅ MIN detection unaffected (backwards compatible)
- ✅ Reliable hardware-level differentiation (not just register addressing)

**Example - Before vs After:**
```
Before (v0.4.7):
  Auto-Detection: MIN 3000-6000TL-X ❌ (wrong - saw 3000+ range)
  AC Power: 1127 W ✅ (worked from 3000+ range)
  Energy Today: 0.1 kWh ❌ (wrong - MIN profile missing PV1/PV2 registers)
  PV1 Energy: Not available ❌ (MIN profile doesn't define register 59-60)

After (v0.4.8):
  Auto-Detection: MIC 2500-6000TL-X (MIN range) ✅ (correct - saw registers 59-62)
  AC Power: 1127 W ✅ (from 3000+ range)
  Energy Today: 0.1 kWh ✅ (correct - using per-MPPT registers)
  PV1 Energy: 0.1 kWh ✅ (now available from register 59-60)
  PV2 Energy: 44927.0 kWh ✅ (now available from register 61-62)
```

---

### Technical Details:

**Register Scan Analysis:**
```
MIC-1000TL-X Hybrid Layout (verified):
  Register 11-12: 0 (MIC AC power location - empty)
  Register 35-36: 1127 (output power - populated)
  Register 59-60: 1/1 (PV1 energy - VALID energy data ✅)
  Register 61-62: 44927/0 (PV2 energy - VALID energy data ✅)
  Register 3028-3029: 1127 (MIN AC power location - populated)
  Register 3049-3052: energy values (MIN location - populated)

MIN 3000-6000TL-X (verified):
  Register 59: 5200 (garbage/DTC code - INVALID for energy ❌)
  Register 59-62: Returns system values, not energy data
  → Detection rejects high word >= 100 as garbage
```

**Validation Logic:**
- Energy registers use 32-bit pairs (high word, low word)
- Valid daily energy: 0-50 kWh → high word typically 0-1
- Valid lifetime energy: 10,000 kWh → high word ~1-2
- **Threshold: high word must be < 100 to be valid energy**
- MIN garbage values (5200, DTC codes, etc.) correctly rejected

**Key Insight:** Registers 59-62 differentiate MIC/MIN at hardware level. MIN may respond to these registers but returns garbage/system values, not energy data.

---

### Migration Notes:

**No action required** - Auto-detection improvement only.

**For Affected MIC-1000TL-X Users (Issue #130):**
- If previously manually selected MIN profile as workaround:
  1. Remove integration
  2. Re-add integration with auto-detection
  3. Inverter will now correctly detect as MIC
  4. All sensors (including per-MPPT energy) will appear

**Detection Changes:**
- MIC inverters with hybrid layout now correctly identified
- All existing MIC and MIN inverters unaffected
- More robust detection using hardware capabilities instead of register addressing

---

# Release Notes - v0.4.7

## 🐛 Bug Fix + 📊 Diagnostic Enhancement

**Fixed (Issue #146):**
- WIT "Energy Today" sensor showing incorrect values (total system output instead of PV-only production)
- WIT "Energy Total" sensor not reflecting actual solar panel production

**Enhanced:**
- Register scan now includes firmware version in metadata output

---

### What's Fixed in v0.4.7:

#### 1. 🔧 Fixed WIT PV Energy Calculation (Issue #146)

**Problem:** WIT users reported "Energy Today" sensor increasing at night when no solar production occurring.

**Root Cause:**
- Registers 53-56 (energy_today/total) track **total system AC output** (PV + battery discharge combined)
- Not suitable for tracking solar production on hybrid inverters with batteries
- Values increase whenever battery powers loads, even at night

**User Report:**
- Register 56 showed 6.2 kWh (wrong - total system output)
- Register 60 (PV1): 4.8 kWh ✅
- Register 64 (PV2): 2.7 kWh ✅
- **Actual PV production: 4.8 + 2.7 = 7.5 kWh** ✅

**The Fix:**
1. **Added Missing Registers to WIT Profile:**
   - 59-60: PV1 Energy Today (per-MPPT tracking)
   - 63-64: PV2 Energy Today (per-MPPT tracking)
   - 91-92: PV Energy Total (lifetime DC input from all MPPTs)

2. **Added Dataclass Fields:**
   - `pv1_energy_today` - PV1 MPPT daily production
   - `pv2_energy_today` - PV2 MPPT daily production
   - `pv_energy_total` - Lifetime PV production

3. **Changed Energy Calculation for WIT:**
   - `energy_today` now calculated as: **PV1 + PV2** (true solar production)
   - `energy_total` now uses register 92 (total PV lifetime energy)
   - Fallback to original registers for non-WIT inverters (backwards compatible)

**Impact:**
- ✅ WIT "Energy Today" now shows accurate solar production (not total system output)
- ✅ Values only increase during daylight when panels are producing
- ✅ Correctly tracks DC input from solar panels only
- ✅ Other inverter series unaffected (backwards compatible)

**Example - Before vs After:**
```
Before (v0.4.6):
  Energy Today: 6.2 kWh  ❌ (total system including battery)

After (v0.4.7):
  Energy Today: 7.5 kWh  ✅ (PV1 4.8 + PV2 2.7 = actual solar)
```

#### 2. 📊 Register Scan Enhancement

**Added:** Firmware version now included in register scan metadata output.

**How it Works:**
- Reads holding registers 9-11 (firmware version, ASCII encoded)
- Decodes to human-readable version string
- Displays in both CSV metadata and notification message

**Example Output:**
```
DETECTION ANALYSIS
Detected Model: WIT 4-15kW Hybrid
Confidence: Very High
DTC Code: 10046
Protocol Version: V2.01
Firmware: GH1.0     <-- NEW
Suggested Profile: WIT_4000_15000TL3
```

**Impact:**
- ✅ Easier troubleshooting - firmware version visible in scans
- ✅ Helps identify firmware-specific behaviors
- ✅ No additional user action required - automatic extraction

---

### Migration Notes:

**No action required** - This is a bug fix and enhancement release.

**For WIT Users:**
- "Energy Today" and "Energy Total" sensors will now show correct PV production values
- **IMPORTANT:** Values may differ from v0.4.6 - this is expected and correct
- Previous values included battery discharge (wrong), new values are PV-only (correct)
- Dashboard energy graphs may show a one-time step change after upgrade

**For All Users:**
- Next register scan will include firmware version automatically
- No changes needed to existing scans

---

### Files Changed:
- `custom_components/growatt_modbus/profiles/wit.py` - Added PV energy registers (59-60, 63-64, 91-92) with descriptions
- `custom_components/growatt_modbus/growatt_modbus.py` - Added PV energy dataclass fields + reading code + smart calculation logic
- `custom_components/growatt_modbus/diagnostic.py` - Added firmware version reading and display
- `custom_components/growatt_modbus/manifest.json` - Version bump to 0.4.7
- `README.md` - Version badge updated to 0.4.7
- `RELEASENOTES.md` - Updated with v0.4.7 changes

---

# Release Notes - v0.4.6

## 🐛 Bug Fixes + 🎯 WIT Control Stability Improvements

**Fixed (Issue #163):**
- SPF AC Charge Energy Today/Total sensors showing 0.00 (should show same values as Battery Charge sensors)
- SPF AC Discharge Energy Today/Total sensors showing 0.00 (registers 64-67)
- Noisy WARNING log message for SPF users: "load_energy_today_low register not found"

**Improved (Issue #143):**
- WIT control stability - prevent oscillation and unstable battery behavior
- WIT control model clarified - VPP protocol vs Legacy protocol differences
- Rate limiting added to prevent rapid control changes
- Control conflict detection for TOU vs remote control scenarios

---

### What's Fixed in v0.4.6:

#### 1. 🔧 Fixed SPF AC Charge/Discharge Energy Sensors

**Root Cause:** SPF uses different register names than WIT for the same energy measurements, causing "AC Charge/Discharge Energy" sensors to show 0.00 even though the data exists.

**Register Name Differences:**
- **WIT:** Uses `ac_charge_energy_*` and `ac_discharge_energy_*` register names
- **SPF:** Uses `charge_energy_*` (56-59) and `ac_discharge_energy_*` (64-67) register names
- Same data, different naming convention

**Affected sensors (now fixed):**
- `ac_charge_energy_today` - Now populated from SPF's `charge_energy_today` (registers 56-57)
- `ac_charge_energy_total` - Now populated from SPF's `charge_energy_total` (registers 58-59)
- `ac_discharge_energy_today` - Now reads from registers 64-65
- `ac_discharge_energy_total` - Now reads from registers 66-67

**The Fix:**
1. **AC Charge Energy**: SPF now populates BOTH `charge_energy_*` AND `ac_charge_energy_*` fields from the same registers (56-59)
2. **AC Discharge Energy**: Added missing register reading code for registers 64-67
3. **WIT compatibility**: WIT-specific register names still work for WIT inverters

**Impact:**
- ✅ SPF users will now see actual values in ALL "AC Charge/Discharge Energy" sensors
- ✅ "AC Charge Energy" sensors will match "Battery Charge" sensors (same data source)
- ✅ "AC Discharge Energy" sensors will show battery → load energy flow
- ✅ Complete energy tracking for SPF 6000 ES Plus and similar models

**What You'll See After Upgrade (SPF users):**
- "Battery Charge Today" = 0.80 kWh ✅ (working before)
- "AC Charge Energy Today" = 0.80 kWh ✅ (NOW FIXED - was 0.00)
- "Battery Charge Total" = 446.90 kWh ✅ (working before)
- "AC Charge Energy Total" = 446.90 kWh ✅ (NOW FIXED - was 0.00)
- "AC Discharge Energy Today" = actual value ✅ (NOW FIXED - was 0.00)
- "AC Discharge Energy Total" = actual value ✅ (NOW FIXED - was 0.00)

**Note:** Both "Battery Charge" and "AC Charge Energy" sensors track the same thing (grid/generator charging your battery) and will show identical values. This is normal - they're just different sensor names for the same SPF register data.

#### 2. 🔇 Reduced Log Noise for Off-Grid Inverters

**Issue:** SPF users (and other off-grid models) saw constant WARNING messages in Home Assistant logs:

    [SPF 3000-6000 ES PLUS@/dev/ttyACM0] load_energy_today_low register not found

**Root Cause:** The `load_energy_today` register is specific to **grid-tied inverters** (SPH/MIN/MID/MAX) that track energy consumed from grid by loads. **Off-grid inverters** like SPF don't have this register because they use different energy tracking:
- `ac_discharge_energy_*` - Battery → loads via inverter
- `op_discharge_energy_*` - Operational discharge energy

The code was logging this as a WARNING even though it's expected and harmless for off-grid models.

**The Fix:** Changed log level from WARNING to DEBUG with clarifying message: "register not found (expected for off-grid models like SPF)"

**Impact:**
- ✅ SPF users will no longer see noisy warnings in logs
- ✅ Debug logging still available if needed for troubleshooting
- ✅ No functional changes - purely cosmetic log improvement

#### 3. 🎯 WIT Control Stability Improvements (Issue #143)

**Problem:** WIT users experiencing power oscillation, charge/discharge looping, and unstable control behavior when using battery management features.

**Root Cause:** WIT inverters use **VPP (Virtual Power Plant) protocol** with fundamentally different control model:
- **WIT**: Time-limited overrides (NOT persistent mode changes like SPH/SPF)
- Register 30476 (`priority_mode`) is **READ-ONLY** on WIT - shows TOU default, cannot be changed via Modbus
- Proper control requires VPP remote registers (30407-30409) with duration-based commands
- Rapid control changes cause oscillation and conflicts with TOU schedules

**The Fixes:**

1. **Register 30476 Marked Read-Only**
   - WIT profile now correctly marks `priority_mode` (30476) as `'access': 'R'`
   - Prevents users from trying to write to read-only register
   - Description updated to clarify VPP control model
   - Users guided to use proper VPP remote control instead

2. **30-Second Rate Limiting**
   - All WIT control writes now have 30-second cooldown
   - Prevents rapid automation loops that cause oscillation
   - Applies to registers: 201, 202, 203, 30100, 30407, 30408, 30409
   - Warning logged if write blocked: "Rate limit: WIT control writes must be 30s apart"
   - Gives inverter time to respond and stabilize

3. **Control Conflict Detection**
   - Detects multiple VPP remote controls active simultaneously
   - Warns when TOU schedule conflicts with remote control
   - Logs warnings to Home Assistant logs
   - Helps users identify problematic automation patterns

4. **Comprehensive WIT Control Guide**
   - New documentation: `docs/WIT_CONTROL_GUIDE.md`
   - Explains VPP vs Legacy protocol differences
   - Shows proper WIT control patterns with examples
   - Documents why register 30476 is read-only
   - Provides automation templates for stable control
   - Troubleshooting guide for common issues

**Impact:**
- ✅ WIT users can now implement stable battery control
- ✅ Oscillation and looping behavior prevented
- ✅ Clear guidance on proper VPP remote control usage
- ✅ Automatic conflict detection helps debug issues
- ✅ Rate limiting prevents automation mistakes

**WIT Control Registers (Rate Limited):**
- 201: Active Power Rate (Legacy VPP)
- 202: Work Mode (Legacy VPP)
- 203: Export Limit (W)
- 30100: Control Authority (VPP master enable)
- 30407: Remote Power Control Enable
- 30408: Remote Charging Time (duration in minutes)
- 30409: Remote Charge/Discharge Power (-100% to +100%)

**For WIT Users:**
- **Read the guide**: See `docs/WIT_CONTROL_GUIDE.md` for proper control patterns
- **Use VPP remote control**: Don't try to write to register 30476
- **Set durations**: All overrides should specify time duration (register 30408)
- **Wait 30s between changes**: Rate limiting is intentional to prevent oscillation
- **Check for conflicts**: Monitor logs for TOU vs remote control warnings

---

### Migration Notes:

**No action required** - This is a bug fix and improvement release. Simply upgrade and:
- SPF AC Charge/Discharge Energy sensors will show correct values
- Log warnings for missing load_energy_today register will disappear
- WIT control writes will have automatic rate limiting

**For SPF users:**
- All four AC Charge/Discharge Energy sensors will now work
- "AC Charge Energy" sensors will show identical values to "Battery Charge" sensors (expected behavior)
- Log noise from missing grid-tied registers eliminated

**For WIT users:**
- **IMPORTANT:** Read `docs/WIT_CONTROL_GUIDE.md` if you use battery control features
- Control writes now have 30s cooldown (prevents oscillation - this is intentional)
- Register 30476 (priority_mode) is now correctly marked read-only
- If you have automations that write to WIT controls rapidly, they may need adjustment
- Check logs for rate limit warnings and control conflict warnings

**Debug logging setup** (optional, for troubleshooting):
```yaml
logger:
  default: info
  logs:
    custom_components.growatt_modbus: debug
```

---

### Files Changed:
- `custom_components/growatt_modbus/growatt_modbus.py` - Added AC charge/discharge energy register mapping for SPF + reduced log noise + WIT rate limiting + conflict detection
- `custom_components/growatt_modbus/profiles/wit.py` - Marked priority_mode as read-only + added VPP control model documentation
- `docs/WIT_CONTROL_GUIDE.md` - NEW: Comprehensive WIT control guide with examples and troubleshooting
- `custom_components/growatt_modbus/manifest.json` - Version bump to 0.4.6
- `README.md` - Version badge updated to 0.4.6
- `RELEASENOTES.md` - Updated with v0.4.6 changes

---

# Release Notes - v0.4.5

## 🔥 CRITICAL Bug Fix: Serial Connection File Descriptor Leak

**Fixed:**
- **CRITICAL:** Serial connection file descriptor leak causing permanent integration failure after overnight offline periods

---

### What's Fixed in v0.4.5:

#### 1. 🔥 CRITICAL: Fixed Serial Connection File Descriptor Leak

**Root Cause:** When using USB-RS485 adapters (serial connection), failed connection attempts during offline periods (e.g., overnight when inverter is powered down) were not properly releasing the serial port file descriptor. Over hours of offline polling, hundreds of leaked file descriptors would accumulate until the system exhausted its limit.

**Symptoms:**
- Integration works fine initially
- Inverter goes offline (night time, powered down)
- After several hours, integration stops working completely
- Error in logs: `OSError: [Errno 24] No file descriptors available`
- Integration never recovers even when inverter comes back online
- **Inverter is actually online** (proven by Growatt cloud connectivity)
- Only fix is restarting Home Assistant

**Technical Details:**
The coordinator's `_fetch_data()` method had three critical flaws:
1. **No cleanup on failed connection** - When `connect()` failed, `disconnect()` was never called to release the serial port
2. **No cleanup before retry** - Each retry attempt would call `connect()` without first calling `disconnect()`, potentially creating multiple open file descriptors
3. **Silent exception handling** - Bare `except: pass` blocks hid disconnect failures

**Scenario Example:**
- Inverter offline 5pm-5am (12 hours)
- Offline polling every 300s = ~144 poll attempts
- Each attempt tries 3 connection retries = ~432 connection attempts
- Each leaked file descriptor accumulates
- At 5:12am when inverter wakes: errno 24 "No file descriptors available"
- Integration permanently broken until HA restart

**The Fix:**
1. **Always disconnect before connect** - Ensures clean state, prevents double-open
2. **Always disconnect after failed connect** - Releases file descriptors even on failure
3. **Proper error logging** - Replace bare `except: pass` with debug logging
4. **Connection state checking** - Skip `connect()` if already connected (prevents double-open)

**Files Changed:**
- `coordinator.py:482-537` - Added disconnect calls before/after every connect attempt
- `growatt_modbus.py:330-350` - Added `is_socket_open()` check to prevent double-connect
- `growatt_modbus.py:351-364` - Enhanced disconnect error logging with critical error detection

**Impact:**
- ✅ **ALL Serial/USB-RS485 users (ALL inverter models):** Integration now properly recovers from overnight offline periods
- ✅ **TCP users:** Not affected by the bug, but benefits from cleaner connection management
- ✅ **All inverter series (MIN/MID/MAX/MOD/SPH/SPF/WIT/MIX/SPA):** No more permanent failures when using serial connections
- ✅ **Logging:** Better visibility into connection lifecycle and resource leak issues

**Migration Notes:**
- No action required - fix is automatic
- If you experienced this issue, upgrade to v0.4.5 and restart Home Assistant once
- Monitor logs after upgrade - should see `Disconnected successfully` debug messages
- If you see `CRITICAL: File descriptor leak detected!` in logs after upgrade, please report the issue

---

### Files Changed:
- `custom_components/growatt_modbus/coordinator.py` - Fixed file descriptor leak in _fetch_data()
- `custom_components/growatt_modbus/growatt_modbus.py` - Enhanced connect/disconnect with leak prevention
- `custom_components/growatt_modbus/manifest.json` - Version bump to 0.4.5
- `RELEASENOTES.md` - Updated with v0.4.5 changes

---
