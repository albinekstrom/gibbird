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

Prices are approximate (October 2026). Check Swedish shops first, e.g.
Electrokit, Kjell & Company or Webhallen. Pimoroni and The Pi Hut ship to Sweden.

**Frame + Pi (bedroom)**

| Part | Notes | ≈ Price |
|---|---|---|
| Pimoroni Inky Impression 7.3" (2025 ed., Spectra 6) | 800×480, 6 colours, board 174.2×123.2 mm, image area 160×96 mm. The 13.3" (1600×1200, A4) also works with the same code | £66–80 |
| ~~Raspberry Pi~~ | **Already owned: Pi 4 Model B.** It runs the camera, classifier and display. A Pi 5 also fits the same hood | – |
| 40-pin GPIO ribbon extension cable, **female → male**, 10–20 cm | Joins the Pi to the display header. Match pin 1 to pin 1 | 60 kr |
| 4× M2.5×6 screws | Pi onto the printed bosses | 20 kr |
| Official Pi 4 USB-C power supply (5.1 V 3 A) | Use a mains extension cord to reach the socket, not a long USB-C cable | 100 kr |
| microSD 32 GB **High Endurance** | It writes continuously | 150 kr |
| BGA "Galant" A4 frame (22.7×31.4 cm, acrylic) | The 3D model's defaults match it: 8 mm rabbet, 13 mm profile | 150 kr |
| 6× wood screws 2.5×10 mm countersunk, 4× M3×10 countersunk, 2× M3×16 | Pre-drill 1.5 mm for the wood screws, because the frame's back edge is only ~8 mm wide. M3×10 hold the pod cover, M3×16 are the stand's pivots | 40 kr |
| 90° USB-C power cable (or angle adapter) | Fits beside the Pi inside the pod | 60 kr |
| Self-adhesive foam/felt strips, 2–3 mm | Press the display against the glass | 50 kr |
| Black paper/card mask (optional) | The window is about 201×288 mm, so ~9 mm of the display's printed border shows at one end. A cut mask hides it | – |
| ~300 g PETG or PLA | | |

**Fan.** The hood has a mount for a 30 mm fan (like the "Pi-Fan" from your Pi 4
case). It sits over the processor and blows out through a grille in the roof, and air
comes in through vents in the bottom wall. The display ribbon cable uses the whole
GPIO header, so power the fan from a spare USB port with a **USB‑A → 2‑pin fan cable**
(≈30 kr) instead of from GPIO pins 4 and 6.

**Camera (balcony), 3–5 m from the Pi**

The Pi's own flat camera cable can't go that far. A wide-angle USB camera works well:
USB 2.0 is specified for cables up to 5 m, and the camera gets its power through the
same cable.

| Part | Notes | ≈ Price |
|---|---|---|
| Wide-angle **4K (8 MP) USB camera**, UVC with MJPEG, ~100–120° lens | E.g. an ELP or Arducam module with a Sony IMX415 or IMX317 sensor. Autofocus is a bonus but not needed at 1–3 m | 500–900 kr |
| **USB 2.0 extension cable, 5 m** (flat if it has to pass a door or window seal) | Up to 5 m works without an amplifier. For longer runs, use an **active** USB repeater cable (5–10 m) | 100–200 kr |
| Right-angle USB-A adapter | So the plug turns sideways inside the hood's top plug space | 30 kr |

What a 4K wide camera sees of a 12 cm bird: ~190 px at 1 m, ~95 px at 2 m, ~65 px
at 3 m. The classifier is reliable from about 100 px, so keep the feeder within about
2 m of the camera.

Other options: **Camera Module 3 Wide** gives a better picture, but it only works on
a short CSI ribbon (≤ 1 m). You could also put a small Pi Zero 2 W next to the camera
and send pictures over Wi-Fi, but that means a second computer to look after.

For either option, add:

| Part | Notes | ≈ Price |
|---|---|---|
| IP65 junction box with a clear lid + cable gland + silica gel | Or put the camera indoors behind the balcony door glass. That avoids weather but you get reflections | 150–250 kr |
| Feeder / perch | This is what brings the birds to the camera | 100–300 kr |

**Total:** about 2,500–3,000 kr with the 7.3" display and a USB camera, since you already have the Pi.

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
