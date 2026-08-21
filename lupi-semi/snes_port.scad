use <primitives.scad>;

gray = [0.5,0.5,0.5,1.0];
light_gray = [0.9,0.9,0.9,1.0];

module _port_c_block(width, height, tickness, small_chamfer_r) {
    core_width = width - (height / 2) - small_chamfer_r;
    height_h = height / 2;
    core_width_h = core_width / 2;
    union(){
        cube([core_width, tickness, height], center = true);
        rotate([90,0,0]){
            translate([core_width_h,0,0])
                cylinder(tickness,height_h,height_h,center = true);
            translate([-core_width_h,-height_h + small_chamfer_r,0])
                cylinder(tickness,small_chamfer_r,small_chamfer_r, center = true);
            translate([-core_width_h,height_h - small_chamfer_r,0])
                cylinder(tickness,small_chamfer_r,small_chamfer_r, center = true);
            translate([-core_width_h-small_chamfer_r / 2 + 0.5, 0, 0])
                cube([small_chamfer_r + 1,height - (small_chamfer_r * 2),tickness], center = true);
        }
    }
}

module _outer_shell_slot() {
    larger_size = 13;
    smaller_size = 2;
    translate([0,larger_size/2,0])
        _port_c_block(width = 43, height = 16, tickness = 4, small_chamfer_r = 3);
}

module _outer_shell() {
    larger_size = 13;
    smaller_size = 2;

    color(gray)
    difference(){
        union(){
            translate([0,larger_size/2,0])
                _port_c_block(width = 43, height = 16, tickness = smaller_size, small_chamfer_r = 3);
            translate([0,-1,0])
                _port_c_block(width = 38, height = 12, tickness = larger_size, small_chamfer_r = 2);
        }
        translate([0,larger_size/2,0])
            _port_c_block(width = 36, height = 10, tickness = larger_size, small_chamfer_r = 1);
    }
}

module _pins_rows(height, radius, add_cut = false){ 
    rotate([90,0,0]){
        for(i = [0:7]){
            translate([  (i - 3.2) * 3.72, 0, 0]) {
                if (i != 4) {
                    cylinder(h = height, r = radius, center = true);
                    if (add_cut) { 
                        translate([0,0,12]) cube([2, 20, 7], center = true);
                    }
                }
            }
        }
    }
}

module _inner_con(width = 32, height = 16){
    union(){
        color(gray){
            difference(){
                translate([0.9,-1,0]){
                    _port_c_block(width = width, height = 5, tickness = height+2, small_chamfer_r = 1);
                }
                union() {
                    translate([3,0,0]) cube([2, 30, 8], center = true);
                    _pins_rows(height = height*1.1, radius = 1.2, add_cut = true);
                }
            }
        }
        color(light_gray){
            translate([0,-2,0])
                _pins_rows(height = height, radius = 0.6);
            rotate([-80,0,0])
                translate([0,-6.5,-9.8])
                    _pins_rows(height = height * 0.6, radius = 0.6);
        }
    }
}

module _snes_port_filet(){
    translate([-16,6,8]) rotate([0,90,0])
        quarter_cylinder(2, 32);
    translate([16,6,-8]) rotate([0,-90,0])
        quarter_cylinder(2, 32);
    translate([19,6,-5]) rotate([0,0,90])
        quarter_cylinder(2, 10);

    translate([-16,6,0]) rotate([90,270,0])
        rotate_extrude(angle=180)
            translate([8, 0]) scale([-1,-1]) quarter_circle(2);

    translate([16,6,5]) rotate([90,0,0])
        rotate_extrude(angle=90)
            translate([3, 0]) scale([-1,-1]) quarter_circle(2);

    translate([16,6,-5]) rotate([90,0,0])
        rotate_extrude(angle=-90)
            translate([3, 0]) scale([-1,-1]) quarter_circle(2);
}

module snes_port_front(){
    difference(){
        translate([-2-2.5,8,2])
            cube([144, 4, 22], center = true);
        translate([-1,0,0])
            ports_slot();
    }

    dist = 47.3;
    placement = [-1*dist, 0, 1*dist];
    for (x_pos = placement){
        translate([x_pos-1,0,1]) _snes_port_filet();
    }   
}

module snes_port() {
    scale([-1,1,-1]) {
        _outer_shell();
        _inner_con();
    }
}

module ports(){
    dist = 47.3;
    placement = [-1*dist, 0, 1*dist];
    for (x_pos = placement){
        translate([x_pos-1,0,1])
            snes_port();
    }
}

module ports_slot(){
    dist = 47.3;
    placement = [-1*dist, 0, 1*dist];

    for (x_pos = placement){
        translate([x_pos,0,1]) scale([-1,1,-1]) {        
            _outer_shell_slot();
        }            
    }
}