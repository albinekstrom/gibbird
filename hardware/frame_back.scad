// GibBird — 3D-printed back cover with a flip-out stand for an A4 picture frame
// holding a Pimoroni Inky Impression 13.3", with a Raspberry Pi 4 or 5 hidden behind it.
//
// Coordinates are seen FROM THE BACK with the frame standing in portrait.
// Origin = bottom-left corner of the frame's back face, Z points away from the display.
//
// The cover screws onto the back of the wooden frame (6 small wood screws). A vented
// hood hides the Pi (Pi 4 and Pi 5 share the same footprint), which sits on 4 bosses next to an opening
// over the display's 40-pin header; a short ribbon cable joins the two inside the hood.
// The power and camera cables leave through the hood's right wall, are held by clips and
// zip-tie anchors, and pass under the stand's foot. A 30 mm fan exhausts through the roof.
// The stand folds flat around the hood and flips out to a fixed angle.
//
// Workflow: measure your frame + display, edit the [Frame] and [Display header] values,
// pick a `part`, press F6 (render), then File > Export > STL.

part = "assembly"; // [assembly, back, back_lower, back_upper, stand]

/* [Frame: MEASURE YOURS] */
// Defaults: BGA "Galant" A4 frame (22.7 x 31.4 cm, 13 mm profile, 8 mm rabbet).
frame_w = 227;        // outer width of the frame (portrait)
frame_h = 314;        // outer height
rabbet_w = 211;       // size of the opening on the back where the display sits
rabbet_h = 298;
// Depth from the frame's back face down to the display's back (PCB). If the display
// sticks out behind the frame, use a deeper frame (or print spacer strips).
display_recess = 2.5;  // 8 mm rabbet - ~2 mm acrylic - ~3.5 mm display

/* [Display header: centre of the Inky's 40-pin header, from the rabbet's bottom-left] */
hdr_x = 62;           // estimated from photos: measure yours!
hdr_y = 137;
hdr_open = [16, 66];  // opening for header + ribbon plug (header runs vertically)

/* [Raspberry Pi 4 / 5] */
ribbon_gap = 6;       // space between the header opening and the Pi
boss_h = 4;           // Pi stands this far above the plate
boss_d = 6;
boss_hole_d = 2.2;    // M2.5 x 6 screws self-tap
pi_tall = 16;         // tallest part above the Pi's board (USB-A stack)
plug_room = 20;       // room above the USB-A ports for a right-angle plug
power_slot = [14, 10];   // USB-C power plug passes through (width along wall, height)
usb_slot = [18, 12];     // USB camera cable (USB-A right-angle plug) passes through
// Flat camera cable (Camera Module via CSI). Pi 4: connector 45 mm from the GPIO end.
// Set csi_slot = [20, 6] to add it; off by default (long runs use a USB camera).
csi_slot = [0, 0];
csi_at = 45;

/* [Fan: 30 mm 5 V fan (e.g. the "Pi-Fan" from a Pi 4 case), exhausting through the roof] */
fan = true;
fan_size = 30;
fan_t = 7;
fan_hole_spacing = 24;
fan_screw_d = 3.2;    // the fan's own screws go through the roof into the fan
fan_at = [29, 32];    // over the SoC, in Pi board coordinates (Pi 4: SoC ~29 mm from the GPIO end)

/* [Back plate] */
plate_t = 3.2;
corner_r = 4;
wall = 2;
screw_d = 2.9;        // wood screws 2.5 x 10 mm, countersunk (pre-drill 1.5 mm)
screw_head_d = 5.2;

/* [Stand] */
stand_open = 35;      // how far the stand swings open (deg). More = leans back further.
hinge_y = 255;        // hinge axis height, from the bottom of the frame
stand_len = 240;      // hinge axis -> foot
stand_w = 170;
bar_w = 12;
stand_t = 6;
hinge_r = 5;
hinge_gap = 0.6;      // clearance between folded stand and plate
pin_d = 3.3;          // stand pivots on the smooth shank of an M3 x 16 screw...
pin_tap_d = 2.8;      // ...which self-taps into the hinge block
pin_depth = 12;
block_w = 6;
block_clear = 0.5;

