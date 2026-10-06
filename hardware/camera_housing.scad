// GibBird — weatherproof housing v2 for a small USB board camera (default: the 38 x 38 mm
// IMX678 8MP 123° USB module), plus a tilting bracket that straps onto a balcony railing post.
//
// Use orientation: the camera looks along +Z, +Y is up. A smooth rounded shell with a
// rain hood over the window, sized from the lens's field of view so it never shows in
// the picture; the lid closes the back flush, with a gasket in
// a groove and a PG9 cable gland (big enough to pass a USB-A plug). All screws are
// inside the shell or under the lid. The board is held by four ribs and pressed into
// place by pegs on the lid, so it needs no screws.
//
// Built for Swedish weather (rain, snow, frost): print in ASA (best: UV- and cold-proof) or PETG,
// never PLA (brittle in frost, soft in sun). 4 walls, 30 % infill, no supports:
//   body:    back opening on the bed
//   lid:     outer face on the bed
//   bracket: base on the bed
//
// Mounting on the balcony railing (no drilling): two stainless hose clamps run through the
// tunnels in the bracket base and around a railing post; a groove in the back of the base
// centres it on the post. Put a strip of EPDM/rubber tape between bracket and post. The
// base also has two countersunk holes for screws or outdoor VHB tape on a flat surface.
//
// Hardware: 4x M3 x 12 + washers (lid), 2x M4 x 10 + washers (tilt, self-tapping),
// 2x stainless hose clamps (band <= 12 mm, size to fit post + base), PG9 cable gland,
// round glass/acrylic window disc (disc_d x 2 mm) + clear silicone, 2 mm silicone O-ring
// cord (or 2 mm foam gasket tape), a silica gel sachet.

part = "assembly"; // [assembly, body, lid, bracket]

/* [Camera board: MEASURE YOURS] */
board = [38, 38];
board_t = 1.6;
lens_len = 22;        // board front face -> front of the lens
lens_d = 12;          // diameter of the lens's front
fov_d = 123;          // diagonal field of view (IMX678 module: 123°)
aspect = [16, 9];
behind = 18;          // room behind the board for the connector and the gland

/* [Window] */
disc_t = 2;
hood_max = 20;        // rain/snow hood beyond the window; shortened automatically so the
                      // lens never sees it

/* [Shell] */
wall = 3.0;           // thick walls keep the camera's own heat in during winter
clear = 7;            // space around the board on each side (room for the screw bosses)
front_t = 3;
radius = 8;           // vertical edges
chamfer = 1.5;
boss = 7;             // lid screw bosses in the inside corners
screw_pilot = 2.6;    // M3 self-taps into the bosses
screw_clear = 3.4;
lid_t = 4;
groove_w = 1.8;       // gasket groove in the lid for 2 mm cord
groove_depth = 1.4;

/* [Cable] */
gland_d = 15.6;       // PG9 thread
weep_d = 2;

/* [Mount] */
pivot_boss_t = 5;     // round pads on the sides for the tilt screws
pivot_pilot = 3.4;    // M4 self-taps into the pads
pivot_clear = 4.4;
arm_t = 5;
arm_w = 16;
base = [76, 40, 8];   // thick enough for the hose-clamp tunnels
base_screw = 4.5;
post_w = 40;          // width of the railing post the bracket straps to (MEASURE)
strap = [13, 2.6];    // hose-clamp band tunnel (width, height)

