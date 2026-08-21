


module _cap() {
  difference() {
    translate([0, 0, 0.1])
      cylinder(h=4, r=8.5);
    hull() {
      translate([0, 0, 0]) cylinder(h=0.1, r=3.5);
      translate([0, 0, 2]) cylinder(h=0.1, r=2.25);
      translate([0, 0, 4]) cylinder(h=0.1, r=0.1);
    }
  }
}

module _screw_body(extra) {
  translate([0, 0, -2]) cylinder(h=12, r=2.5 + extra / 2);

  scale([-1, 1, 1]) linear_extrude(height=10, twist=1600, slices=120) {
      translate([0.75, 0, 0])
        circle(r=2.5 + extra);
    }
}

module _screw(extra = 0) {
  difference() {
    _screw_body(extra=extra);
    if (extra == 0)
      union() {
        translate([0, 0, 6]) _cap();
        rotate([0, 0, 90]) {
          translate([-0, -9, -2.5]) cube([8, 8, 2.5]);
          translate([-4, 2.0, -5]) cube([8, 8, 20]);
        }
      }
  }
}

module screw() {
  translate([40, 0, 2]) rotate([0, -90, 0]) _screw();
  translate([22, 0, 0]) difference() {
      union() {
        rotate([0, 0, 22.5]) cylinder(h=6, r=5, $fn=8);
        for (i = [0:8])
          rotate([0, 0, i * 45]) translate([0, 4.5, 3.5]) sphere(r=1);
      }
      union() {
        translate([0, 0, 6.1]) scale([1.1, 1.1, 1]) _screw();
        translate([-6, -1, 0]) cube([12, 2, 1]);
      }
    }
}
