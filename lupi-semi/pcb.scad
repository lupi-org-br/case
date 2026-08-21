use <comps.scad>;
use <snes_port.scad>;

module pcb_board() {
  translate([-3.4, -83.5, -8]) {
    translate([0, 40, 0]) color([0 / 255, 160 / 255, 120 / 255])
        cube([130, 74, 1.5], center=true);

    color([90 / 255, 90 / 255, 90 / 255, 0.5])
      scale([0.75, 0.75, 1]) translate([-92, -10.1, 0.75]) linear_extrude(height=0.5)
            import("imports/lupi_pcb_board_outline.svg");
  }

  translate([-18.5, -46.5, -2]) {
    color([10 / 255, 10 / 255, 10 / 255, 0.5])
      cube([2, 2, 10], center=true);
    translate([-10, -14, 0])
      color([190 / 255, 190 / 255, 190 / 255, 0.5])
        cylinder(h=10, r=2, center=true);
  }

  translate([-68, -41, -6]) {
    color([20 / 255, 10 / 255, 120 / 255])
      cube([10, 10, 12]);

    color([20 / 255, 20 / 255, 20 / 255]) translate([5, 5, 6]) {
        rotate([90, 0, 0]) cylinder(r=0.5, h=12, center=true);
        rotate([0, 90, 0]) cylinder(r=0.5, h=12, center=true);
        cylinder(r=0.5, h=14, center=true);
      }
  }
}