/* [Hidden] */
$fn = 64;
eps = 0.01;
in_w = board.x + 2 * clear;
in_h = board.y + 2 * clear;
W = in_w + 2 * wall;
H = in_h + 2 * wall;
standoff = lens_len + 1;                   // lens stops 1 mm behind the window
// Field of view -> window size and the longest hood that stays out of the picture.
tan_d = tan(fov_d / 2);
tan_v = tan_d * aspect.y / norm(aspect);
win_d = ceil(lens_d + 2 * (front_t + 1) * tan_d + 1);
disc_d = win_d + 4;
hood_len = min(hood_max, floor((board.y / 2 + clear - win_d / 2) / tan_v) - 1);
D_in = standoff + board_t + behind;
D = D_in + front_t;
board_z = D_in - standoff - board_t;       // board's back face
corners = [for (sx = [-1, 1], sy = [-1, 1]) [sx, sy]];
boss_xy = [in_w / 2 - boss / 2, in_h / 2 - boss / 2];
pivot_z = D / 2;
arm_gap = W + 2 * pivot_boss_t + 1;
pivot_h = sqrt(pow(H / 2, 2) + pow(D / 2 + hood_len, 2)) + 3;   // room to tilt

echo(str("housing ", W, " x ", H, " x ", D + hood_len, " mm; window ", win_d, " mm, disc ", disc_d,
         " mm; hood ", hood_len, " mm; board back at z = ", board_z));
assert(disc_d / 2 < board.x / 2 - 2, "window disc too big to pass the board ribs: use a smaller lens_d/fov");

module rsquare(size, r) { offset(r = r) offset(delta = -r) square(size, center = true); }

module shell_solid(h) {
    hull() {
        linear_extrude(h - chamfer) rsquare([W, H], radius);
        translate([0, 0, h - chamfer]) linear_extrude(chamfer) rsquare([W - 2 * chamfer, H - 2 * chamfer], radius - chamfer);
    }
}

module body() {
    difference() {
        union() {
            shell_solid(D);
            // rain/snow hood: the roof continues past the window. Only the roof: with a
            // wide lens, side cheeks would show in the picture.
            translate([0, 0, D - eps]) difference() {
                intersection() {
                    linear_extrude(hood_len) rsquare([W, H], radius);
                    translate([-W, H / 2 - wall, 0]) cube([2 * W, wall, hood_len]);
                }
                // drip groove under the front edge, so water falls off instead of creeping back
                translate([-W, H / 2 - wall - 1, hood_len - 4]) cube([2 * W, 1.6, 1.6]);
            }
            // round pads for the tilt screws
            for (s = [-1, 1])
                translate([s * (W / 2 + pivot_boss_t / 2 - 1), 0, pivot_z])
                    rotate([0, 90, 0]) cylinder(d = arm_w, h = pivot_boss_t + 2, center = true);
        }
        // cavity
        translate([0, 0, -1]) linear_extrude(D_in + 1) rsquare([in_w, in_h], 2);
        // window, and the disc's seat on the inside of the front wall
        translate([0, 0, D_in - 1]) cylinder(d = win_d, h = front_t + 2);
        translate([0, 0, D_in - eps]) cylinder(d = disc_d + 0.4, h = disc_t);
        // weep hole at the front of the bottom wall
        translate([0, -H / 2 - 1, D_in - 4]) rotate([-90, 0, 0]) cylinder(d = weep_d, h = wall + 2);
        // blind pilot holes in the pads (they stop short of the cavity)
        for (s = [-1, 1])
            translate([s * (W / 2 + pivot_boss_t + 1), 0, pivot_z])
                rotate([0, s > 0 ? -90 : 90, 0]) cylinder(d = pivot_pilot, h = pivot_boss_t + 2.5);
    }
    // inside: lid screw bosses in the corners...
    difference() {
        for (c = corners) translate([c.x * boss_xy.x, c.y * boss_xy.y, 0]) linear_extrude(D_in) square(boss, center = true);
        for (c = corners) translate([c.x * boss_xy.x, c.y * boss_xy.y, -1]) cylinder(d = screw_pilot, h = 13);
    }
    // ...and a rib on each wall that the board rests against (chamfered: prints without support)
    rib_reach = in_w / 2 - board.x / 2 + 2;
    for (a = [0, 90, 180, 270]) rotate([0, 0, a])
        hull() {
            translate([in_w / 2 - rib_reach, -4, board_z + board_t]) cube([rib_reach, 8, D_in - board_z - board_t]);
            translate([in_w / 2 - eps, -4, board_z + board_t - rib_reach]) cube([eps, 8, eps]);
        }
}

