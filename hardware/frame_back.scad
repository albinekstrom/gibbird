// GibBird — back cover v2 for a picture frame holding a Pimoroni Inky Impression,
// with a Raspberry Pi 4/5 hidden behind it.
//
// Coordinates are seen FROM THE BACK with the frame standing in portrait.
// Origin = bottom-left corner of the frame's back face, Z points away from the display.
//
// Design: one clean central column. A pod hides the Pi (its cover comes off with 4
// screws hidden under the stand), a hollow spine carries the power and camera cables
// out to the bottom edge, and a solid flip-out stand closes over both, so from behind
// the frame looks like a slab with a single neat block on it.
//
// Parts and print orientation (all without supports):
//   back_lower, back_upper  plate halves, flat side down; glue the lap joint
//                           (or `back` in one piece if your bed is big enough)
//   pod_cover               roof down (a textured plate gives a nice finish)
//   stand                   pod side down
//
// Workflow: measure your frame + display, edit the [Frame] and [Display header] values,
// pick a `part`, press F6 (render), then File > Export > STL.

part = "assembly"; // [assembly, back, back_lower, back_upper, pod_cover, stand]

/* [Frame: MEASURE YOURS] */
// Defaults: BGA "Galant" A4 frame (22.7 x 31.4 cm, 13 mm profile, 8 mm rabbet).
frame_w = 227;        // outer width of the frame (portrait)
frame_h = 314;        // outer height
rabbet_w = 211;       // opening on the back where the display sits
rabbet_h = 298;
display_recess = 2.5; // frame back face -> display back (8 mm rabbet - acrylic - display)

/* [Display header: centre of the Inky's 40-pin header, from the rabbet's bottom-left] */
hdr_x = 62;           // estimated: measure yours!
hdr_y = 137;
hdr_open = [16, 66];  // opening for header + ribbon plug (header runs vertically)

/* [Pod: hides the Raspberry Pi] */
pod_w = 110;
pod_y0 = 98;          // bottom edge of the pod, frame coordinates
cable_room = 14;      // inside the pod, right of and below the Pi, for cables
plug_room = 20;       // above the USB-A ports, for a right-angle plug
boss_h = 4;           // Pi stands this far above the plate (M2.5 x 6 screws)
boss_d = 6;
boss_hole_d = 2.2;
pi_tall = 16;         // tallest part above the Pi's board
wall = 2.4;
roof_t = 2.4;
radius = 6;           // corner radius of plate, pod and stand
chamfer = 1.2;        // softened top edges
cover_screw = 3.4;    // 4x M3 x 10 countersunk, into bosses on the plate
cover_pilot = 2.6;

/* [Fan: 30 mm 5 V fan over the SoC, exhausting through the roof] */
fan = true;
fan_size = 30;
fan_t = 7;
fan_hole_spacing = 24;
fan_screw_d = 3.2;
fan_at = [29, 32];    // in Pi board coordinates (Pi 4 SoC ~29 mm from the GPIO end)

/* [Spine: hollow channel for the cables] */
spine_w = 34;

/* [Back plate] */
plate_t = 3.2;
screw_d = 2.9;        // 6x wood screws 2.5 x 10 mm into the frame (pre-drill 1.5 mm)
screw_head_d = 5.2;

/* [Stand] */
stand_open = 35;      // how far the stand swings open (deg)
flap_t = 5;
hinge_r = 5;
hinge_gap = 0.6;
knuckle_w = 10;       // hinge towers at both ends
knuckle_clear = 0.5;
pin_d = 3.3;          // stand pivots on the smooth shank of an M3 x 16 screw...
pin_tap_d = 2.8;      // ...which self-taps into the hinge tower
pin_depth = 12;

/* [Split for printers smaller than the frame] */
split_y = 85;
lap = 16;