/* [Cables] */
cable_xs = [160, 172];   // where power + camera cables run down (frame coordinates)
cable_d = 6;             // cable thickness the clips and foot arch are sized for
clip_ys = [45, 120];
tie_ys = [36];           // zip-tie anchors on each cable path (plus one below each hood slot)

/* [Split for printers smaller than the frame] */
split_y = 85;        // seam height; keep it clear of the hood
lap = 16;             // glued lap joint length

/* [Hidden] */
$fn = 48;
eps = 0.01;
pi_board = [56, 85];  // Pi lying vertically: GPIO edge left, USB-C right, USB-A at top
m_x = (frame_w - rabbet_w) / 2;
m_y = (frame_h - rabbet_h) / 2;
hdr = [m_x + hdr_x, m_y + hdr_y];
board0 = [hdr.x + hdr_open.x / 2 + ribbon_gap, hdr.y - 37];   // board bottom-left corner
board_z = plate_t + boss_h;
hood_in0 = [hdr.x - hdr_open.x / 2 - 4, board0.y - 6];
hood_in1 = [board0.x + pi_board.x + 4, board0.y + pi_board.y + plug_room];
hood_in_h = boss_h + 1.6 + pi_tall + 3;                         // above the plate top
hood_out0 = hood_in0 - [wall, wall];
hood_out1 = hood_in1 + [wall, wall];
axis_z = plate_t + hinge_r + hinge_gap;
stand_cx = frame_w / 2;
leg_in0 = stand_cx - stand_w / 2 + bar_w;
leg_in1 = stand_cx + stand_w / 2 - bar_w;
// Length of the stop tab behind the hinge: it touches the plate exactly at `stand_open`.
tail = (hinge_r + hinge_gap - hinge_r * cos(stand_open)) / sin(stand_open);
// Pi holes / ports, mapped from board coordinates (x along 85 mm, y along 56 mm,
// USB-C edge at y = 0) to the rotated position on the plate.
function on_plate(p) = [board0.x + pi_board.x - p.y, board0.y + p.x];
pi_holes = [for (x = [3.5, 61.5], y = [3.5, 52.5]) on_plate([x, y])];
power_y = on_plate([11.2, 0]).y;
csi_y = on_plate([csi_at, 0]).y;
fan_c = on_plate(fan_at);
usb_y = board0.y + pi_board.y + plug_room / 2;

assert(hood_out0.x > leg_in0, "hood hits the left stand leg: move hdr_x or narrow the stand");
assert(hood_out1.x + cable_d < min(cable_xs) - cable_d / 2, "cables must run right of the hood");
assert(max(cable_xs) + cable_d < leg_in1, "cables hit the right stand leg");
assert(hood_out1.y < hinge_y - hinge_r - bar_w, "hood hits the stand's top bar: raise hinge_y");
assert(hood_out0.y > hinge_y - stand_len + bar_w, "hood hits the stand's foot");
assert(hood_out0.y > split_y + lap / 2, "split seam runs through the hood: lower split_y");
assert(stand_w / 2 + block_clear + block_w < frame_w / 2, "stand too wide for the frame");
assert(!fan || hood_in_h - boss_h - 1.6 - fan_t >= 8, "no room for the fan above the Pi's heatsinks");

echo(str("stop tab ", tail, " mm; hood sticks out ", hood_in_h + wall, " mm behind the plate; ",
         "hood ", hood_out1 - hood_out0, " mm"));

module rrect(size, r) { offset(r = r) offset(delta = -r) square(size); }

