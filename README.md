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
| Pimoroni Inky Impression 13.3" (2025 ed., Spectra 6) | 1600×1200, 6 colours, PCB is exactly A4 (297×210 mm) | £230 / $275 |
| ~~Raspberry Pi~~ | **Already owned: Pi 4 Model B.** It runs the camera, classifier and display. A Pi 5 also fits the same hood | – |
| 40-pin GPIO ribbon extension cable, **female → male**, 10–20 cm | Joins the Pi to the display header. Match pin 1 to pin 1 | 60 kr |
| 4× M2.5×6 screws | Pi onto the printed bosses | 20 kr |
| Official Pi 4 USB-C power supply (5.1 V 3 A) | Use a mains extension cord to reach the socket, not a long USB-C cable | 100 kr |
| microSD 32 GB **High Endurance** | It writes continuously | 150 kr |
| A4 / 21×30 cm wooden frame | The back must be flat and about 20 mm wide so screws can go in. Check the rabbet depth | 150–300 kr |
| 6× wood screws 3×12 mm countersunk, 2× M3×16 screws | M3 screws are the stand's hinge pins | 30 kr |
| Self-adhesive foam/felt strips, 2–3 mm | Press the display against the glass | 50 kr |
| ~300 g PETG or PLA | | |

The fan from your case runs off GPIO pins 4 and 6, but the display ribbon takes the
whole header. Start without the fan; the heatsinks and hood vents should be enough
because the Pi only classifies when something moves. Check `vcgencmd measure_temp`.
If it goes above about 75 °C, add a 40-pin GPIO 1-to-2 splitter so the fan can
plug in next to the ribbon.

**Camera (balcony)**

A wide-angle camera sees the whole balcony, but each bird takes up fewer pixels.
Roughly, for a 12 cm bird:

| Camera | Field of view | Bird at 1 m | at 2 m | at 3 m |
|---|---|---|---|---|
| Camera Module 3 **Wide**, full 12 MP | 102° horizontal | ~230 px | ~110 px | ~75 px |
| Camera Module 3 (standard), full 12 MP | 66° | ~420 px | ~210 px | ~140 px |
| 1080p USB webcam, ~78° | 78° | ~140 px | ~70 px | ~45 px |

The classifier looks at 224×224 px crops. It's reliable from about 100 px and gets
poor below about 60 px. With the Wide camera, keep the feeder or perch within about
2 m. Birds further away will be detected, but often not identified.

Recommended: **Camera Module 3 Wide** (≈350 kr), with the cable chosen by distance.

| Distance Pi → camera | Cable | ≈ Price |
|---|---|---|
| up to ~1 m | Standard 15-pin camera ribbon cable (Pi 4 uses the full-size connector), 1 m | 50 kr |
| further (through a wall or door) | CSI-to-HDMI extension kit (e.g. Arducam) + flat HDMI cable. Check it lists Camera Module 3 | 300–400 kr |
| alternative | 1080p USB webcam + **active** USB extension 5–10 m. Simpler, but lower resolution (see above) | 700–1,000 kr |

For either option, add:

| Part | Notes | ≈ Price |
|---|---|---|
| IP65 junction box with a clear lid + cable gland + silica gel | Or put the camera indoors behind the balcony door glass. That avoids weather but you get reflections | 150–250 kr |
| Feeder / perch | This is what brings the birds to the camera | 100–300 kr |

**Total:** about 4,000–4,500 kr, since you already have the Pi. Most of it is the display.

## 3D-printed back

`hardware/frame_back.scad` is parametric. Install [OpenSCAD](https://openscad.org)
(the `openscad@snapshot` Homebrew cask works on macOS), open the file and use the
Customizer panel.

![Assembly](docs/assembly.png)

- **Back plate.** Covers the frame's back and screws into the wood with 6 screws.
- **Pi hood.** The Pi (4 or 5) is screwed flat onto four bosses inside a vented hood
  (90×115 mm, 27 mm deep). Its GPIO edge faces an opening over the display's 40-pin
  header, so a short ribbon cable joins the two inside the hood. The hood has roof
  vents over the cooler and low vents in the bottom wall. Three slots in the right wall let
  the USB-C power plug, the flat camera cable and a USB plug pass through.
- **Cables.** Snap-in clips guide both cables down to the bottom edge, and they
  pass under an arch in the stand's foot.
- **Flip-out stand.** A rectangular stand that folds flat around the hood. It pivots
  on two M3×16 screws that self-tap into the hinge blocks. A small stop tab behind the
  hinge sets the opening angle (`stand_open`, default 35°). The tab length is
  calculated from that angle.
- **Split.** The plate is 251×338 mm by default, so it is split into two pieces
  joined by a glued 16 mm lap joint (`split_y`). All parts fit a 256×256 bed.
  Glue with CA or epoxy.

Measure these before printing: `frame_w/h`, `rabbet_w/h`, `display_recess`, and the
display header centre `hdr_x/hdr_y`. The header centre is measured from the bottom-left
of the rabbet, looking at the **back**, with the frame in portrait. The default
(62, 137) is only an estimate from the video. The Pi's position is worked out from
the header position. The file will refuse to render if the hood would collide with
the stand or the seam. The `stl/` folder has exports made with the default numbers,
so treat them as a test print only.

Print flat side down: 0.2 mm layers, 3 walls, 15 % infill. Only the hood roof
bridges, so no supports are needed. PETG handles a warm windowsill better than PLA.

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