/* [Hidden] */
$fn = 48;
eps = 0.01;
pi_board = [56, 85];  // Pi lying vertically: GPIO edge left, USB-C right, USB-A at top
m_x = (frame_w - rabbet_w) / 2;
m_y = (frame_h - rabbet_h) / 2;
hdr = [m_x + hdr_x, m_y + hdr_y];
pod_cx = frame_w / 2;
pod_x0 = pod_cx - pod_w / 2;
pod_x1 = pod_cx + pod_w / 2;
pod_in_x0 = pod_x0 + wall;
pod_in_x1 = pod_x1 - wall;
pod_in_y0 = pod_y0 + wall;
board0 = [pod_in_x1 - cable_room - pi_board.x, pod_in_y0 + cable_room];
pod_in_y1 = board0.y + pi_board.y + plug_room;
pod_y1 = pod_in_y1 + wall;
pod_in_h = boss_h + 1.6 + pi_tall + 3;        // above the plate top
top_z = plate_t + pod_in_h + roof_t;          // top of pod, spine and hinge base
axis_y = pod_y1 + hinge_r + 1.5;
axis_z = top_z + hinge_gap + hinge_r;
hinge_y1 = axis_y + hinge_r + 2;              // top edge of the hinge base
flap_len = axis_y - 3;
// Stop tab behind the hinge: it touches the hinge base exactly at `stand_open`.
tail = (hinge_r + hinge_gap - hinge_r * cos(stand_open)) / sin(stand_open);
function on_plate(p) = [board0.x + pi_board.x - p.y, board0.y + p.x];
pi_holes = [for (x = [3.5, 61.5], y = [3.5, 52.5]) on_plate([x, y])];
fan_c = on_plate(fan_at);
cover_bosses = [for (x = [pod_in_x0 + 3.5, pod_in_x1 - 3.5], y = [pod_in_y0 + 3.5, pod_in_y1 - 3.5]) [x, y]];
hdr0 = hdr - hdr_open / 2;
hdr1 = hdr + hdr_open / 2;

assert(hdr0.x >= pod_in_x0 && hdr1.x <= pod_in_x1 && hdr0.y >= pod_in_y0 && hdr1.y <= pod_in_y1,
       "the display header must lie inside the pod: move pod_y0 or widen pod_w");
assert(hdr1.x + 2 < board0.x, "the display header is under the Pi: widen pod_w");
for (b = cover_bosses)
    assert(b.x + 3.5 < hdr0.x || b.x - 3.5 > hdr1.x || b.y + 3.5 < hdr0.y || b.y - 3.5 > hdr1.y,
           "a cover screw boss is over the display header opening");
assert(split_y + lap / 2 < pod_y0, "the split seam runs through the pod: lower split_y");
assert(hinge_y1 < frame_h - 5, "the stand hinge is above the top of the frame");
assert(!fan || pod_in_h - boss_h - 1.6 - fan_t >= 8, "no room for the fan above the Pi's heatsinks");

echo(str("pod ", pod_w, " x ", pod_y1 - pod_y0, " mm, ", top_z, " mm deep; stand ", pod_w, " x ",
         flap_len, " mm; stop tab ", tail, " mm"));

// ---- helpers ---------------------------------------------------------------

module rbox2d(p0, p1, r) { translate(p0) offset(r = r) offset(delta = -r) square(p1 - p0); }

// Rectangle with selectively rounded corners: round = [bottom-left, bottom-right, top-right, top-left].
module rbox2d_sel(p0, p1, r, round) {
    pts = [[p0.x, p0.y], [p1.x, p0.y], [p1.x, p1.y], [p0.x, p1.y]];
    dirs = [[1, 1], [-1, 1], [-1, -1], [1, -1]];
    hull() for (i = [0 : 3])
        if (round[i]) translate(pts[i] + dirs[i] * r) circle(r = r);
        else translate(pts[i] + (dirs[i] - [1, 1]) * 0.005) square(0.01);
}

// Block with (selectively) rounded corners and a chamfered top edge.
module soft_block(p0, p1, z0, h, r = radius, ch = chamfer, round = [1, 1, 1, 1]) {
    hull() {
        translate([0, 0, z0]) linear_extrude(h - ch) rbox2d_sel(p0, p1, r, round);
        translate([0, 0, z0 + h - ch]) linear_extrude(ch)
            rbox2d_sel(p0 + [ch, ch], p1 - [ch, ch], max(r - ch, 0.5), round);
    }
}

