module _ellipse2d(rx, ry) {
  scale([rx, ry]) circle(r=1);
}

module _squircle_2d(W = 100, H = 60, bulge_x = 12, bulge_y = 10) {
  bx = min(max(bulge_x, 0.001), W / 2);
  by = min(max(bulge_y, 0.001), H / 2);

  hull() {
    translate([0, H / 2 - by]) _ellipse2d(W / 2 - bx, by);
    translate([0, -H / 2 + by]) _ellipse2d(W / 2 - bx, by);
    translate([-W / 2 + bx, 0]) _ellipse2d(bx, H / 2 - by);
    translate([W / 2 - bx, 0]) _ellipse2d(bx, H / 2 - by);
  }
}

module squircle(W = 100, H = 60, height = 5, center = false, bulge_x = 1.4, bulge_y = 0.6) {
  linear_extrude(height=height, center=center)
    _squircle_2d(W=W, H=H, bulge_x=bulge_x, bulge_y=bulge_y);
}

module squircle_inside_cube(size = [1, 1, 1], center = false, bulge_x = 1.4, bulge_y = 0.6) {
  sz = is_list(size) ? size : [size, size, size];
  w = sz[0];
  h = sz[1];
  d = sz[2];

  translate(center ? [0, 0, 0] : [w / 2, h / 2, d / 2])
    rotate([90, 0, 0])
      squircle(W=w, H=d, height=h, center=true, bulge_x=bulge_x, bulge_y=bulge_y);
}

module tapered_port(size, padding = [2, 0, 2], shift = [-1, 3, -2], bulge_x = 1.4, bulge_y = 0.6) {
  hull() {
    translate(shift) squircle_inside_cube(size + padding, bulge_x=bulge_x, bulge_y=bulge_y);
    translate([0, 7, 0]) squircle_inside_cube(size, bulge_x=bulge_x, bulge_y=bulge_y);
  }
}
