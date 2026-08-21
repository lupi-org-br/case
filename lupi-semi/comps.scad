module resistor() {
    color("#2831d3ff")
    cube([6, 2, 2], center = true);
}

module capacitor() {
    color("#150758ff")
    translate([0,0,-7.5])
        cylinder(h = 15, r = 4, center = true, $fn=8);
}