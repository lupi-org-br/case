use <../primitives.scad>;
use <../squircle.scad>;
use <../parts/screw.scad>;

module _paws() {
  difference() {
    union() {
      scale([1, 1, 1]) translate([-67, -26, -20]) linear_extrude(height=3)
            import("../imports/paw.svg");

      scale([1, 1, 1]) translate([25, -26, -20]) linear_extrude(height=3)
            import("../imports/paw.svg");
    }

    rotate([0, -90, 0]) translate([-20.5, -28, -100]) linear_extrude(height=200)
          right_triangle(base=4.5, height=10);
  }
}

module _grid(width, height = 20, depth = 1) {
  spacing = 4;
  thickness = 1;
  diagonal = sqrt(width * width + height * height);

  intersection() {
    union() {
      for (i = [floor(-diagonal / spacing):ceil(diagonal / spacing)]) {
        offset = i * spacing;
        rotate([0, 0, 45])
          translate([offset, -diagonal / 2, 0])
            cube([thickness, diagonal, depth]);
      }
      for (i = [floor(-diagonal / spacing):ceil(diagonal / spacing)]) {
        offset = i * spacing;
        rotate([0, 0, -45])
          translate([offset, -diagonal / 2, 0])
            cube([thickness, diagonal, depth]);
      }
    }
    translate([-width / 2, -height / 2, 0])
      cube([width, height, depth]);
  }
}

module _bottom_shell() {
  difference() {
    union() {
      extra = 13;
      hull() {
        translate([62.5, -68 - extra, -17]) cube([3, 54 + extra, 3]);
        translate([-74.5, -68 - extra, -17]) cube([3, 54 + extra, 3]);
      }
      hull() {
        translate([-80.5, -68 - extra, -14]) cube([3, 54 + extra, 3]);
        translate([-74.5, -68 - extra, -14]) cube([3, 54 + extra, 3]);
      }
      hull() {
        translate([68.5, -68 - extra, -14]) cube([3, 54 + extra, 3]);
        translate([62.5, -68 - extra, -14]) cube([3, 54 + extra, 3]);
      }
    }
    ;

    translate([-5, -15, -20])
      squircle(W=47, H=20, height=12);

    translate([-5, -47, -20])
      squircle(W=120, H=25, height=12);

    translate([-5, -58, -20])
      squircle(W=72, H=30, height=12);
  }

  translate([-5.5, -13.32, -17])
    _grid(width=54, height=24, depth=3);

  translate([-5.5, -52, -17])
    _grid(width=128, height=46, depth=3);
}

module _pcb_slider(adding_grip = true) {
  difference() {
    union() {
      translate([62, -26, -11]) cube([2, 20, 5]);
      translate([60.5, -26, -14]) cube([2, 20, 5]);
      if (adding_grip) translate([61, -26, -6.8]) cube([1, 20, 0.8]);

      translate([-70.5, -26, -16]) cube([2, 20, 10]);
      translate([-68.5, -26, -14]) cube([2, 20, 5]);
      if (adding_grip) translate([-68.5, -26, -6.8]) cube([1, 20, 0.8]);
    }

    rotate([0, 90, 0]) translate([5, -28, -100]) linear_extrude(height=200)
          right_triangle(base=10, height=16);
  }
}

module _foot() {
  rotate([90, 0, 0]) translate([22, -4, -16])
      hull() intersection() {
          translate([-16, -5, -4]) cube([29, 8, 17]);
          union() {
            translate([-16, 2, -4]) cube([12, 1.5, 17]);
            translate([-14, 2, -4]) cylinder(h=17, r=2);
            translate([7, 3, -4]) cylinder(h=17, r=3);
          }
        }
}

module _screws_socket() {
  difference() {
    union() {
      translate([-80.5, -84, -16]) _foot();
      translate([-82.5, -84, -15.5]) scale([0.62, 1, -1.5]) _foot();
      translate([71.5, -84, -16]) scale([-1, 1, 1]) _foot();
      translate([73.5, -84, -15.5]) scale([-0.62, 1, -1.5]) _foot();
    }
    translate([-80, -72.5, -26]) rotate([-42, 0, 0]) cube([150, 20, 20]);
    translate([-80, -62, -16]) rotate([42, 0, 0]) cube([150, 20, 20]);
  }
}

module _case_belly() {
  _paws();
  _bottom_shell();

  translate([0, 0, 0]) _pcb_slider();
  translate([0, -40, 0]) _pcb_slider(adding_grip=false);
  _screws_socket();
}

module case_walls() {
  union() {
    hull() {
      translate([-80.5, -81, 12]) cube([3, 67, 3]);
      translate([68.5, -81, 12]) cube([3, 67, 3]);
    }
    hull() {
      translate([-80.5, -81, 12]) cube([3, 67, 3]);
      translate([-80.5, -81, -13]) cube([3, 67, 3]);
    }
    hull() {
      translate([68.5, -81, 12]) cube([3, 67, 3]);
      translate([68.5, -81, -13]) cube([3, 67, 3]);
    }
  }
}

module case_belly() {

  difference() {
    _case_belly();
    translate([-80.5, -84, -16]) union() {
        hull() {
          translate([12, 13, 1.25]) rotate([90, 0, 0])
              cylinder(h=11, r=3);
          translate([12, 20, 1.25]) rotate([90, 0, 0])
              cylinder(h=1, r=1);
        }

        hull() {
          translate([140, 13, 1.25]) rotate([90, 0, 0])
              cylinder(h=11, r=3);
          translate([140, 20, 1.25]) rotate([90, 0, 0])
              cylinder(h=1, r=1);
        }

        translate([140, 12, 1.25]) rotate([90, 90, 0])
            _screw(extra=0.75);

        translate([12, 12, 1.25]) rotate([90, 90, 0])
            _screw(extra=0.75);
      }
  }
}
