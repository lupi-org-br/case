use <../pcb.scad>;
use <../snes_port.scad>;
use <../squircle.scad>;
use <../primitives.scad>;

module _front_ports_cutout(){
    translate([20.2,8,-5]) scale([1,1,1])
        capsule(r=0.5, h=12);
    translate([-27.2,8,-5]) 
        capsule(r=0.5, h=12);  
}

module _front_laterals(){
    translate([67.5,8,2]) {
        linear_extrude(height=22, center=true, twist=0)
            quarter_circle(r=4);
        translate([1,-10,-11])
            cube([3, 10, 22]);
    }

    translate([-76.5,8,2]) scale([-1,1,1]){
        linear_extrude(height=22, center=true, twist=0)
            quarter_circle(r=4);
        translate([1,-10,-11])
            cube([3, 10, 22]);
    }
}

module _front_panel() {
    translate([0,2,0]){
        difference(){
            snes_port_front();
            union(){
                translate([-4.5,12,1]) rotate([90,0,0]) {
                    squircle(W=144.2, H=19, height=8, center=true);
                }
                _front_ports_cutout();
            }
        }
    }

    _front_laterals();
}

module _front_base_shell(){
    difference(){
        translate([-0.2,-0.5,-17]) linear_extrude(height=4)
            scale([0.918,0.75,1]) hull() projection() _front_panel();
        rotate([0,90,0]) translate([17.01,9.01,-100]) scale([-1,-1,1])
            linear_extrude(height=200) right_triangle(base=3, height=5);
    }
}

module _front_bottom_shell(){
    difference(){
        translate([0,0,-14]) linear_extrude(height=5)
            hull() projection() _front_panel();
        rotate([0,90,0]) translate([14.01,12.01,-100]) scale([-1,-1,1])
            linear_extrude(height=200) right_triangle(base=3, height=7);
    }
}

module _front_top_shell(){
    difference(){
        translate([0,0,11]) linear_extrude(height=4)
            hull() projection() _front_panel();
        rotate([0,90,0]) translate([-15.01,12.01,100]) scale([1,-1,-1])
            linear_extrude(height=200) right_triangle(base=2, height=12);
    }
}

module _lupi_logo_text(){
    translate([-48, -3, 14.5]) 
        scale([-1,-1,1]) linear_extrude(height=0.5) 
            import("../imports/lupi_logo_text.svg");
}

module _lupi_logo_slab(){
    translate([-73, -13, 14.5]) cube([25,10,3]);
}

module _case_body(){
    union(){
        difference(){
            union(){
                hull(){
                    translate([-80.5,-14,12]) cube([3,12,3]);
                    translate([68.5,-14,12]) cube([3,12,3]);
                };
                hull(){
                    translate([-80.5,-14,12]) cube([3,12,3]);
                    translate([-80.5,-14,-13]) cube([3,12,3]);
                };
                hull(){
                    translate([68.5,-14,12]) cube([3,12,3]);
                    translate([68.5,-14,-13]) cube([3,12,3]);
                };
                hull(){
                    translate([68.5-6,-14,-17]) cube([3,12,3]);
                    translate([-80.5+6,-14,-17]) cube([3,12,3]);
                }
                hull(){
                    translate([-80.5,-14,-14]) cube([3,12,3]);
                    translate([-80.5+6,-14,-14]) cube([3,12,3]);
                }
                hull(){
                    translate([68.5,-14,-14]) cube([3,12,3]);
                    translate([68.5-6,-14,-14]) cube([3,12,3]);
                }
            };
            _lupi_logo_slab();

            translate([-5,-15,-20])
                squircle(W=47, H=20, height=12);

            translate([-44.5,-8.5 + 2.2,15]) rotate([0,90,0]) scale([1,2,1]) capsule(r=0.5, h=108);
            translate([-44.5,-8.5 - 1.5,15]) rotate([0,90,0]) scale([1,2,1]) capsule(r=0.5, h=108);            
        };
        _lupi_logo_text();
    }
}

module _case_ply_mark_dots(count) {
    spacing = 4.5;
    total_width = (count - 1) * spacing;
    start_x = -total_width / 2;

    for (i = [0 : count - 1]) {
        x_pos = start_x + i * spacing;
        translate([x_pos, 6, 13.5]) rotate([-10,0,0]) {
            hull(){
                cylinder(r=1.4, h=2.4, center=true);
                cylinder(r=2, h=1.0, center=true);
            }   
        }
    }
}

module _case_pyrs_markers() {
    dist = 47.3;
    padding = -2.25;
    translate([-1*dist+padding,0,0]) _case_ply_mark_dots(3);
    translate([padding,0,0]) _case_ply_mark_dots(2);
    translate([1*dist+padding,0,0]) _case_ply_mark_dots(1);
}

module _inner_chanfers(){
    union(){
        size_bot = 138;
        rotate([0,90,0]) translate([8.6, -3,-size_bot/2 - 2.5])
            linear_extrude(height=size_bot-4) right_triangle(base=6.17, height=8);

        size_mid = 150;
        rotate([0,90,0]) translate([8.2, -3, -size_mid/2 - 2.5])
            linear_extrude(height=size_mid-4) right_triangle(base=3.11, height=10);
        
        size_top = 150;
        rotate([0,90,0]) translate([-7.5 - 2.7, -3 ,-size_top/2 - 2.5]) scale([-1,1,1])
            linear_extrude(height=size_top-4) right_triangle(base=2, height=10);
    }
}

module case_front(){
    difference(){
        union(){
            _front_panel();
            _front_bottom_shell();
            _front_top_shell();
            _front_base_shell();
        }
        _inner_chanfers();
    }

    _case_pyrs_markers();
    _case_body();
}
