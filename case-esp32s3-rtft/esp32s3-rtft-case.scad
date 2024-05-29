/*
Enclosure for Adafruit ESP32-S3 Reverse TFT Feather.
(C) 2023, P. Bauermeister.
*/

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
    dy = INNER_WIDTH/2 -INNER_WIDTH/5;

    // for plug
    pz = PILLAR_HEIGHT - PLUG_THICKNESS + PLAY*2;
    translate([0, 0, OUTER_HEIGHT - INNER_HEIGHT])
    translate([-INNER_LENGTH/2, INNER_WIDTH/2 - PLUG_WIDTH/2, pz])
    cube([INNER_LENGTH, PLUG_WIDTH, PLUG_THICKNESS]);

    // for board
    translate([0, 0, OUTER_HEIGHT - INNER_HEIGHT])
    cube([INNER_LENGTH, INNER_WIDTH, INNER_HEIGHT]);

    // for bottom
    translate([BORDER_X, BORDER_Y + dy - BORDER_Y/2, -ATOM])
    cube([INNER_LENGTH - 2*BORDER_X, INNER_WIDTH - 2*BORDER_Y -dy, OUTER_HEIGHT + ATOM*2]);

    if(0)
    translate([INNER_LENGTH/2, INNER_WIDTH/2, -ATOM])
    cylinder(d=INNER_WIDTH/2,h=OUTER_HEIGHT+ ATOM*2, $fn=60);

    
    // corner cut
    translate([0, dy , 0])
    rotate([-45, 0, 0])
    translate([-INNER_LENGTH, -INNER_WIDTH, -INNER_HEIGHT])
    cube([INNER_LENGTH*3, INNER_WIDTH, INNER_HEIGHT]);
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


module cap() {
    difference() {
        translate([-THICKNESS*2, -THICKNESS*2, 0])
        cube([INNER_LENGTH + THICKNESS*4, INNER_WIDTH + THICKNESS*4, THICKNESS*4]);

        translate([-THICKNESS, -THICKNESS, THICKNESS*2])
        cube([INNER_LENGTH + THICKNESS*2, INNER_WIDTH + THICKNESS*2, THICKNESS*4+1]);


        
        translate([0, -INNER_WIDTH/20*0, THICKNESS*.5]) {
            translate([0, INNER_WIDTH/2+.5 +.2, -THICKNESS*2.5 + .2]) rotate([45, 0, 0]) case();
            translate([0, INNER_WIDTH/2+.5, -THICKNESS*2.5]) rotate([45, 0, 0]) case();
            translate([0, INNER_WIDTH/2, -THICKNESS*2.5]) rotate([45, 0, 0]) case();
        }
    }
}


case();
translate([0, -INNER_WIDTH*1.5, 0]) cap();