module screw_positions() {
    for (x = [m_x / 2, frame_w / 2, frame_w - m_x / 2], y = [m_y / 2, frame_h - m_y / 2])
        translate([x, y]) children();
    for (x = [m_x / 2, frame_w - m_x / 2]) translate([x, frame_h / 2]) children();
}

module hood() {
    translate(hood_out0) linear_extrude(plate_t + hood_in_h + wall) rrect(hood_out1 - hood_out0, 3);
    for (p = pi_holes) translate([p.x, p.y, plate_t - eps]) cylinder(d = boss_d, h = boss_h + eps);
}

module hood_cuts() {
    // hollow inside (stops at the plate top, except over the display header)
    translate([hood_in0.x, hood_in0.y, plate_t]) difference() {
        cube([hood_in1.x - hood_in0.x, hood_in1.y - hood_in0.y, hood_in_h]);
        for (p = pi_holes) translate([p.x - hood_in0.x, p.y - hood_in0.y, -1]) cylinder(d = boss_d, h = boss_h + 1);
    }
    translate([hdr.x - hdr_open.x / 2, hdr.y - hdr_open.y / 2, -1]) cube([hdr_open.x, hdr_open.y, plate_t + 2]);
    for (p = pi_holes) translate([p.x, p.y, plate_t]) cylinder(d = boss_hole_d, h = boss_h + 1);
    // roof: fan grille + screw holes (or plain vents), low intake vents in the bottom wall
    roof_z = plate_t + hood_in_h - 1;
    if (fan) {
        translate([fan_c.x, fan_c.y, roof_z]) {
            intersection() {
                cylinder(d = fan_size - 2, h = wall + 2);
                for (i = [-3 : 3]) translate([i * 4 - 1.25, -fan_size / 2, 0]) cube([2.5, fan_size, wall + 2]);
            }
            for (sx = [-1, 1], sy = [-1, 1])
                translate([sx * fan_hole_spacing / 2, sy * fan_hole_spacing / 2, 0]) cylinder(d = fan_screw_d, h = wall + 2);
        }
    } else {
        for (i = [0 : 3])
            translate([board0.x + 6 + i * 12, board0.y + 10, roof_z]) cube([5, pi_board.y - 20, wall + 2]);
    }
    for (i = [0 : 4])
        translate([hood_in0.x + 8 + i * 14, hood_out0.y - 1, plate_t + 3]) cube([7, wall + 2, 8]);
    // cable slots in the right wall: USB-C power next to its port, camera ribbon, USB at the top
    translate([hood_in1.x - 1, power_y - power_slot.x / 2, board_z]) cube([wall + 2, power_slot.x, power_slot.y]);
    translate([hood_in1.x - 1, usb_y - usb_slot.x / 2, board_z]) cube([wall + 2, usb_slot.x, usb_slot.y]);
    if (csi_slot.x > 0)
        translate([hood_in1.x - 1, csi_y - csi_slot.x / 2, board_z + 4]) cube([wall + 2, csi_slot.x, csi_slot.y]);
}

module hinge_blocks() {
    for (s = [-1, 1]) {
        x0 = s > 0 ? stand_cx + stand_w / 2 + block_clear : stand_cx - stand_w / 2 - block_clear - block_w;
        translate([x0, 0, 0]) hull() {
            translate([0, hinge_y - hinge_r - 3, plate_t - eps]) cube([block_w, 2 * hinge_r + 6, eps]);
            translate([0, hinge_y, axis_z]) rotate([0, 90, 0]) cylinder(r = hinge_r, h = block_w);
        }
    }
}

module hinge_holes() {
    translate([stand_cx - stand_w / 2 - block_clear - block_w - 1, hinge_y, axis_z])
        rotate([0, 90, 0]) cylinder(d = pin_tap_d, h = stand_w + 2 * (block_clear + block_w) + 2);
}

