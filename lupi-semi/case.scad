use <case/front.scad>;
use <case/belly.scad>;
use <case/btn.scad>;
use <case/top.scad>;

module case() {
  case_front();
  case_belly();

  difference() {
    case_walls();
    case_top_cutouts();
  }

  case_top_fixtures();
}