module lid() {
    difference() {
        union() {
            linear_extrude(lid_t) rsquare([W, H], radius);
            // pegs that press the board against the ribs (0.5 mm short: add a dab of foam)
            for (a = [0, 90, 180, 270]) rotate([0, 0, a])
                translate([board.x / 2 - 2, 0, lid_t - eps]) cylinder(d = 4, h = board_z - 0.5 + eps);
        }
        // gasket groove on the inner face, under the middle of the shell wall
        translate([0, 0, lid_t - groove_depth]) linear_extrude(groove_depth + 1) difference() {
            rsquare([in_w + wall + groove_w, in_h + wall + groove_w], 3);
            rsquare([in_w + wall - groove_w, in_h + wall - groove_w], 3);
        }
        for (c = corners) translate([c.x * boss_xy.x, c.y * boss_xy.y, -1]) {
            cylinder(d = screw_clear, h = lid_t + 2);
            cylinder(d = 6.5, h = 1 + 1);   // shallow seat for screw head + washer
        }
        translate([0, 0, -1]) cylinder(d = gland_d, h = lid_t + 2);
        // soften the outer edge
        translate([0, 0, -eps]) difference() {
            linear_extrude(chamfer) rsquare([W + 2, H + 2], radius);
            hull() {
                linear_extrude(eps) rsquare([W - 2 * chamfer, H - 2 * chamfer], radius - chamfer);
                translate([0, 0, chamfer]) linear_extrude(eps) rsquare([W, H], radius);
            }
        }
    }
}

module bracket() {
    // base with two slim tilt arms; straps onto a railing post with hose clamps
    // (or screws / VHB tape on a flat surface)
    difference() {
        union() {
            linear_extrude(base.z) rsquare([base.x, base.y], 6);
            for (s = [-1, 1])
                hull() {
                    translate([s * (arm_gap / 2 + arm_t / 2), 0, base.z / 2]) cube([arm_t, base.y, base.z], center = true);
                    translate([s * (arm_gap / 2 + arm_t / 2), 0, pivot_h]) rotate([0, 90, 0]) cylinder(d = arm_w, h = arm_t, center = true);
                }
        }
        for (s = [-1, 1]) {
            translate([s * (arm_gap / 2 + arm_t / 2), 0, pivot_h]) rotate([0, 90, 0]) cylinder(d = pivot_clear, h = arm_t + 2, center = true);
            translate([s * (base.x / 2 - 8), 0, -1]) {
                cylinder(d = base_screw, h = base.z + 2);
                translate([0, 0, base.z - 1]) cylinder(d1 = base_screw, d2 = base_screw + 3, h = 1.5);
            }
            // tunnels for the hose clamps, running across the base
            translate([-base.x, s * (base.y / 4) - strap.x / 2, 2]) cube([2 * base.x, strap.x, strap.y]);
        }
        // groove in the back face that centres the base on the post
        translate([-post_w / 2 - 0.3, -base.y, -1]) cube([post_w + 0.6, 2 * base.y, 1 + 1.5]);
    }
}

if (part == "body") body();
else if (part == "lid") translate([0, 0, 0]) lid();
else if (part == "bracket") bracket();
else {
    tilt = 15;
    color("#e9e6df") bracket();
    translate([0, 0, pivot_h]) rotate([90 + tilt, 0, 0]) translate([0, 0, -pivot_z]) {
        color("#f4f2ed") body();
        color("#dcd6cc") translate([0, 0, -lid_t]) lid();
        color("lightblue", 0.5) translate([0, 0, D_in]) cylinder(d = disc_d, h = disc_t);
    }
}
