// GibBird — 3D-printed back cover with a flip-out stand for an A4 picture frame
// holding a Pimoroni Inky Impression 13.3" with a Raspberry Pi on its back.
//
// Coordinates are seen FROM THE BACK with the frame standing in portrait.
// Origin = bottom-left corner of the frame's back face, Z points away from the display.
//
// The cover screws onto the back of the wooden frame (6 small wood screws). It covers
// the Pi with a vented hood, guides the power cable to the bottom edge, and carries a
// rectangular stand that folds flat around the hood and flips out to a fixed angle.
//
// Workflow: measure your frame + display, edit the [Frame] and [Raspberry Pi] values,
// pick a `part`, press F6 (render), then File > Export > STL.

part = "assembly"; // [assembly, back, back_lower, back_upper, stand]

/* [Frame: MEASURE YOURS] */
frame_w = 251;        // outer width of the frame (portrait)
frame_h = 338;        // outer height
rabbet_w = 211;       // size of the opening on the back where the display sits
rabbet_h = 298;
// Depth from the frame's back face down to the display's back (PCB). If the display
// sticks out behind the frame, use a deeper frame (or print spacer strips).
display_recess = 2;

/* [Raspberry Pi: measured on the display back, from the rabbet's bottom-left corner] */
pi_cx = 84;           // centre of the Pi footprint
pi_cy = 140;
pi_box = [64, 72];    // clearance box (fits a Pi Zero 2 W or Pi 3 A+, either way round)
pi_stack_h = 18;      // display back -> top of the tallest part (Pi + header + plug)

/* [Back plate] */
plate_t = 3.2;
corner_r = 4;
wall = 2;
screw_d = 3.4;        // wood screws 3 x 12 mm, countersunk
screw_head_d = 6.6;

/* [Stand] */
stand_open = 35;      // how far the stand swings open (deg). More = leans back further.
hinge_y = 225;        // hinge axis height, from the bottom of the frame
stand_len = 210;      // hinge axis -> foot
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

/* [Cable] */
cable_x = 80;         // cable path, frame coordinates
cable_w = 9;          // slot width (flat or round micro-USB cable)
cable_h = 6;
clip_ys = [45, 85];

/* [Split for printers smaller than the frame] */
split_y = 110;        // seam height; keep it clear of the hood
lap = 16;             // glued lap joint length

/* [Hidden] */
$fn = 48;
eps = 0.01;
m_x = (frame_w - rabbet_w) / 2;
m_y = (frame_h - rabbet_h) / 2;
hood_c = [m_x + pi_cx, m_y + pi_cy];
hood_in_top = -display_recess + pi_stack_h + 2;   // inner roof height above plate bottom
hood_out = pi_box + [2 * wall, 2 * wall];
axis_z = plate_t + hinge_r + hinge_gap;
stand_cx = frame_w / 2;
// Length of the stop tab behind the hinge: it touches the plate exactly at `stand_open`.
tail = (hinge_r + hinge_gap - hinge_r * cos(stand_open)) / sin(stand_open);

assert(hood_in_top > plate_t + 2, "hood too low: check pi_stack_h / display_recess");
assert(cable_x > hood_c.x - pi_box.x / 2 + cable_w / 2 && cable_x < hood_c.x + pi_box.x / 2 - cable_w / 2,
       "cable_x must be inside the hood footprint");
assert(hood_c.x - hood_out.x / 2 > stand_cx - stand_w / 2 + bar_w, "hood hits the left stand leg");
assert(hood_c.x + hood_out.x / 2 < stand_cx + stand_w / 2 - bar_w, "hood hits the right stand leg");
assert(hood_c.y + hood_out.y / 2 < hinge_y - hinge_r - bar_w, "hood hits the stand's top bar");
assert(hood_c.y - hood_out.y / 2 > hinge_y - stand_len + bar_w, "hood hits the stand's foot");
assert(hood_c.y - hood_out.y / 2 > split_y + lap / 2, "split seam runs through the hood");
assert(stand_w / 2 + block_clear + block_w < frame_w / 2, "stand too wide for the frame");

echo(str("stop tab: ", tail, " mm; hood height above plate: ", hood_in_top + wall - plate_t, " mm"));

module rrect(size, r) { offset(r = r) offset(delta = -r) square(size); }

module screw_positions() {
    for (x = [m_x / 2, frame_w / 2, frame_w - m_x / 2], y = [m_y / 2, frame_h - m_y / 2])
        translate([x, y]) children();
    for (x = [m_x / 2, frame_w - m_x / 2]) translate([x, frame_h / 2]) children();
}

module hood() {
    translate([hood_c.x - hood_out.x / 2, hood_c.y - hood_out.y / 2, 0])
        linear_extrude(hood_in_top + wall) rrect(hood_out, 3);
}

module hood_cuts() {
    // through-opening for the Pi
    translate([hood_c.x - pi_box.x / 2, hood_c.y - pi_box.y / 2, -1])
        cube([pi_box.x, pi_box.y, hood_in_top + 1]);
    // vent slots in the roof
    for (i = [-2 : 2])
        translate([hood_c.x + i * 11 - 2.5, hood_c.y - pi_box.y / 2 + 10, hood_in_top - 1])
            cube([5, pi_box.y - 20, wall + 2]);
    // cable slot in the bottom wall
    translate([cable_x - cable_w / 2, hood_c.y - hood_out.y / 2 - 1, plate_t])
        cube([cable_w, wall + 2, cable_h]);
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

module cable_clip(y) {
    // L-shaped hook, open on the +x side so the cable snaps in sideways
    t = 1.6; d = 8; ch = cable_h - 1.5; cw = cable_w - 2;
    translate([cable_x - cw / 2 - t, y - d / 2, plate_t - eps]) {
        cube([t, d, ch + t]);
        translate([0, 0, ch]) cube([cw + t - 2, d, t]);
    }
}

module back() {
    difference() {
        union() {
            linear_extrude(plate_t) rrect([frame_w, frame_h], corner_r);
            hood();
            hinge_blocks();
            for (y = clip_ys) cable_clip(y);
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
            // thicker foot where the cable passes underneath
            translate([cable_x - stand_cx - cable_w / 2 - 4, -stand_len, -hinge_r])
                cube([cable_w + 8, bar_w, stand_t + 4]);
        }
        for (s = [-1, 1])
            translate([s * (stand_w / 2 - pin_depth / 2 + eps), 0, 0])
                rotate([0, 90, 0]) cylinder(d = pin_d, h = pin_depth, center = true);
        translate([cable_x - stand_cx - cable_w / 2, -stand_len - 1, -hinge_r - eps])
            cube([cable_w, bar_w + 2, cable_h - hinge_gap]);
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
    // ghost frame + display + Pi for orientation
    %translate([0, 0, -20]) difference() {
        cube([frame_w, frame_h, 20]);
        translate([m_x, m_y, -1]) cube([rabbet_w, rabbet_h, 22]);
    }
    %translate([m_x, m_y, -display_recess - 6]) cube([rabbet_w, rabbet_h, 6]);
    %translate([hood_c.x - 15, hood_c.y - 32.5, -display_recess]) cube([30, 65, pi_stack_h - 4]);
}
