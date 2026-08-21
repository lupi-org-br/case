use <btn.scad>;

module case_top_cutouts() {
  union() {
    translate([-5, -60, 13.5]) rotate([270 - 45, 90, 0]) scale([2, 1, 1])
          btn_footprint();
    translate([-80, -80, 14]) linear_extrude(height=3)
        import("../imports/case_top.svg");
    translate([-80, -80, 12.5]) linear_extrude(height=6)
        import("../imports/case_top_2.svg");
  }
}

module case_top_fixtures() {
  for (i = [0:6]) {
    offset = i * 2.7;
    translate([offset - 35.45, -64, 12.1])
      cube([1, 9.1, 2.3]);
  }

  translate([-5, -60, 13.5]) rotate([270 - 45, 90, 0]) btn();
}
