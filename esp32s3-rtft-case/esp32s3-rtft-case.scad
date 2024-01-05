

INNER_LENGTH   = 52.0  - .3;
INNER_WIDTH    = 23.5  - .1;
INNER_HEIGHT   =  9.0  + .75;

THICKNESS      =  1.5 +.25;
OUTER_HEIGHT   = (INNER_WIDTH  + THICKNESS*2) * 4 / 5;

PCB_THICKNESS  =  1.5;
CHAMFER        =  1.0;

PLUG_WIDTH     = 13.0 -2;
PLUG_THICKNESS =  4.0;
ATOM           =  0.01;

BORDER_X       = 10.0;
BORDER_Y       =  2.0;



PILLAR_SIDE    =  2.0;
PILLAR_HEIGHT  =  5.5  +.25;

FN             = 8;
PLAY           = .17;

module box() {
    d = THICKNESS-CHAMFER;
    hull()
    for (x=[-d, INNER_LENGTH + d]) {
        for (y=[-d, INNER_WIDTH + d]) {
            for (z=[CHAMFER, OUTER_HEIGHT - CHAMFER]) {
                translate([x, y, z])
                sphere(r=CHAMFER, $fn=FN);
            }
        }
    }
}

module chamber() {
    // for plug
    pz = PILLAR_HEIGHT - PLUG_THICKNESS + PLAY*2;
    translate([0, 0, OUTER_HEIGHT - INNER_HEIGHT])
    translate([-INNER_LENGTH/2, INNER_WIDTH/2 - PLUG_WIDTH/2, pz])
    cube([INNER_LENGTH, PLUG_WIDTH, PLUG_THICKNESS]);

    // for board
    translate([0, 0, OUTER_HEIGHT - INNER_HEIGHT])
    cube([INNER_LENGTH, INNER_WIDTH, INNER_HEIGHT]);

    // for bottom
    translate([BORDER_X, BORDER_Y, -ATOM])
    cube([INNER_LENGTH - 2*BORDER_X, INNER_WIDTH - 2*BORDER_Y, OUTER_HEIGHT + +ATOM*2]);
}

module case() {
    difference() {
        box();
        chamber();
    }
    
    // pillars
    for (x=[0, INNER_LENGTH-PILLAR_SIDE]) {
        for (y=[0, INNER_WIDTH-PILLAR_SIDE]) {
            translate([x, y, OUTER_HEIGHT - INNER_HEIGHT])
            cube([PILLAR_SIDE, PILLAR_SIDE, PILLAR_HEIGHT]);
        }
    }
    
    // blockers
    BLOCKER_SIZE = 2;
    BLOCKER_THICKNESS = .6;
    BLOCKER_POS = 10;
    for (x=[BLOCKER_POS, INNER_LENGTH-BLOCKER_POS]) {
        for (y=[0, INNER_WIDTH]) {

            translate([x, y, OUTER_HEIGHT - INNER_HEIGHT])

            hull() {
                translate([0, 0, INNER_HEIGHT-THICKNESS/2])
                resize([BLOCKER_SIZE, , ATOM, ATOM])
                cylinder($fn=12);

                translate([0, 0, PILLAR_HEIGHT+PCB_THICKNESS/2])
                resize([BLOCKER_SIZE, BLOCKER_THICKNESS, ATOM])
                cylinder($fn=12);

                translate([0, 0, 0])
                resize([BLOCKER_SIZE, ATOM, ATOM])
                cylinder($fn=12);
            }
        }
    }
    
    // clip
    CYLINDER_RADIUS = .4;
    cl = INNER_WIDTH/4;
    cz = OUTER_HEIGHT - INNER_HEIGHT + PILLAR_HEIGHT + PCB_THICKNESS;
    for (x=[0, INNER_LENGTH]) {
        translate([x, (INNER_WIDTH-cl)/2, cz])
        rotate([-90, 0, 0])
        cylinder(r=CYLINDER_RADIUS, h = cl, $fn=12);
    }
}

case();

if (0)
  %translate([0, 0, THICKNESS])
  cube([INNER_LENGTH, INNER_WIDTH, INNER_HEIGHT]);

if (0) {
    l = INNER_LENGTH + THICKNESS*2;
    w = INNER_WIDTH  + THICKNESS*2;
    h = w;
    translate([-THICKNESS, -THICKNESS, 0])
    %cube([l, w, h]);
}