module countersunk(d, head, depth) {
    translate([0, 0, -1]) cylinder(d = d, h = depth + 2);
    translate([0, 0, depth - (head - d) / 2]) cylinder(d1 = d, d2 = head + eps, h = (head - d) / 2 + eps);
}

module screw_positions() {
    for (x = [m_x / 2, frame_w / 2, frame_w - m_x / 2], y = [m_y / 2, frame_h - m_y / 2])
        translate([x, y]) children();
    for (x = [m_x / 2, frame_w - m_x / 2]) translate([x, frame_h / 2]) children();
}

// ---- back plate (with spine, bosses and hinge base) ------------------------

module back() {
    difference() {
        union() {
            soft_block([0, 0], [frame_w, frame_h], 0, plate_t);
            // spine: hollow cable channel from the pod to the bottom edge
            soft_block([pod_cx - spine_w / 2, 0], [pod_cx + spine_w / 2, pod_y0 - 0.3], 0, top_z, r = 2);
            // hinge base above the pod, with a tower at each end for the stand's pivots
            soft_block([pod_x0, pod_y1 + 0.3], [pod_x1, hinge_y1], 0, top_z, round = [0, 0, 1, 1]);
            for (x = [pod_x0, pod_x1 - knuckle_w])
                hull() {
                    translate([x, axis_y - hinge_r - 2, top_z - eps]) cube([knuckle_w, 2 * hinge_r + 4, eps]);
                    translate([x, axis_y, axis_z]) rotate([0, 90, 0]) cylinder(r = hinge_r, h = knuckle_w);
                }
            // Pi standoffs and the cover's screw bosses
            for (p = pi_holes) translate([p.x, p.y, plate_t - eps]) cylinder(d = boss_d, h = boss_h + eps);
            for (b = cover_bosses) translate([b.x, b.y, plate_t - eps]) cylinder(d = 7, h = top_z - roof_t - plate_t + eps);
            // low lip that locates the pod cover
            translate([0, 0, plate_t - eps]) linear_extrude(1.5)
                difference() {
                    rbox2d([pod_in_x0 + 0.3, pod_in_y0 + 0.3], [pod_in_x1 - 0.3, pod_in_y1 - 0.3], radius - wall);
                    rbox2d([pod_in_x0 + 1.9, pod_in_y0 + 1.9], [pod_in_x1 - 1.9, pod_in_y1 - 1.9], radius - wall);
                }
        }
        // spine tunnel, open at the bottom edge and into the pod
        translate([pod_cx - spine_w / 2 + wall, -1, plate_t])
            cube([spine_w - 2 * wall, pod_y0 + 2, top_z - roof_t - plate_t]);
        translate([pod_cx - spine_w / 2 + wall, pod_in_y0 - 1, plate_t - 1]) cube([spine_w - 2 * wall, 4, 3]);
        // display header opening
        translate([hdr0.x, hdr0.y, -1]) cube([hdr_open.x, hdr_open.y, plate_t + 2]);
        for (p = pi_holes) translate([p.x, p.y, plate_t]) cylinder(d = boss_hole_d, h = boss_h + 1);
        for (b = cover_bosses) translate([b.x, b.y, plate_t]) cylinder(d = cover_pilot, h = top_z);
        // stand pivots (self-tapping into the towers)
        translate([pod_x0 - 1, axis_y, axis_z]) rotate([0, 90, 0]) cylinder(d = pin_tap_d, h = pod_w + 2);
        screw_positions() countersunk(screw_d, screw_head_d, plate_t);
        // the glue seam becomes a deliberate design line
        translate([-1, split_y - lap / 2 - 0.6, plate_t - 0.6]) cube([frame_w + 2, 1.2, 1]);
    }
}

// Everything below the seam, plus the lower half of the plate over the lap.
module lower_region() {
    translate([-1, -1, -1]) cube([frame_w + 2, split_y - lap / 2 + 1, 200]);
    translate([-1, split_y - lap / 2 - eps, -1]) cube([frame_w + 2, lap + 2 * eps, 1 + plate_t / 2]);
}

