use <../primitives.scad>;

module btn_footprint(){
    hull() btn();
}

module btn() {
    difference() {
        union() {
            translate([-1.5, 4.5, 20]) scale([0.1, 0.1, -0.1]) rotate([90, 0, 0])
                linear_extrude(height=90)
                    import("../imports/btn_coil.svg");

            translate([-1.5, 5, 0]) cube([3, 3, 22]);
            translate([-1.5, -8, 0]) cube([3, 3, 22]);

            hull() {
                translate([-1.5, 5, 0]) cube([3, 3, 2]);
                translate([-1.5, -8, 0]) cube([3, 3, 2]);
            }

            translate([0.25, 0, 19.5]) rotate([90, 0, 90]) 
                cylinder(h=3.5, r=4.5, center=true);

            translate([1.5, 0, 18.5]) scale([1, 1, 2])
                sphere(r=2.5);

            difference() {
                union() {
                    hull() {
                        translate([-1.5, 5, 19]) cube([3, 3, 7]);
                        translate([-1.5, -8, 19]) cube([3, 3, 7]);
                    }
                }
                union() {
                    translate([0.25, 0, 19.5]) rotate([90, 0, 90]) 
                        cylinder(h=18, r=5.5, center=true);
                }
            }
        }
        translate([-1.5, 0, 19.5]) scale([0.2, 1, 1])
            sphere(r=3);
    }
}