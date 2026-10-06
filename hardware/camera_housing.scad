// GibBird — weatherproof housing for a small USB board camera (e.g. a 38 x 38 mm
// 4K board camera with an M12 lens), plus a tilting bracket.
//
// Use orientation: the camera looks along +Z, +Y is up. The open back (z = 0) is closed
// by the lid, which carries a PG9 cable gland (big enough to pass a USB-A plug).
// A glass or acrylic disc behind the front opening is the window; a visor keeps rain
// and sun off it. The board is held by four corner stops and pressed into place by
// pegs on the lid, so it needs no screws.
//
// Print in PETG or ASA (not PLA: sun and heat), 4 walls, 30 % infill.
//   body:    back opening on the bed, no supports
//   lid:     flat side down
//   bracket: base plate on the bed
//
// Hardware: 4x M3 x 12 (lid), 2x M4 x 12 + washers (tilt, self-tap into the ears),
// PG9 cable gland, 30 mm round x 2 mm glass/acrylic disc + clear silicone,
// 2 mm silicone O-ring cord (or 2 mm foam gasket tape), a silica gel sachet.

part = "assembly"; // [assembly, body, lid, bracket]

/* [Camera board: MEASURE YOURS] */
board = [38, 38];
board_t = 1.6;
lens_len = 22;        // board front face -> front of the lens
behind = 18;          // room behind the board for the connector and the gland

/* [Window] */
disc_d = 30;          // round glass/acrylic window
disc_t = 2;
win_d = 26;           // visible opening (keep wider than the lens's view cone)
visor_len = 18;

/* [Box] */
wall = 3.2;
clear = 4;            // space around the board on each side
front_t = 3;
corner_col = 6;       // board stops in the corners
boss_d = 9;
screw_pilot = 2.6;    // M3 self-taps into the body
screw_clear = 3.4;
oring_w = 1.8;        // groove for 2 mm cord in the back rim
oring_depth = 1.4;

/* [Cable] */
gland_d = 15.6;       // PG9 thread
weep_d = 2;           // tiny drain hole at the lowest front corner

/* [Mount] */
ear_t = 6;
ear = 16;
pivot_pilot = 3.4;    // M4 self-taps into the ears
pivot_clear = 4.4;
arm_t = 5;
base = [70, 28, 4];
base_screw = 4.5;

/* [Hidden] */
$fn = 64;
eps = 0.01;
in_w = board.x + 2 * clear;
in_h = board.y + 2 * clear;
W = in_w + 2 * wall;
H = in_h + 2 * wall;
standoff = lens_len + 1;                   // lens stops 1 mm behind the window
D_in = standoff + board_t + behind;
D = D_in + front_t;
board_z = D_in - standoff - board_t;      // board back face
corners = [for (sx = [-1, 1], sy = [-1, 1]) [sx, sy]];
boss_xy = [W / 2 - 1, H / 2 - 1];
pivot_z = D / 2;
pivot_h = sqrt(pow(H / 2 + boss_d / 2, 2) + pow(D / 2 + visor_len, 2)) + 3;  // room to tilt
arm_gap = W + 2 * ear_t + 2;

echo(str("housing ", W, " x ", H, " x ", D + visor_len, " mm; board back at z = ", board_z));

module rrect(size, r) { offset(r = r) offset(delta = -r) square(size, center = true); }

module body() {
    difference() {
        union() {
            linear_extrude(D) rrect([W, H], 3);
            for (c = corners) translate([c.x * boss_xy.x, c.y * boss_xy.y, 0]) cylinder(d = boss_d, h = D);
            // ears for the tilt bracket
            for (s = [-1, 1])
                translate([s * (W / 2 + ear_t / 2 - eps), 0, pivot_z])
                    rotate([0, 90, 0]) cylinder(d = ear, h = ear_t, center = true);
            visor();
        }
        // cavity, window and the disc's seat on the inside of the front wall
        translate([0, 0, -1]) linear_extrude(D_in + 1) rrect([in_w, in_h], 1.5);
        translate([0, 0, D_in - 1]) cylinder(d = win_d, h = front_t + 2);
        translate([0, 0, D_in - eps]) cylinder(d = disc_d + 0.4, h = disc_t);
        // lid screws, O-ring groove in the back rim
        for (c = corners) translate([c.x * boss_xy.x, c.y * boss_xy.y, -1]) cylinder(d = screw_pilot, h = 14);
        translate([0, 0, -1]) linear_extrude(oring_depth + 1) difference() {
            rrect([in_w + wall + oring_w, in_h + wall + oring_w], 2);
            rrect([in_w + wall - oring_w, in_h + wall - oring_w], 2);
        }
        // weep hole at the front of the bottom wall
        translate([0, -H / 2 - 1, D_in - 4]) rotate([-90, 0, 0]) cylinder(d = weep_d, h = wall + 2);
        // blind pilot holes in the ears (they must not reach the cavity)
        for (s = [-1, 1])
            translate([s * (W / 2 + ear_t + 1), 0, pivot_z])
                rotate([0, s > 0 ? -90 : 90, 0]) cylinder(d = pivot_pilot, h = ear_t + 1);
    }
    // board stops in the corners; their back ends are chamfered so they print without support
    for (c = corners)
        translate([c.x * (in_w / 2 - corner_col / 2), c.y * (in_h / 2 - corner_col / 2), 0])
            hull() {
                translate([0, 0, board_z + board_t]) linear_extrude(D_in - board_z - board_t) square(corner_col, center = true);
                translate([c.x * corner_col / 2, c.y * corner_col / 2, board_z + board_t - corner_col])
                    cube([eps, eps, eps], center = true);
            }
}

