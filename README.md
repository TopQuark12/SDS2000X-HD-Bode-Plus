# Siglent SDS2000X HD Bode Plot Enhancements

An experimental, unofficial firmware modification adding thru normalization, variable-level normalization, channel bandwidth preservation, Standard/Fast settling and enhanced CSV export to the Bode Plot function.

> [!WARNING]
> **FLASH AT YOUR OWN RISK.** This is experimental, unofficial modified firmware, not an official Siglent release. It is not endorsed or supported by Siglent. Flashing may make the instrument unusable, erase settings or stored data, or introduce measurement and control failures. Successful offline tests or a successful flash do not establish correct operation. Recovery may require service or access to hardware programming tools; recovery or rollback is not guaranteed.

Before considering installation:

- Confirm that the package is intended for your exact instrument model, hardware variant and firmware base. Do not assume that firmware for a similarly named scope is compatible.
- Back up settings and measurement files separately. Keep the appropriate original vendor firmware and establish a recovery procedure for your instrument before proceeding.
- Verify the package against its published checksum. A matching checksum confirms file integrity, not compatibility or measurement accuracy.
- Follow the applicable vendor update procedure, use reliable power and storage, and do not interrupt an update.
- Proceed only if you accept the possibility of losing access to the instrument. Avoid installing experimental firmware on an instrument you depend on for critical work.

After installation, verify ordinary acquisition, channel scaling, bandwidth settings, generator control and Bode results against known signals before relying on measurements. Read the validation limits below.

**Find the controls**

Open **Analysis → Bode Plot → Data**. Drag the right-hand menu vertically to reach the new controls and the original List, Source, Save and Recall controls.

**Quick start: normalize, then measure**

1. Connect a **thru reference**: bypass the device under test and feed the input and output measurement paths from the same signal, preserving the intended cables, probes and terminations as far as practical. Check that each channel’s probe attenuation setting matches its probe.
2. In **Configure**, select the generator, input/output channels, sweep range, point density, amplitude and channel gain mode. Select the channel bandwidths in the normal channel menus. In **Data**, choose **Settling Standard** or **Fast** before calibration.
3. Run a complete reference sweep, preferably in **Single** mode. Wait until it finishes and Operation is Off.
4. Tap **Capture Thru**. This stores the completed sweep as the reference, replaces any previous reference and leaves correction OFF. It does not start a sweep.
5. Tap **Correction** to turn it ON. The captured sweep should now display approximately **0 dB and 0°**. This verifies self-normalization; repeat the sweep to check measurement repeatability.
6. Insert the device under test and repeat the sweep with the same settings. Keep Correction ON. The plot and list now show the response relative to the stored reference.

Normalization divides measured gain by reference gain and subtracts reference phase. Capturing a resistive divider as the reference therefore removes that divider’s response: subsequent results are relative to it, rather than an absolute measurement of the divider.

**Normalization math — engineering note**

At each frequency, for each enabled output channel, let `Ain` and `Aout` be the measured input/output magnitudes, and `φ` the scope's measured output-to-input phase. Subscript `ref` denotes the captured thru sweep:

```text
Gmeas = Aout / Ain
Gref  = Aout_ref / Ain_ref
Gnormalized = Gmeas / Gref

Gain_normalized_dB = 20 log10(Gnormalized)
                   = Gain_measured_dB − Gain_reference_dB
Phase_normalized  = wrap(φmeas − φref) into (−180°, +180°]
```

This is equivalent to dividing the measured complex response by the reference response. For example, a measured −6 dB / −35° response with a −1 dB / −5° reference displays **−5 dB / −30°**.

The implementation uses double-precision arithmetic, retains the raw readings, divides each output magnitude by its reference gain, and leaves the input magnitude unchanged. It then uses the scope's normal gain calculation and display path. Every correction starts from raw data, so toggling correction cannot compound it.

Correction is point-by-point: there is **no reference interpolation, smoothing or added averaging**. The frequency grid must match (relative frequency tolerance `1e−12`), and the captured configuration must match, including the active variable-level profile, channel bandwidths and settling mode. Invalid points are rejected. This removes repeatable response errors present in the reference; it does not remove random noise, recover clipped signals, or correct changed loading or nonlinear behavior. A noisy or very small reference response can make normalized results unreliable. A flat self-normalized trace alone is therefore not an accuracy test.

**Data menu controls**

- **Capture Thru:** stores a completed, valid reference sweep.
- **Correction ON/OFF:** switches between normalized and raw results without rerunning the sweep. OFF keeps the reference; repeated toggling does not accumulate correction.
- **Clear Thru:** discards the reference, disables correction and restores raw results.
- **Export CSV:** saves the latest sweep, including raw and displayed values.
- **Export Thru CSV:** saves the stored reference for external analysis or record keeping.
- **Thru status:** shows reference availability, correction state, sweep completeness, point count, last error and settling mode.
- **Settling Standard/Fast:** selects settling behavior for subsequent sweeps. Changing it disables correction and requires a matching reference.

Stop the sweep before capturing, clearing, toggling correction or changing settling. The corresponding controls are disabled while sweeping.

**Variable-level sweeps**

Select **Configure → Sweep Type → Vari-Level**, choose a profile and configure its frequency/amplitude nodes. Then follow the same reference-capture procedure. Use that same profile, frequency mode and point density for the DUT sweep.

All four profile slots and both linear and logarithmic frequency modes are supported by the implementation. Selecting another profile or editing the active profile requires a matching reference. Editing an unused profile does not invalidate the current reference.

