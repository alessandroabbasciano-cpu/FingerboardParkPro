import math
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import FreeCAD as fc  # type: ignore
else:
    try:
        import FreeCAD as fc
    except Exception:
        fc = None

if TYPE_CHECKING:
    import Part  # type: ignore
else:
    try:
        import Part  # type: ignore
    except Exception:
        if fc is not None and hasattr(fc, "Part"):
            Part = fc.Part
        else:
            Part = None

def make_diamond_cutter(length, groove_width, axis='X'):
    side = groove_width / math.sqrt(2)
    box = Part.makeBox(length if axis=='X' else side, 
                       length if axis=='Y' else side, 
                       length if axis=='Z' else side)
    if axis == 'X':
        box.translate(fc.Vector(0, -side/2.0, -side/2.0))
        box.rotate(fc.Vector(0,0,0), fc.Vector(1,0,0), 45)
    elif axis == 'Y':
        box.translate(fc.Vector(-side/2.0, 0, -side/2.0))
        box.rotate(fc.Vector(0,0,0), fc.Vector(0,1,0), 45)
    else: # Z
        box.translate(fc.Vector(-side/2.0, -side/2.0, 0))
        box.rotate(fc.Vector(0,0,0), fc.Vector(0,0,1), 45)
    return box

def apply_texture(shape, w, h, l, bl, bh, gd, sides=4): 
    cutters = []
    rows = int(h / bh) + 1
    # --- LATI LUNGHI (XZ) - Fiancate ---
    for y_pos in [0, l]:
        for r in range(1, rows):
            z = r * bh
            if z < h:
                c = make_diamond_cutter(w + 20, gd, 'X')
                c.translate(fc.Vector(-10, y_pos, z))
                cutters.append(c)
        for r in range(rows):
            z_s, shift = r * bh, (0 if r % 2 == 0 else bl/2.0)
            for i in range(int(w/bl) + 2):
                cv = make_diamond_cutter(bh, gd, 'Z')
                cv.translate(fc.Vector((i * bl) + shift, y_pos, z_s))
                cutters.append(cv)
    # --- RETRO (YZ) ---
    for r in range(1, rows):
        z = r * bh
        if z < h:
            c = make_diamond_cutter(l + 20, gd, 'Y')
            c.translate(fc.Vector(w, -10, z))
            cutters.append(c)
    for r in range(rows):
        z_s, shift = r * bh, (0 if r % 2 == 0 else bl/2.0)
        for i in range(int(l/bl) + 2):
            cv = make_diamond_cutter(bh, gd, 'Z')
            cv.translate(fc.Vector(w, (i * bl) + shift, z_s))
            cutters.append(cv)
    # --- FRONTE (YZ) - Solo se richiesto ---
    if sides == 4:
        for r in range(1, rows):
            z = r * bh
            if z < h:
                c = make_diamond_cutter(l + 20, gd, 'Y')
                c.translate(fc.Vector(0, -10, z))
                cutters.append(c)
        for r in range(rows):
            z_s, shift = r * bh, (0 if r % 2 == 0 else bl/2.0)
            for i in range(int(l/bl) + 2):
                cv = make_diamond_cutter(bh, gd, 'Z')
                cv.translate(fc.Vector(0, (i * bl) + shift, z_s))
                cutters.append(cv)
    if cutters:
        try:
            return shape.cut(Part.makeCompound(cutters))
        except:
            return shape
    return shape

def make_rect_cutter(length, width, depth, axis='X'):
    """Crea un parallelepipedo per scanalature a fondo piatto."""
    box = Part.makeBox(length if axis=='X' else width, 
                       length if axis=='Y' else width, 
                       depth) # Profondità fissa in Z
    
    # Centriamo il cutter rispetto alla larghezza e lo posizioniamo 
    # in modo che 'depth' sia la parte che affonda
    if axis == 'X':
        box.translate(fc.Vector(0, -width/2.0, -depth))
    else: # axis == 'Y'
        box.translate(fc.Vector(-width/2.0, 0, -depth))
    return box

def apply_horizontal_tiles(shape, length, width, tile_size, groove_width, rotated=False, depth=0.5):
    bbox = shape.BoundBox
    z_top = bbox.ZMax
    center_x = length / 2.0
    center_y = width / 2.0
    cutters = []
    
    # Usiamo il taglio rettangolare (Flat Bottom)
    if not rotated:
        # Griglia Standard
        num_y = int(width / tile_size) + 1
        for i in range(num_y + 1):
            y_pos = i * tile_size
            c = make_rect_cutter(length + 10, groove_width, depth, 'X')
            c.translate(fc.Vector(-5, y_pos, z_top))
            cutters.append(c)
            
        num_x = int(length / tile_size) + 1
        for i in range(num_x + 1):
            x_pos = i * tile_size
            c = make_rect_cutter(width + 10, groove_width, depth, 'Y')
            c.translate(fc.Vector(x_pos, -5, z_top))
            cutters.append(c)
    else:
        # Griglia Ruotata 45°
        diag = math.sqrt(length**2 + width**2) + (tile_size * 2)
        num = int(diag / tile_size) + 2
        for i in range(num):
            pos = (i * tile_size) - (diag / 2.0)
            c1 = make_rect_cutter(diag, groove_width, depth, 'X')
            c1.translate(fc.Vector(-diag/2.0, pos, 0))
            cutters.append(c1)
            c2 = make_rect_cutter(diag, groove_width, depth, 'Y')
            c2.translate(fc.Vector(pos, -diag/2.0, 0))
            cutters.append(c2)
            
        if cutters:
            grid = Part.Compound(cutters)
            grid.rotate(fc.Vector(0,0,0), fc.Vector(0,0,1), 45)
            grid.translate(fc.Vector(center_x, center_y, z_top))
            return shape.cut(grid)

    if cutters:
        shape = shape.cut(Part.Compound(cutters))
    return shape