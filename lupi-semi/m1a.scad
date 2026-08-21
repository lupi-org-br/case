use <pcb.scad>;
use <snes_port.scad>;
use <case.scad>;
use <primitives.scad>;
use <squircle.scad>;
use <case/back.scad>;
use <parts/screw.scad>;
use <parts/audio.scad>;
use <case/cutouts.scad>;

$fn = 18;

//ports();
// pcb_board();
//#translate([-80.5, -84, -16])
//  color("#a12c7cff") back_case();

module proto() {
  color("#a12c7cff")
    scale([-1.2, 1.4, 1]) translate([-45, -25, -17.7]) linear_extrude(height=2)
          import("imports/proto-text.svg");
}

color("#cfbfcaff")
  render() union() {
      difference() {
        case();
        case_lateral_cutout();
      }

      audio_port();
      proto();
    }
