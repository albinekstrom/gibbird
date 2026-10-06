# GibBird: balcony bird camera + e-ink frame

A camera on the balcony spots birds, works out the species, and an A4 colour
e-ink frame in the bedroom shows who visited today. It's based on teddymakesstuff's
"Avian Visitors" frame, but that one listens for birds (BirdNET audio, hence
"Heard Today") and this one watches with a camera.

It's set up for **Gothenburg** first: a curated list of 58 local species with Swedish
names and a Swedish poster. Everything that depends on location sits in one region
file, so you can make a list for anywhere else (see [Other locations](#other-locations)).

```
 BALCONY                 camera cable           BEDROOM (hidden behind the frame)
 ┌──────────────────┐   ─────────────────────▶ ┌────────────────────────────────┐
 │ Camera Module 3  │   (CSI, CSI→HDMI kit,    │ Raspberry Pi 4 (or 5)          │
 │ Wide in a        │    or USB webcam)        │  gibbird cam:   motion → crop  │
 │ weatherproof box │                          │                 → classify     │
 └──────────────────┘                          │  gibbird frame: poster → Inky  │
                                               │ ribbon cable → Inky 13.3" panel│
                                               └────────────────────────────────┘
```

## Step-by-step

**Placement:** [docs/INSTALLATION.md](docs/INSTALLATION.md) describes where the frame,
camera, feeder and cables go (office window + balcony), plus the weatherproof camera
housing (`hardware/camera_housing.scad`).

1. **Buy the parts** (list below). Also get a feeder or perch about 0.5–1.5 m from
   where the camera will sit. The classifier needs the bird to fill a good part of
   the picture. A bird flying past at 5 m will not be identified.
2. **Pick and measure the frame.** Measure its outer size, the rabbet (the opening on
   the back where the display goes), how deep the display sits below the back face,
   and where the display's 40-pin header is.
3. **Print the back.** Enter your measurements in `hardware/frame_back.scad` and export
   `back_lower`, `back_upper` and `stand` (see [3D print](#3d-printed-back)).
4. **Flash the SD card** with Raspberry Pi Imager → *Raspberry Pi OS Lite (64-bit)*.
   In the Imager settings, set Wi-Fi, enable SSH, and use the hostname `birdframe`.
5. **Build the frame.** Put the display face-down in the frame with foam strips on
   top. Take the Pi 4 out of its aluminium case (keep the stick-on heatsinks) and screw
   it onto the four bosses in the printed back.
   Plug the ribbon cable into the display header, then screw the back onto the frame
   and plug the other end into the Pi. Run the power and camera cables out through the
   hood's right wall, along the clips, and under the stand's foot.
6. **Mount the camera** in a weatherproof box, high in a corner so it sees the whole
   balcony, with the feeder no more than about 2 m away. Run the cable inside along
   the balcony door seal and into the hood.
7. **Install the software** ([Software](#software)). Use `gibbird classify` on a few
   photos and check the web page at `http://birdframe.local:8080`.
8. **Calibrate** at `http://birdframe.local:8080/calibrate` ([below](#zones-and-calibration)).
9. **Tune** `min_score`, the camera angle and the feeder position in the first week.

## Shopping list

This is the current build: a Pi 4 behind a Waveshare 7.3" e-ink panel, and an IMX678
USB camera outside the office window. Prices are from amazon.se, October 2026.

**Already owned:** Raspberry Pi 4 Model B with its fan and heatsinks, the official Pi 4
USB-C power supply, a microSD 32 GB High Endurance card, and a picture frame. The 3D
model still has to be sized for that frame.

**Main parts**

| Part | Notes | ≈ Price |
|---|---|---|
| **Waveshare 7.3" 6‑Color e‑Paper HAT (E)** (E Ink Spectra 6, 800×480) | Comes with the driver board and a 40-pin extension header. The driver board plugs straight onto the Pi, so no ribbon cable is needed | 1 258 kr |
| **Iyalezirk IMX678 USB camera module, 8 MP, 123°** | USB, 4K MJPEG, 38×38 mm board. Sony Starvis 2 sensor, good in grey winter light. Sold by a third-party seller | 864 kr + 33 kr |

**For the frame and the Pi**

| Part | Notes | ≈ Price |
|---|---|---|
| 90° USB-C adapter (male → female) | So the power plug fits beside the Pi inside the pod | 50–100 kr |
| USB-A → 2-pin fan cable, 5 V | Powers the Pi-Fan from a USB port, since the display board takes the GPIO pins | 30–60 kr |
| Screw kit M2.5 + M3 (stainless) | Pi 4× M2.5×6, pod cover 4× M3×10 countersunk, stand 2× M3×16 | 100–200 kr |
| 6× wood screws 2.5×10 mm countersunk | Back plate to the frame (pre-drill 1.5 mm) | 30–50 kr |
| Self-adhesive foam/felt pads, 2–3 mm | Support the thin glass display panel evenly | 50–80 kr |
| PLA or PETG filament, ~300 g | For the indoor frame back | – |

**For the camera outside**

| Part | Notes | ≈ Price |
|---|---|---|
| USB 2.0 extension, A‑male → A‑female, 2–3 m, **carries data** (flat if it crosses the window seal) | From the camera's cable to the Pi | 80–150 kr |
| 2× stainless hose clamps (band ≤ 12 mm) | Strap the camera bracket to a railing post without drilling. Choose a size that fits around the post plus the 8 mm base | 40–80 kr |
| EPDM/rubber tape | Between the bracket and the railing, to grip and protect the paint | 50 kr |
| PG9 cable gland, IP68 | Seals the cable into the housing | 50–80 kr |
| Round glass/acrylic disc, 32 mm × 2 mm | The housing's window (the size the housing model works out for this lens) | 30–80 kr |
| 2 mm silicone O-ring cord or EPDM foam gasket tape | Seals the housing lid | 50–100 kr |
| Clear outdoor silicone | Glues the window disc in | 60–100 kr |
| Silica gel sachets | Keep the housing dry; replace each autumn | 40–80 kr |
| ASA filament (PETG works; never PLA outdoors) | For the camera housing and bracket | 250–350 kr |
| Feeder for the railing + sunflower seeds | 1.2–1.5 m from the camera. Check your housing association's rules first | 150–350 kr |
| Optional: conformal coating spray | Extra moisture protection for the camera board | 100 kr |

**Total for what's left to buy:** about **3 000–3 500 kr** including the display and camera.

## 3D-printed back

`hardware/frame_back.scad` is parametric. Install [OpenSCAD](https://openscad.org)
(the `openscad@snapshot` Homebrew cask works on macOS), open the file and use the
Customizer panel.

| Stand open | Stand closed |
|---|---|
| ![Back with the stand open](docs/assembly.png) | ![Back with the stand closed](docs/assembly_closed.png) |

The back is one clean central column, and nothing else is visible:

- **Pod.** Hides the Pi (4 or 5). The Pi screws onto four bosses on the plate, next
  to an opening over the display's 40-pin header, and a short ribbon cable joins them
  inside. The pod **cover** is a separate part, printed roof-down for a smooth finish
  with no sagging spans. It comes off with 4 screws that are hidden under the stand,
  so you can reach the Pi without taking the back off the frame.
- **Fan.** A 30 mm fan mount and grille in the cover's roof, over the processor. Air
  comes in through slots in the cover's bottom wall.
- **Spine.** A hollow channel from the pod down to the bottom edge. The power and
  camera cables run inside it, so no clips, zip ties or loose cables show. Use a
  **90° (angled) USB-C power cable**: there are 14 mm beside the Pi for the plug.
- **Stand.** A solid flap that closes over the pod and spine, so from behind the frame
  looks like a slab with one neat block on it. It has vent slots over the fan. It
  pivots on two M3×16 screws in towers at the top of the pod, and a stop tab sets the
  angle (`stand_open`, default 35°).
- **Plate.** Rounded corners and softened edges. It screws onto the frame with 6 small
  countersunk screws. On a 256 mm print bed it's printed in two halves, joined by a
  glued lap joint. The joint lines up with a thin groove, so it reads as a design line
  rather than a seam.

**Assembly:** glue the plate halves → screw the Pi onto the bosses → plug the ribbon
into the Pi → thread the power and camera cables up through the spine and plug them
in → put the display face-down in the frame with foam strips → plug the ribbon into
the display header, lower the plate and screw it to the frame → screw the fan into
the cover and plug its USB lead into the Pi → screw on the cover (4× M3×10) → fit
the stand (2× M3×16).

Measure these before printing: `frame_w/h`, `rabbet_w/h`, `display_recess`, and the
display header centre `hdr_x/hdr_y`. The header centre is measured from the bottom-left
of the rabbet, looking at the **back**, with the frame in portrait. The default
(62, 137) is only an estimate from the video. The Pi's position is worked out from
the header position. The file refuses to render if the display header ends up outside the pod or under
the Pi, or if the seam runs through the pod. The `stl/` folder has exports made with the default numbers,
so treat them as a test print only.

No part needs supports: plate halves flat side down, cover roof down, stand pod-side
down. Use 0.2 mm layers, 3 walls and 15 % infill. PETG handles a warm windowsill
better than PLA. A matte or silk filament in one colour gives the cleanest look.

## Software

```
gibbird/           Python package
  camera.py        Picamera2 / OpenCV frame sources
  motion.py        background-subtraction motion detector + crop
  classifier.py    TFLite / LiteRT classifier (Google iNat birds, 964 species)
  watcher.py       motion → classify → confirm over several frames → visits
  store.py         SQLite visit log
  server.py        HTTP API + a simple phone page
  calibration.py   detection zones, image → real-world (cm) homography, size filter
  web/             calibration page
  render.py        e-ink poster (1200×1600) + language strings
  frame_app.py     polling, change detection, quiet hours
  data/regions/    species lists (gothenburg.csv)
hardware/          OpenSCAD model + STLs
scripts/           model download, region generator
systemd/           services (camera + frame, both on the same Pi)
```

How detection works. A low-resolution stream is checked for motion. Each moving region
is cut out of the full-resolution frame (12 MP on Camera Module 3) as a square, padded, and classified. A
species only counts when it wins 2 of 4 checks in a row, and it must be on the region
list. This stops the model from reporting, say, an American goldfinch in Gothenburg.
Sightings less than 2 minutes apart count as one visit. The most confident photo of
each visit is kept.

### Zones and calibration

Open `http://birdframe.local:8080/calibrate` while `gibbird cam` is running. It shows
a live snapshot.

- **Zones.** Outline where birds should be detected: railing, feeder, flower box.
  Motion outside the zones is ignored, so trees, the street and neighbours don't
  trigger anything.
- **Reference points.** Choose one flat surface where birds land, for example the
  face of the railing. Click 4 or more spots on it that you've measured with a tape,
  and type their positions in cm. From these the Pi works out how the picture maps to
  real centimetres. A white 50 cm grid is then drawn over the snapshot so you can
  check the fit. With 5 or more points it also shows a fit error.
- **What calibration gives you.** Zones are stored in centimetres. If the camera gets
  bumped, redo only the reference points and the zones stay where they were in the
  real world. Moving things outside the bird size range (default 6–80 cm) are ignored,
  such as a cat, a person or a flapping towel. Sizes are measured on the reference
  surface, so things far in front of or behind it are measured less accurately.

Everything is saved to `data/calibration.json` and applied immediately, without a
restart. The page has no login, so only use it on your home network.

The frame redraws only when the set of species or visit counts changes. It waits at
least 15 minutes between refreshes and stays dark 23:00–07:00. A full Spectra
refresh takes about 30 s and flashes. If nothing has been seen today, it shows the
last 7 days instead.

### Raspberry Pi (`birdframe`): deploy from your computer

You develop on your Mac and push to the Pi over SSH. The Pi doesn't need git or GitHub.

```bash
cp config.example.toml config.toml        # edit locally; it is copied on every deploy
scripts/deploy.sh --setup                  # first time: packages, SPI/I2C, venv, services
                                           # (reboots once; then run scripts/deploy.sh again)
scripts/deploy.sh                          # after every change: sync + restart
scripts/deploy.sh --logs                   # follow the logs
scripts/deploy.sh --status                 # services + CPU temperature
```

The target defaults to `albin@birdframe.local`; set `GIBBIRD_HOST=user@host` to change
it. The deploy uses rsync and leaves the Pi's `data/` folder (visits, photos,
calibration) and its Python environment alone. Python packages are only reinstalled
when `pyproject.toml` changes.

If the poster comes out upside down, set `rotation = 270`.

### On your Mac (no hardware)

```bash
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]' ai-edge-litert
scripts/download_model.sh
.venv/bin/pytest
.venv/bin/gibbird -c config.example.toml classify photo.jpg      # test the model
.venv/bin/gibbird -c config.example.toml demo --photos ~/birds   # poster.png, dithered like the panel
.venv/bin/gibbird -c config.example.toml frame --once --preview p.png  # against a running cam
```

To run the full camera pipeline on a laptop, set `source = "opencv:0"` (webcam) or
`source = "clip.mp4"` (a video file).

## Other locations

```bash
# Uses GBIF bird records within 15 km. Local names in any ISO 639-2 language (swe, deu, fra, …)
python3 scripts/make_region.py --lat 59.33 --lon 18.07 --radius 15 --lang swe \
    --min-records 200 --out gibbird/data/regions/stockholm.csv
```

Then set `region = "stockholm"` in `config.toml`. The generated list includes ducks,
waders and seabirds that won't land on a balcony. Delete those rows by hand, as was
done for `gothenburg.csv`. You can also add `aliases` for look-alikes the model knows
under another name (e.g. *Corvus corone* → Hooded Crow).
For poster text in another language, add an entry to `TEXT` in `gibbird/render.py`.

## Ideas for later

- Raspberry Pi AI Camera or AI HAT+ for a real bird detector instead of motion.
- Add BirdNET (audio) as well, like the original, so it covers "heard" and "seen".
- A weekly poster on Sundays, and a "first of the year" highlight.
