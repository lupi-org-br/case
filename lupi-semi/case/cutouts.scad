module case_lateral_cutout() {
  translate([-82.5, -69, -10]) hull() {
      cube([1, 62, 3]);
      translate([2, 4, 0]) cube([1, 54, 3]);
    }

  translate([73.5, -69, -10]) hull() scale([-1, 1, 1]) {
        cube([1, 62, 3]);
        translate([2, 4, 0]) cube([1, 54, 3]);
      }

  translate([-81.5, -61.5 - 1, -7]) cube([11, 50, 13]);

  // TODO: remove
  //translate([-61.4, -95, -25]) cube([140, 120, 50]);
}
