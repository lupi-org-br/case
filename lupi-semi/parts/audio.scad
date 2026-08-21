use <../squircle.scad>;

module _audio_port() {
  intersection() {
    hull() {
      translate([-80.5, -66, -7]) linear_extrude(height=15)
          import("../imports/case_side_audio.svg");
      translate([-80.5, -66, -6]) cube([3, 50, 1]);
    }
    union() {
      translate([-80.5, -66, -7]) cube([10, 50, 2]);
      translate([-80.5, -66, 5]) cube([10, 50, 1]);
    }
  }

  translate([-80.5, -66, -5]) linear_extrude(height=10)
      import("../imports/case_side_audio.svg");
}

module audio_port() {
  difference() {
    translate([0, 3.5, 0]) _audio_port();
    union() {
      hull() {
        translate([-78 + 2, -37 + 1, 0]) rotate([0, 90, 0]) rotate([0, 0, 0])
              squircle(W=8.5, H=8.5 + 2, height=0.1, bulge_x=1.25, bulge_y=0.75);
        translate([-78 + 8, -37 + 1, 0]) rotate([0, 90, 0]) rotate([0, 0, 45])
              squircle(W=8.5, H=8.5, height=1, bulge_x=1.25, bulge_y=0.75);
      }

      translate([-80, -41.5, -6.0]) linear_extrude(height=4)
          import("../imports/case_audio_icon.svg");
    }
  }
}
