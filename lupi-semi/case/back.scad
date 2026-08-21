
use <../snes_port.scad>;
use <../case.scad>;
use <../primitives.scad>;
use <../squircle.scad>;

module _sd_card_pcb_cutout() {
  translate([12.5, 3.5, 12]) rotate([0, 90, 0]) scale([1, 1, 1])
        capsule(r=2, h=28);

  translate([12.5 + 59, 3.5, 12]) rotate([0, 90, 0]) scale([1, 1, 1])
        capsule(r=2, h=26.7);

  translate([19.5 + 1, -1, 8]) rotate([0, 90, 0]) scale([1.6, 1, 1])
        capsule(r=3, h=14);

  translate([77.5 + 1, -1, 8]) rotate([0, 90, 0]) scale([1.6, 1, 1])
        capsule(r=3, h=14);
}

module _air_gaps() {
  shift = [-0.5, 0, -6];
  padding = [1, 0, 8];

  for (i = [1:7]) {
    translate([75.7 - (5.3 * i), -4, 10])
      tapered_port([2, 1, 2], padding=padding, shift=shift, bulge_x=0.4, bulge_y=0.2);
  }

  for (i = [1:2]) {
    translate([17 - (5.3 * i), -4, 10])
      tapered_port([2, 1, 2], padding=padding, shift=shift, bulge_x=0.4, bulge_y=0.2);
  }
}

module _device_ports() {
  translate([101, -4, 9])
    tapered_port([30, 1, 11], padding=[4, 0, 4], shift=[-2, 3, -3]);
  translate([39, -4, 20]) tapered_port([35, 1, 6]);
  translate([76, -4, 8]) tapered_port([17, 1, 5]);
  translate([18, -4, 8]) tapered_port([17, 1, 5]);
}

module _pcb_back_grip() {
  translate([57.6, 3, 8 - 0.75]) cube([2, 2, 2.5]);
  translate([57.6 - 5.25, 3, 8 - 0.75]) cube([2, 2, 2.5]);
  translate([48.5, -3, 4.5 + 3.25]) rotate([0, 90, 0])
      tapered_port([1.5, 1, 15], padding=[0, 0, 0], shift=[0.5, 6, 0], bulge_x=0.4, bulge_y=0.1);
}

module _top_case_pin() {
  hull() {
    translate([-5 + 28, 3, 20]) cube([3, 2, 5]);
    translate([-5 + 23, 16, 23]) cube([3, 2, 2]);
  }

  hull() {
    translate([-5 + 18, 3, 20]) cube([3, 2, 5]);
    translate([-5 + 23, 16, 23]) cube([3, 2, 2]);
  }

  translate([-3.5 + 23, 14.2, 25]) scale([1, 1, 0.5])
      sphere(r=2.5);
}

module _foot() {
  rotate([90, 0, 0]) translate([22, -4, -3]) hull()
        intersection() {
          translate([-16, -5, 0]) cube([29, 8, 3]);
          union() {
            translate([-16, 2, 0]) cube([12, 1.5, 3]);
            translate([-10 - 4, 2, 0]) cylinder(h=3, r=2);
            translate([10 - 3, 3, 0]) cylinder(h=3, r=3);
          }
        }
}

module _top_part() {
  difference() {
    translate([0, 2.5, 30]) linear_extrude(height=2)
        import("../imports/case_top_3.svg");
    union() {
      translate([132, 34, 31.5]) scale([-1, -1, 1]) linear_extrude(height=2)
            import("../imports/lupi_logo_graph.svg");

      intersection() {
        translate([3, 0, 30]) scale([0.96, 1, 1]) linear_extrude(height=2)
              import("../imports/case_top_3.svg");
        union() {
          for (i = [0:21]) {
            translate([-101.8 + i * 10, 45, 32.2]) rotate([23.5, 90, 0]) scale([1, 2, 1])
                  capsule(r=0.4, h=128);
          }
        }
      }
    }
  }
}

module _back_part() {
  difference() {
    translate([0, 0, 2]) {
      union() {
        cube([152, 3, 30]);
        translate([6, 0, -3]) cube([140, 3, 3]);
        translate([15, 3, 5 - 0.75]) cube([120, 1.2, 1.0]);
        translate([0, -3, 0]) scale([1, 2.0, 1]) _pcb_back_grip();
        translate([0, -3, 10]) scale([1, 2, -1]) _pcb_back_grip();
        translate([29.2, -3, 10]) scale([1, 2, -1]) _pcb_back_grip();
        translate([-29.2, -3, 10]) scale([1, 2, -1]) _pcb_back_grip();

        // #translate([15, 20, 26]) cube([120, 30, 2]);
        _top_case_pin();
        translate([76, -3, 0]) scale([2, 2, 1]) _top_case_pin();
      }
    }

    intersection() {
      translate([3, -2, 2]) cube([146, 6, 28]);
      union() {
        _device_ports();
        _sd_card_pcb_cutout();
        _air_gaps();

        translate([-5, 0.12, -9]) rotate([90, 0, 0]) linear_extrude(height=3)
              import("../imports/case_back.svg");
      }
    }
  }

  _foot();
  translate([152, 0, 0]) scale([-1, 1, 1]) _foot();
}

module back_case() {
  _top_part();
  difference() {
    _back_part();
    union() {
      translate([12, 6, 1.25]) rotate([90, 0, 0])
          cylinder(h=10, r=4);
      translate([140, 6, 1.25]) rotate([90, 0, 0])
          cylinder(h=10, r=4);
    }
  }
}
