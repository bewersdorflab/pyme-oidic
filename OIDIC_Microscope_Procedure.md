# OI-DIC Microscope Operating Procedure

*Olympus IX81 inverted microscope with ASI XY stage, PCO edge 4.2 camera, liquid-crystal OI-DIC (orientation-independent DIC) module, controlled by PYME Acquire.*

2026-10: Written by [Jyot Antani](https://antanij.github.io/) & Claude based on demo by [Yujin  Bao](https://bewersdorflab.yale.edu/profile/yujin-bao).

> Section 0 is a quick checklist; sections 1–10 give the detailed steps.

---

## 0. Quick checklist

- [ ] Power switches on (microscope, XY stage, PIFOC, cooler, PCO)
- [ ] PYME Acquire started — 3 windows open; fluorescence & Focus Lock minimized (not closed)
- [ ] Oil on objective, sample mounted
- [ ] Focus by moving objective **down** only
- [ ] Köhler: aperture/diaphragm closed → eyepieces → lower condenser → camera → aperture open → diaphragm just outside FOV
- [ ] LC calibration: filter cube to position 2 (Blank) → initialize → polarizer to minimum → run → check curves have a minimum → save
- [ ] Sample stack (≤ 20 µm) → background (Standard, empty field, defocused)
- [ ] Tiled imaging: restart computer first (XY stage)
- [ ] Reconstruct (integrate → OPD), save as `_opd.h5` — can be done on another PC

---

## 1. Power on the hardware

On the switch panel under the monitor, turn on (green light = on):

| Switch | What it powers |
|---|---|
| Microscope | Olympus IX81 main power |
| XY Stage | ASI motorized stage |
| PIFOC | Z piezo (fine focus) |
| CAM cooler | Camera cooling (right-most) |
| PCO camera | Camera used for **OI-DIC** |
| Hamamatsu camera | used for **SMLM / fluorescence** |


## 2. Start the software

1. Double-click the **PYME Acquire "Fluorescence"** icon on the desktop. A command window opens, then the PYME Acquire splash screen. Wait for it to finish initializing.
2. **Three windows** open together from that one icon:
   - **OI-DIC window** (titled *Drift Tracking*) – camera preview, acquisition and OIDIC menus.
   - **Focus lock** – laser-reflection focus channel.
   - **Fluorescence** channel called "PYME Acquire"
3. For OI-DIC-only work, **minimize** the fluorescence & Focus Lock window — **do not close it**. Closing any of the three windows shuts down the whole program. Unpin and hide minimize Focus Lock window within Drift Tracking screen.
4. The right-hand panels show the stage position (x, y, z), integration time, camera mode and the acquisition settings (including tiling).

## 3. Mount the sample

1. Put a drop of **silicone immersion oil** on the objective.
2. Place the sample dish in the stage holder, coverslip down, over the objective.

## 4. Find focus safely

1. Bring the objective **all the way up**, close to the coverslip, first.
2. While looking for the sample, **only move the objective down** (away from the sample). This avoids driving the objective into the coverslip and squeezing/cracking it.
3. Turn on the transmitted (brightfield) lamp with the button on the side of the IX81; the neighbouring knob sets the intensity. Use **maximum intensity** to find the sample (adjust later as needed).
4. Focus until the sample appears in the live preview, then pick the **middle focal plane** of the region you want and adjust display contrast (histogram panel).

## 5. Set up Köhler illumination

1. **Close the condenser aperture** fully.
2. **Close the field diaphragm** fully (minimum).
3. Switch the light path from **camera → eyepieces**.
4. **Lower the condenser** while looking through the eyepieces until the image of the field diaphragm is sharp.
   - ⚠️ Make sure the condenser does **not touch the sample** — the clearance is **VERY** small.
5. Switch back from **eyepieces → camera**.
6. **Open the condenser aperture fully.**
7. Watching the camera image, **open the field diaphragm just enough** that its edge sits just outside the field of view.

## 6. Liquid-crystal calibration (do before every imaging session)

1. Change filter cube position to 2 (Blank) looking from left side of filter wheel, directly below the list.
2. In the OI-DIC window open **OIDIC → OIDIC Calibration**.
3. Click **Initialize calibration**. The default parameters normally don't need changing (see table below).
4. Rotate the **polarizer** (wheel on the condenser) until the field of view is at its **minimum intensity**.
5. Click **Run calibration**. It steps the liquid-crystal voltages to find the zero-bias positions and plots two curves (path-length shift vs. voltage, one per shear direction). 
6. Make sure the scatter points on the calibration curve have a minimum. If they have a different shape (e.g., monotonic), something is wrong. 
   - Check your light path (e.g., filter wheel).
   - Restart the liquid crystal by unplugging and re-plugging it, then recalibrate.
7. **Save calibration**.

**Default calibration parameters**

| Parameter | Value shown |
|---|---|
| Wavelength | 546.0 nm |
| Shear distance | 70.0 nm |
| Liquid crystal settling time | 300 ms |
| First shear direction voltage | 1.0 |
| Second shear direction voltage | 4.0 |
| First shear direction zero-bias voltage | ~2.7 |
| Second shear direction zero-bias voltage | ~2.8 |

## 7. Acquire an OI-DIC z-stack

1. Bring the sample back into focus and choose a region (avoid bubbles; a tissue edge is fine).
2. In **Acquisition Tasks** set:
   - Acquisition type: **OIDIC**
   - Mode: **6-frame** (4-frame is faster, see §9)
   - Sample (not Background); Bias: **0.15**
   - images to average: **9** (this means averaging over 8 images in the current code)
   - Select **Z-stepped** and open *Z stepping*: Piezo channel z, **Middle and #**
   - Step size and # slices: keep total thickness **≤ 20 µm**. (In the recording they discussed 200 nm × 15 slices, then 0.4 µm and 1 µm steps; the saved file was named *500nm × 30 slices*.) Note the program may alter the slice count you type — double-check before starting.
3. Spool to **File**, folder `scope_baby\<date>` (e.g. `2026_9_29`).
4. Give the series a descriptive name (e.g. `oidic1_500nmx30slices`) and press **Start**.

## 8. Acquire a background reference

1. Switch from Z-stepped to **Standard** (no z-stack needed for background).
2. Select **Background**; name it e.g. `oidicbg`.
3. Move the stage to a field of view **with no sample**, and defocus so nothing is visible.
4. Press **Start** to acquire the background reference image.

## 9. Tiled OI-DIC (larger area)
[for FUTURE FIX] **Restart computer before tiled imaging**. XY stage needs the computer to be ON so if the switch is turned on later, it won't work.

1. Acquisition type: **Tiled OIDIC**; mode 6-frame (or 4-frame), averaging as before.
2. **# steps x / y** – counter-intuitive: entering **3 × 3** gives **4 × 4 tiles** (it counts *steps*, not tiles).
3. **Tile spacing** is the stage step as a fraction of the tile size: **0.9 = 10 % overlap** (not 90 %).
4. Tick **Save raw frames**.
5. Z-stepped tiling is possible but produces very large datasets — keep slices few (e.g. **2 µm steps × 10 slices**).
6. To cut acquisition time, switch to **4-frame mode** instead of 6-frame.
7. Name the series and press **Start**.


## 10. Reconstruct in PYMEImage

> **Note:** Reconstruction does not have to run on the acquisition computer. Copy the `.h5` files and reconstruct on a personal PC or the lab workstation (with PYME + the OI-DIC module installed) — especially for tiled images that are too large for the acquisition computer's RAM.

1. Open the sample `.h5` file in **PYMEImage** (drag-and-drop the file onto it).
2. **Modules → OIDIC** to enable the OIDIC module, then click **Reconstruct**.
3. When prompted, select the **background reference** file (`oidicbg.h5`).
4. In *Edit properties*, leave the other parameters (bias 0.15, N frames 6, shear distance 70, wavelength 546) and choose the **reconstruction type**:
   - **integrate** – reconstructs the **optical path difference (OPD)**; quantitative. Do this one first.
   - **Riesz** – higher contrast for visualization only; **not quantitative**.
5. Wait (≈1–2 min). Then **File → Save as → PYME HDF (.h5)**, using the same name as the acquisition plus `_opd`, e.g. `oidic1_500nmx30slices_opd.h5`.
6. Repeat steps 2–5 with the second reconstruction type if you also want the high-contrast version.

---

## Notes: software repositories

- **PYME (python-microscopy):** https://github.com/python-microscopy/python-microscopy
- **Current microscope-control PYME repository** (not updated to the latest PYME version, to stay compatible with the OI-DIC repository): https://github.com/Yujin-Bao/python-microscopy
- **OI-DIC repository:** https://github.com/bewersdorflab/pyme-oidic