// ---- pod cover (frame coordinates; printed roof-down) ----------------------

module pod_cover() {
    difference() {
        soft_block([pod_x0, pod_y0], [pod_x1, pod_y1], plate_t, top_z - plate_t, round = [1, 1, 0, 0]);
        // hollow, open at the plate side
        translate([0, 0, plate_t - 1]) linear_extrude(top_z - roof_t - plate_t + 1)
            rbox2d([pod_in_x0, pod_in_y0], [pod_in_x1, pod_in_y1], radius - wall);
        // cables pass into the spine through the bottom wall
        translate([pod_cx - spine_w / 2 + wall, pod_y0 - 1, plate_t - 1])
            cube([spine_w - 2 * wall, wall + 2, top_z - roof_t - plate_t + 1]);
        // intake vents in the bottom wall, either side of the spine
        for (s = [-1, 1], i = [0 : 2])
            translate([pod_cx + s * (spine_w / 2 + 6 + i * 9) - 2.5, pod_y0 - 1, plate_t + 4]) cube([5, wall + 2, 12]);
        // fan grille and screw holes in the roof
        if (fan) translate([fan_c.x, fan_c.y, top_z - roof_t - 1]) {
            intersection() {
                cylinder(d = fan_size - 2, h = roof_t + 2);
                for (i = [-3 : 3]) translate([i * 4 - 1.25, -fan_size / 2, 0]) cube([2.5, fan_size, roof_t + 2]);
            }
            for (sx = [-1, 1], sy = [-1, 1])
                translate([sx * fan_hole_spacing / 2, sy * fan_hole_spacing / 2, 0]) cylinder(d = fan_screw_d, h = roof_t + 2);
        }
        // cover screws (hidden under the stand when it is closed)
        for (b = cover_bosses) translate([b.x, b.y, top_z - roof_t]) countersunk(cover_screw, 6.4, roof_t);
    }
}

// ---- stand ------------------------------------------------------------------
// Local coordinates: hinge axis along X through the origin, flap towards -Y,
// underside (towards the pod when folded) at z = -hinge_r.

module stand() {
    inner = pod_w / 2 - knuckle_w - knuckle_clear;
    difference() {
        union() {
            // flap, clear of the hinge towers
            translate([0, 0, -hinge_r]) soft_block([-pod_w / 2, -flap_len], [pod_w / 2, -hinge_r - 2], 0, flap_t);
            // centre knuckle joined to the flap, with the stop tab behind the axis
            hull() {
                rotate([0, 90, 0]) cylinder(r = hinge_r, h = 2 * inner, center = true);
                translate([-inner, -hinge_r - 3, -hinge_r]) cube([2 * inner, 1, flap_t]);
                translate([-inner, 0, -hinge_r]) cube([2 * inner, tail, eps]);
            }
        }
        for (s = [-1, 1])
            translate([s * (inner - pin_depth / 2 + eps), 0, 0]) rotate([0, 90, 0]) cylinder(d = pin_d, h = pin_depth, center = true);
        // vent slots over the fan, so it can breathe with the stand closed
        if (fan) for (i = [-2 : 2])
            translate([fan_c.x - pod_cx + i * 7 - 2, fan_c.y - axis_y - 17, -hinge_r - 1]) cube([4, 34, flap_t + 2]);
    }
}

module stand_in_place(angle) {
    translate([pod_cx, axis_y, axis_z]) rotate([-angle, 0, 0]) stand();
}

// ---- output -----------------------------------------------------------------

if (part == "back") back();
else if (part == "back_lower") intersection() { back(); lower_region(); }
else if (part == "back_upper") difference() { back(); lower_region(); }
else if (part == "pod_cover") translate([0, 0, top_z]) mirror([0, 0, 1]) pod_cover();
else if (part == "stand") translate([0, 0, hinge_r]) stand();
else {
    color("#ece8e1") back();
    color("#dcd6cc") pod_cover();
    color("#c9c1b3") stand_in_place(stand_open);
}