**Bandwidth and sweep speed**

Bode respects each channel’s existing bandwidth selection. Set **FULL**, **20 MHz**, or another available limit deliberately before capturing the reference. A channel already set to 20 MHz stays there until you change it.

**Standard** retains the original settling waits and is the startup default. **Fast** shortens selected acquisition and manual/Hold gain waits. It does not halve every delay or guarantee a faster overall sweep. Generator communication, low-frequency acquisition and automatic ranging can still dominate.

**Exactly what Standard/Fast changes**

- **Horizontal settling:** Standard passes through the native requested delay `D`. Fast uses `max(1,000, floor(D/2))` microseconds when `D > 1,000 µs`; requests at or below 1,000 µs are unchanged. Thus a 20 ms wait becomes 10 ms, while a 1.25 ms wait becomes 1 ms.
- **Manual/Hold channel settling:** the fixed wait changes from **50 ms to 10 ms** when that path executes, saving 40 ms per call.
- **Automatic ranging:** decisions, retries and its existing waits are unchanged. Selecting Fast does not replace Auto gain with Hold.

The native horizontal delay is approximately **2.5 × its timing duration**. For longer timebases that duration is the selected record duration; at short timebases it uses a floor of 50 µs per horizontal division (500 µs for ten divisions). The separate first-point wait of **3 × that timing duration** is unchanged. Timebase selection, record length, acquisition settings, generator commands/readback and variable-level amplitude interpolation are also unchanged. Fast changes waiting time, not IFBW, sample count or averaging.

For an engineering comparison, capture a separate matching reference in each settling mode and repeat measurements on the actual DUT. Prefer Standard where a resonant or slow response needs longer to settle; try Fast when repeated results remain within your gain/phase error budget. Reference normalization cannot reliably cancel DUT-dependent settling transients. Benchmark the complete sweep on your own setup: shorter programmed waits do not guarantee a reduction in total sweep time.

Check repeatability before using Fast for final measurements, particularly near resonances or with large amplitude changes. Hold gain avoids automatic range adjustments, but you must choose ranges that avoid clipping while retaining useful resolution. No new IFBW or averaging control is provided.

**Export to USB**

1. Insert a USB drive. Finish and stop the sweep for a complete dataset.
2. Tap **Export CSV** or **Export Thru CSV**.
3. Choose a folder and save using the suggested filename or a new name. The chooser starts at detected external storage; opening native Save first is unnecessary.
4. Wait for the **CSV saved** message before removing the drive.

Existing files are refused: use a new filename. Export takes a snapshot when requested; exporting during a sweep may produce an incomplete dataset.

The CSV begins with metadata lines starting with `#`, followed by column names and data. When importing into a spreadsheet, skip the metadata lines before the column header.

Useful columns include `frequency_hz`, `raw_gain_db`, `raw_phase_deg`, `display_gain_db` and `display_phase_deg`. For corrected results, check **`calibration_applied=1`** and **`valid=1`**; check **`# complete=1`** for a completed sweep. The amplitude columns use vendor internal scaled magnitudes, not calibrated RMS or peak volts. Exported reference CSVs cannot currently be imported back into the scope.

**If something looks wrong**

- **Blank list:** turn List ON and select an output actually measured by the sweep. For example, with C2 as input and C4 as the only measured output, choose **Source C4**. An unmeasured output channel has no rows.
- **Check status / CONFIG_MISMATCH:** a setting no longer matches the reference. Restore the matching settings, or run a new reference sweep and capture it. Do not capture the DUT response unless you intend to use it as the new baseline.
- **Capture unavailable:** finish a valid sweep and stop it first.
- **Reference missing after restart:** calibration is held in memory and must be recaptured. Only one reference is stored at a time.
- **SCPI timeout:** an unresolved service responsiveness issue was observed even while VNC remained usable. A timeout alone does not establish that calibration data is invalid.

Recapture after changing cables, probes, attenuation, ranges or the measurement path, even if the scope does not report a mismatch. Normalization supports gain-response measurements with up to 1,024 points; PSRR and absolute-voltage display modes are not supported for correction.

**Optional computer control**

The supplied `fra_client.py` uses the scope’s SCPI connection. Replace `SCOPE_HOST` with your instrument’s hostname or IP address. From the folder containing that script:

```sh
python3 fra_client.py SCOPE_HOST status
python3 fra_client.py SCOPE_HOST capture
python3 fra_client.py SCOPE_HOST on
python3 fra_client.py SCOPE_HOST export --output measurement.csv
python3 fra_client.py SCOPE_HOST thru --output reference.csv
```

Other actions are `off`, `clear`, `standard`, `fast` and `perf`. Use `perf` for timing diagnostics; avoid repeatedly polling synchronous status during a speed comparison. The client refuses to overwrite existing output files.


**Validation and known limitations**

Numerical normalization, configuration checks, selected touchscreen controls and representative simple/variable-level sweeps have been exercised on hardware. Broader combinations and error paths have offline test coverage, which does not replace testing on the instrument. The current dialog-parent and USB export-path changes still require on-device verification; touchscreen USB export should not be treated as fully hardware validated.

An unresolved SCPI responsiveness issue has been observed during hardware testing, including timeouts on ordinary identity queries while VNC remained responsive. Its cause has not been established, and the current changes do not claim to resolve it.

Calibration is volatile, only one reference is stored, and reference CSV import is unavailable. This is response normalization, not a full network-analyzer error correction. Validate accuracy, repeatability and stability for the intended measurement conditions.
