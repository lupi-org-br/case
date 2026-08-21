module quarter_cylinder(r, h) {
    intersection() {
        cylinder(r=r, h=h);
        translate([0, 0, -0.01])
            cube([r, r, h + 0.02]);
    }
}

module quarter_circle(r) {
    intersection() {
        circle(r=r);
        translate([0, 0])
            square([r, r]);
    }
}

module capsule(h, r) {
    cylinder_height = h - 2 * r;
    
    union() {
        translate([0, 0, r])
            sphere(r=r);
            
        translate([0, 0, r])
            cylinder(r=r, h=cylinder_height);
        
        translate([0, 0, h - r])
            sphere(r=r);
    }
}

module right_triangle(base, height) {
    polygon(points=[[0,0], [base,0], [0,height]]);
}