module visor() {
    // roof + side cheeks around the window, sloping down towards the front
    translate([0, 0, D - eps]) {
        hull() {
            translate([-W / 2, H / 2 - 2, 0]) cube([W, 2, eps]);
            translate([-W / 2, H / 2 - 6, visor_len]) cube([W, 2, eps]);
        }
        for (s = [-1, 1])
            hull() {
                translate([s * (W / 2 - 1) - 1, -H / 4, 0]) cube([2, H / 4 + H / 2, eps]);
                translate([s * (W / 2 - 1) - 1, H / 2 - 6, visor_len]) cube([2, 4, eps]);
            }
    }
}

module lid() {
    lid_t = 3.5;
    lip = 4;
    difference() {
        union() {
            hull() for (c = corners) translate([c.x * boss_xy.x, c.y * boss_xy.y, 0]) cylinder(d = boss_d, h = lid_t);
            // alignment lip inside the box
            translate([0, 0, lid_t - eps]) linear_extrude(lip) difference() {
                rrect([in_w - 0.6, in_h - 0.6], 1.2);
                rrect([in_w - 4.6, in_h - 4.6], 1);
            }
            // pegs that press the board's corners against the stops (0.5 mm short: add foam)
            for (c = corners)
                translate([c.x * (board.x / 2 - 3), c.y * (board.y / 2 - 3), lid_t - eps])
                    cylinder(d = 4, h = board_z - 0.5 + eps);
        }
        for (c = corners) translate([c.x * boss_xy.x, c.y * boss_xy.y, -1]) {
            cylinder(d = screw_clear, h = lid_t + 2);
            cylinder(d1 = 6.4, d2 = screw_clear, h = 1.6);  // countersink on the outside
        }
        translate([0, 0, -1]) cylinder(d = gland_d, h = lid_t + 2);
    }
}

module bracket() {
    // base plate (screw it on, or stick it with outdoor VHB tape) + two tilt arms
    difference() {
        union() {
            translate([-base.x / 2, -base.y / 2, 0]) cube(base);
            for (s = [-1, 1])
                hull() {
                    translate([s * (arm_gap / 2 + arm_t / 2), 0, base.z / 2]) cube([arm_t, base.y, base.z], center = true);
                    translate([s * (arm_gap / 2 + arm_t / 2), 0, pivot_h]) rotate([0, 90, 0]) cylinder(d = ear, h = arm_t, center = true);
                }
        }
        for (s = [-1, 1]) {
            translate([s * (arm_gap / 2 + arm_t / 2), 0, pivot_h]) rotate([0, 90, 0]) cylinder(d = pivot_clear, h = arm_t + 2, center = true);
            translate([s * (base.x / 2 - 7), 0, -1]) {
                cylinder(d = base_screw, h = base.z + 2);
                translate([0, 0, base.z - 2 + 1]) cylinder(d1 = base_screw, d2 = base_screw + 4, h = 2 + eps);
            }
        }
    }
}

if (part == "body") body();
else if (part == "lid") lid();
else if (part == "bracket") bracket();
else {
    tilt = 15;
    color("dimgray") bracket();
    translate([0, 0, pivot_h]) rotate([90 + tilt, 0, 0]) translate([0, 0, -pivot_z]) {
        color("silver") body();
        color("gray") translate([0, 0, -12]) lid();
        color("lightblue", 0.5) translate([0, 0, D_in]) cylinder(d = disc_d, h = disc_t);
        color("green") translate([-board.x / 2, -board.y / 2, board_z]) cube([board.x, board.y, board_t]);
    }
}