module cable_clip(x, y) {
    // L-shaped hook, open on the +x side so the cable snaps in sideways
    t = 1.6; d = 8;
    translate([x - cable_d / 2 - t, y - d / 2, plate_t - eps]) {
        cube([t, d, cable_d + t]);
        translate([0, 0, cable_d]) cube([cable_d + t - 1.5, d, t]);
    }
}

module tie_anchor(x, y) {
    // bridge with a tunnel for a zip tie (up to 3.6 mm wide) that wraps the cable
    translate([x - 5, y - 3, plate_t - eps]) difference() {
        cube([10, 6, 3.5]);
        translate([-1, 1, -1]) cube([12, 4, 2.8]);
    }
}

module back() {
    difference() {
        union() {
            linear_extrude(plate_t) rrect([frame_w, frame_h], corner_r);
            hood();
            hinge_blocks();
            for (x = cable_xs, y = clip_ys) cable_clip(x, y);
            for (x = cable_xs, y = concat(tie_ys, [power_y - 14])) tie_anchor(x, y);
        }
        hood_cuts();
        hinge_holes();
        screw_positions() {
            translate([0, 0, -1]) cylinder(d = screw_d, h = plate_t + 2);
            translate([0, 0, plate_t - (screw_head_d - screw_d) / 2])
                cylinder(d1 = screw_d, d2 = screw_head_d + eps, h = (screw_head_d - screw_d) / 2 + eps);
        }
    }
}

// Everything below the seam, plus the lower half of the plate over the lap.
module lower_region() {
    translate([-1, -1, -1]) cube([frame_w + 2, split_y - lap / 2 + 1, 200]);
    translate([-1, split_y - lap / 2 - eps, -1]) cube([frame_w + 2, lap + 2 * eps, 1 + plate_t / 2]);
}

module stand() {
    // Local coordinates: hinge axis along X through the origin, legs towards -Y,
    // underside (the face towards the plate when folded) at z = -hinge_r.
    arch_x0 = min(cable_xs) - cable_d / 2 - 1 - stand_cx;
    arch_w = max(cable_xs) - min(cable_xs) + cable_d + 2;
    difference() {
        union() {
            hull() {
                rotate([0, 90, 0]) cylinder(r = hinge_r, h = stand_w, center = true);
                translate([-stand_w / 2, 0, -hinge_r]) cube([stand_w, tail, eps]);  // stop tab
            }
            translate([-stand_w / 2, -bar_w, -hinge_r]) cube([stand_w, bar_w, stand_t]);
            for (x = [-stand_w / 2, stand_w / 2 - bar_w])
                translate([x, -stand_len, -hinge_r]) cube([bar_w, stand_len, stand_t]);
            translate([-stand_w / 2, -stand_len, -hinge_r]) cube([stand_w, bar_w, stand_t]);
            // thicker foot where the cables pass underneath
            translate([arch_x0 - 4, -stand_len, -hinge_r]) cube([arch_w + 8, bar_w, cable_d + 4]);
        }
        for (s = [-1, 1])
            translate([s * (stand_w / 2 - pin_depth / 2 + eps), 0, 0])
                rotate([0, 90, 0]) cylinder(d = pin_d, h = pin_depth, center = true);
        translate([arch_x0, -stand_len - 1, -hinge_r - eps]) cube([arch_w, bar_w + 2, cable_d - hinge_gap]);
    }
}

module stand_in_place(angle) {
    translate([stand_cx, hinge_y, axis_z]) rotate([-angle, 0, 0]) stand();
}

if (part == "back") back();
else if (part == "back_lower") intersection() { back(); lower_region(); }
else if (part == "back_upper") difference() { back(); lower_region(); }
else if (part == "stand") translate([0, 0, hinge_r]) stand();  // print flat side down
else {
    color("burlywood") back();
    color("tan") stand_in_place(stand_open);
    color("green") translate([board0.x, board0.y, board_z]) cube([pi_board.x, pi_board.y, 1.6]);
}
