# Try to import FreeCAD/Part for runtime; if unavailable (editor, linter), provide minimal stubs
try:
    import importlib
    fc = importlib.import_module("FreeCAD")
    Part = importlib.import_module("Part")
except Exception:
    from types import SimpleNamespace
    # Minimal Vector stub used by editor/static checks
    class _Vector:
        def __init__(self, x=0, y=0, z=0):
            self.x = x
            self.y = y
            self.z = z
        def __repr__(self):
            return f"Vector({self.x}, {self.y}, {self.z})"
    fc = SimpleNamespace(Vector=_Vector)

    # Minimal Part stub with placeholder callables to satisfy static analysis
    class _PartStub:
        @staticmethod
        def makeBox(*args, **kwargs): return None
        @staticmethod
        def makeCylinder(*args, **kwargs): return None
        @staticmethod
        def makePolygon(*args, **kwargs): return None
        @staticmethod
        def Face(*args, **kwargs): return None
    Part = _PartStub()

import math

try:
    import brick_utils
except Exception:
    # Dummy brick_utils so editors don't flag missing import; preserve apply_texture signature
    class _BrickUtilsStub:
        @staticmethod
        def apply_texture(shape, a, b, c, *args, **kwargs):
            return shape
    brick_utils = _BrickUtilsStub()

class ViewProviderFB:
    def __init__(self, vobj): vobj.Proxy = self
    def getIcon(self): return ""
    def getDefaultDisplayMode(self): return "Shaded"

class FB_Ledge:
    def __init__(self, obj):
        obj.addProperty("App::PropertyLength","Length","Dim").Length = 120.0
        obj.addProperty("App::PropertyLength","Height","Dim").Height = 35.0
        obj.addProperty("App::PropertyLength","Width","Dim").Width = 50.0
        # Parametri Slab
        obj.addProperty("App::PropertyBool","UseSlab","Slab").UseSlab = True
        obj.addProperty("App::PropertyLength","SlabH","Slab").SlabH = 5.0
        obj.addProperty("App::PropertyLength","Overhang","Slab").Overhang = 2.0
        # Parametri Texture
        obj.addProperty("App::PropertyBool","Texture","Texture").Texture = True
        obj.addProperty("App::PropertyLength","BrickL","Texture").BrickL = 20.0
        obj.addProperty("App::PropertyLength","BrickH","Texture").BrickH = 10.0
        obj.addProperty("App::PropertyLength","Groove","Texture").Groove = 1.2
        obj.addProperty("App::PropertyBool","LockTexture","Texture").LockTexture = False 
        obj.Proxy = self

    def execute(self, fp):
        L, H, W = fp.Length.Value, fp.Height.Value, fp.Width.Value
        
        if fp.UseSlab:
            SH, OH = fp.SlabH.Value, fp.Overhang.Value
            base_L, base_W, base_H = L - (2*OH), W - (2*OH), H - SH
            
            base_wall = Part.makeBox(base_L, base_W, base_H)
            if fp.Texture:
                base_wall = brick_utils.apply_texture(base_wall, base_L, base_H, base_W, fp.BrickL.Value, fp.BrickH.Value, fp.Groove.Value, sides=4)
            base_wall.translate(fc.Vector(OH, OH, 0))
            
            slab = Part.makeBox(L, W, SH).translate(fc.Vector(0, 0, base_H))
            fp.Shape = base_wall.fuse(slab)
        else:
            # Senza Slab: la base occupa tutta l'altezza e tutta la pianta
            base_wall = Part.makeBox(L, W, H)
            if fp.Texture:
                base_wall = brick_utils.apply_texture(base_wall, L, H, W, fp.BrickL.Value, fp.BrickH.Value, fp.Groove.Value, sides=4)
            fp.Shape = base_wall

class FB_Hubba:
    def __init__(self, obj):
        # Parametri Dimensionali
        obj.addProperty("App::PropertyLength","Length","Dim").Length = 150.0
        obj.addProperty("App::PropertyLength","Width","Dim").Width = 30.0
        obj.addProperty("App::PropertyLength","HeightStart","Dim").HeightStart = 60.0 # Altezza in cima
        obj.addProperty("App::PropertyLength","HeightEnd","Dim").HeightEnd = 20.0   # Altezza alla fine
        # Slab
        obj.addProperty("App::PropertyBool","UseSlab","Slab").UseSlab = True
        obj.addProperty("App::PropertyLength","SlabH","Slab").SlabH = 4.0
        obj.addProperty("App::PropertyLength","Overhang","Slab").Overhang = 2.0
        # Texture
        obj.addProperty("App::PropertyBool","Texture","Texture").Texture = True
        obj.addProperty("App::PropertyLength","BrickL","Texture").BrickL = 20.0
        obj.addProperty("App::PropertyLength","BrickH","Texture").BrickH = 10.0
        obj.addProperty("App::PropertyLength","Groove","Texture").Groove = 1.2
        obj.addProperty("App::PropertyBool","LockTexture","Texture").LockTexture = False 
        obj.Proxy = self

    def execute(self, fp):
        L, W = fp.Length.Value, fp.Width.Value
        HS, HE = fp.HeightStart.Value, fp.HeightEnd.Value
        
        # 1. Definizione profilo laterale Hubba (Trapezio inclinato)
        if fp.UseSlab:
            SH, OH = fp.SlabH.Value, fp.Overhang.Value
            bHS, bHE = HS - SH, HE - SH
            bW = W - (2 * OH)
            
            # Profilo Base
            pts = [fc.Vector(0,0,0), fc.Vector(L,0,0), fc.Vector(L,0,bHE), fc.Vector(0,0,bHS), fc.Vector(0,0,0)]
            base = Part.Face(Part.makePolygon(pts)).extrude(fc.Vector(0, bW, 0))
            if fp.Texture:
                # Approssimiamo l'altezza media per la texture
                base = brick_utils.apply_texture(base, L, max(bHS, bHE), bW, fp.BrickL.Value, fp.BrickH.Value, fp.Groove.Value, sides=4)
            base.translate(fc.Vector(0, OH, 0))
            
            # Profilo Slab
            pts_s = [fc.Vector(0,0,bHS), fc.Vector(L,0,bHE), fc.Vector(L,0,HE), fc.Vector(0,0,HS), fc.Vector(0,0,bHS)]
            slab = Part.Face(Part.makePolygon(pts_s)).extrude(fc.Vector(0, W, 0))
            fp.Shape = base.fuse(slab)
        else:
            pts = [fc.Vector(0,0,0), fc.Vector(L,0,0), fc.Vector(L,0,HE), fc.Vector(0,0,HS), fc.Vector(0,0,0)]
            shape = Part.Face(Part.makePolygon(pts)).extrude(fc.Vector(0, W, 0))
            if fp.Texture:
                shape = brick_utils.apply_texture(shape, L, max(HS, HE), W, fp.BrickL.Value, fp.BrickH.Value, fp.Groove.Value, sides=4)
            fp.Shape = shape

class FB_Steps:
    def __init__(self, obj):
        obj.addProperty("App::PropertyInteger","Steps","Base").Steps = 3
        obj.addProperty("App::PropertyLength","TotalHeight","Base").TotalHeight = 45.0
        obj.addProperty("App::PropertyLength","StepW","Base").StepW = 30.0
        obj.addProperty("App::PropertyLength","Width","Base").Width = 100.0
        # Rail Holes (Per tondini di metallo vero)
        obj.addProperty("App::PropertyBool","RailHoles","Rail").RailHoles = False
        obj.addProperty("App::PropertyLength","RailDiam","Rail").RailDiam = 6.2 # Es. tondino da 6mm
        obj.addProperty("App::PropertyLength","RailDist","Rail").RailDist = 50.0 # Distanza dal bordo
        # Slab e Texture (Mantieni logica precedente)
        obj.addProperty("App::PropertyBool","UseSlab","Slab").UseSlab = True
        obj.addProperty("App::PropertyLength","SlabH","Slab").SlabH = 4.0
        obj.addProperty("App::PropertyLength","Overhang","Slab").Overhang = 2.0
        obj.addProperty("App::PropertyBool","Texture","Texture").Texture = True
        obj.addProperty("App::PropertyLength","BrickL","Texture").BrickL = 20.0
        obj.addProperty("App::PropertyLength","BrickH","Texture").BrickH = 10.0
        obj.addProperty("App::PropertyLength","Groove","Texture").Groove = 1.2
        obj.addProperty("App::PropertyBool","LockTexture","Texture").LockTexture = False 
        obj.Proxy = self

    def execute(self, fp):
        res = None
        S = fp.Steps
        if S < 1: return
        
        # CALCOLO AUTOMATICO: Altezza totale diviso numero gradini
        total_H = fp.TotalHeight.Value
        step_h_calc = total_H / S 
        
        W = fp.StepW.Value
        TW = fp.Width.Value
        
        for i in range(S):
            curr_total_h = step_h_calc * (i + 1)
            
            if fp.UseSlab:
                SH, OH = fp.SlabH.Value, fp.Overhang.Value
                base_h = curr_total_h - SH
                base_width = TW - (2 * OH)
                
                # Creazione Base (Alzata) all'origine per la texture
                step_base = Part.makeBox(base_width, W, base_h)
                if fp.Texture and base_h > 0:
                    step_base = brick_utils.apply_texture(step_base, base_width, base_h, W, fp.BrickL.Value, fp.BrickH.Value, fp.Groove.Value, sides=4)
                
                # Traslazione dopo la texture
                step_base.translate(fc.Vector(OH, i * W, 0))
                
                # Creazione Slab (Pedata)
                slab = Part.makeBox(TW, W + OH, SH).translate(fc.Vector(0, i * W, base_h))
                current_step = step_base.fuse(slab)
            else:
                # Senza Slab: Blocco unico di mattoni
                step_base = Part.makeBox(TW, W, curr_total_h)
                if fp.Texture:
                    step_base = brick_utils.apply_texture(step_base, TW, curr_total_h, W, fp.BrickL.Value, fp.BrickH.Value, fp.Groove.Value, sides=4)
                step_base.translate(fc.Vector(0, i * W, 0))
                current_step = step_base                
            res = current_step if res is None else res.fuse(current_step)

        # Aggiunta fori per Rail
        if fp.RailHoles and res:
            r_rad = fp.RailDiam.Value / 2
            # Foro in cima (sull'ultimo gradino) e in fondo (sul primo)
            hole_top = Part.makeCylinder(r_rad, 20, fc.Vector(fp.RailDist.Value, (S-1)*W + W/2, total_H-15), fc.Vector(0,0,1))
            hole_bot = Part.makeCylinder(r_rad, 20, fc.Vector(fp.RailDist.Value, W/2, step_h_calc-15), fc.Vector(0,0,1))
            res = res.cut(hole_top.fuse(hole_bot))
        
        fp.Shape = res

class FB_Jersey:
    def __init__(self, obj):
        obj.addProperty("App::PropertyLength","Length","Base").Length = 120.0
        obj.addProperty("App::PropertyLength","Height","Base").Height = 60.0
        obj.addProperty("App::PropertyLength","BaseWidth","Base").BaseWidth = 50.0
        obj.addProperty("App::PropertyLength","TopWidth","Base").TopWidth = 20.0
        obj.addProperty("App::PropertyLength","BaseHeight","Forma").BaseHeight = 10.0
        obj.addProperty("App::PropertyLength","SlopeHeight","Forma").SlopeHeight = 15.0
        obj.addProperty("App::PropertyBool","EnableJoint","Incastro").EnableJoint = True
        obj.addProperty("App::PropertyLength","JointLen","Incastro").JointLen = 3.0
        obj.addProperty("App::PropertyLength","JointWidth","Incastro").JointWidth = 5.0
        obj.addProperty("App::PropertyLength","JointHeight","Incastro").JointHeight = 60.0
        obj.addProperty("App::PropertyLength","Tolerance","Incastro").Tolerance = 0.4
        obj.addProperty("App::PropertyBool","Texture","Texture").Texture = False
        obj.addProperty("App::PropertyLength","BrickL","Texture").BrickL = 20.0
        obj.addProperty("App::PropertyLength","BrickH","Texture").BrickH = 10.0
        obj.addProperty("App::PropertyLength","Groove","Texture").Groove = 1.2
        obj.addProperty("App::PropertyBool","LockTexture","Texture").LockTexture = True
        obj.Proxy = self
    def execute(self, fp):
        L, H, BW, TW, BH, SH = fp.Length.Value, fp.Height.Value, fp.BaseWidth.Value, fp.TopWidth.Value, fp.BaseHeight.Value, fp.SlopeHeight.Value
        pts = [fc.Vector(0,0,0), fc.Vector(BW,0,0), fc.Vector(BW,0,BH), fc.Vector(TW+(BW-TW)*0.75, 0, BH+SH), fc.Vector(BW/2+TW/2, 0, H), fc.Vector(BW/2-TW/2, 0, H), fc.Vector(BW-(TW+(BW-TW)*0.75), 0, BH+SH), fc.Vector(0,0,BH), fc.Vector(0,0,0)]
        shape = Part.Face(Part.makePolygon(pts)).extrude(fc.Vector(0, L, 0))
        if fp.EnableJoint:
            jl, jw, jh, tol = fp.JointLen.Value, fp.JointWidth.Value, fp.JointHeight.Value, fp.Tolerance.Value
            male = Part.makeBox(jw, jl, jh).translate(fc.Vector(BW/2 - jw/2, L, (H-jh)/2))
            female = Part.makeBox(jw+tol, jl+1.0, jh+tol).translate(fc.Vector(BW/2 - (jw+tol)/2, -1.0, (H-(jh+tol))/2))
            shape = shape.fuse(male).cut(female)
        if fp.Texture: shape = brick_utils.apply_texture(shape, BW, H, L, fp.BrickL.Value, fp.BrickH.Value, fp.Groove.Value, sides=3)
        fp.Shape = shape

class FB_QuarterPipe:
    def __init__(self, obj):
        obj.addProperty("App::PropertyLength","Radius","Base").Radius = 120.0
        obj.addProperty("App::PropertyLength","Platform","Base").Platform = 30.0
        obj.addProperty("App::PropertyLength","Width","Base").Width = 100.0
        obj.addProperty("App::PropertyLength","CopingDiam","Coping").CopingDiam = 6.0
        obj.addProperty("App::PropertyBool","CopingScasso","Coping").CopingScasso = True
        obj.addProperty("App::PropertyBool","WoodSlot","Legno").WoodSlot = True
        obj.addProperty("App::PropertyLength","WoodThick","Legno").WoodThick = 2.0
        obj.addProperty("App::PropertyBool","Texture","Texture").Texture = True
        obj.addProperty("App::PropertyLength","BrickL","Texture").BrickL = 20.0
        obj.addProperty("App::PropertyLength","BrickH","Texture").BrickH = 10.0
        obj.addProperty("App::PropertyLength","Groove","Texture").Groove = 1.2
        obj.addProperty("App::PropertyBool","LockTexture","Texture").LockTexture = False
        obj.Proxy = self
    def execute(self, fp):
        R, W, P = fp.Radius.Value, fp.Width.Value, fp.Platform.Value
        total_L = R + P
        shape = Part.makeBox(total_L, W, R).cut(Part.makeCylinder(R, W, fc.Vector(0,0,R), fc.Vector(0,1,0)))
        if fp.CopingDiam.Value > 0:
            c_pos = fc.Vector(R+1.0, 0, R-1.0)
            c_obj = Part.makeCylinder(fp.CopingDiam.Value/2, W, c_pos, fc.Vector(0,1,0))
            shape = shape.cut(c_obj) if fp.CopingScasso else shape.fuse(c_obj)
        if fp.WoodSlot:
            wt = fp.WoodThick.Value
            x_s = math.sqrt(2*wt*R - wt**2)
            trim = Part.makeBox(total_L-x_s, W-4, R+10).translate(fc.Vector(x_s, 2, -5))
            shape = shape.cut(Part.makeCylinder(R+wt, W, fc.Vector(0,0,R), fc.Vector(0,1,0)).common(trim))
        if fp.Texture: shape = brick_utils.apply_texture(shape, total_L, R, W, fp.BrickL.Value, fp.BrickH.Value, fp.Groove.Value, sides=3)
        fp.Shape = shape

class FB_Kicker:
    def __init__(self, obj):
        obj.addProperty("App::PropertyLength","Length","Base").Length = 150.0
        obj.addProperty("App::PropertyLength","Height","Base").Height = 40.0
        obj.addProperty("App::PropertyLength","Width","Base").Width = 100.0
        obj.addProperty("App::PropertyBool","Texture","Texture").Texture = True
        obj.addProperty("App::PropertyLength","BrickL","Texture").BrickL = 20.0
        obj.addProperty("App::PropertyLength","BrickH","Texture").BrickH = 10.0
        obj.addProperty("App::PropertyLength","Groove","Texture").Groove = 1.2
        obj.addProperty("App::PropertyBool","LockTexture","Texture").LockTexture = False
        obj.Proxy = self
    def execute(self, fp):
        L, H, W = fp.Length.Value, fp.Height.Value, fp.Width.Value
        wire = Part.makePolygon([fc.Vector(0,0,0), fc.Vector(L,0,0), fc.Vector(L,0,H), fc.Vector(0,0,0)])
        shape = Part.Face(wire).extrude(fc.Vector(0, W, 0))
        if fp.Texture: shape = brick_utils.apply_texture(shape, L, H, W, fp.BrickL.Value, fp.BrickH.Value, fp.Groove.Value, sides=3)
        fp.Shape = shape

class FB_Base:
    def __init__(self, obj):
        # Dimensioni
        obj.addProperty("App::PropertyLength","Length","Dim").Length = 200.0
        obj.addProperty("App::PropertyLength","Width","Dim").Width = 150.0
        obj.addProperty("App::PropertyLength","Thickness","Dim").Thickness = 8.0
        # Arrotondamenti Angoli (Verticali)
        obj.addProperty("App::PropertyLength","FilletFL","Angoli Terra").FilletFL = 20.0 # Front-Left
        obj.addProperty("App::PropertyLength","FilletFR","Angoli Terra").FilletFR = 20.0 # Front-Right
        obj.addProperty("App::PropertyLength","FilletBL","Angoli Terra").FilletBL = 20.0 # Back-Left
        obj.addProperty("App::PropertyLength","FilletBR","Angoli Terra").FilletBR = 20.0 # Back-Right
        # Arrotondamenti Spigoli Superiori
        obj.addProperty("App::PropertyLength","FilletTopFront","Bordi Superiori").FilletTopFront = 3.0
        obj.addProperty("App::PropertyLength","FilletTopBack","Bordi Superiori").FilletTopBack = 3.0
        obj.addProperty("App::PropertyLength","FilletTopLeft","Bordi Superiori").FilletTopLeft = 3.0
        obj.addProperty("App::PropertyLength","FilletTopRight","Bordi Superiori").FilletTopRight = 3.0
        # Texture
        obj.addProperty("App::PropertyBool","Tiles","Texture").Tiles = True
        obj.addProperty("App::PropertyBool","Rotate45","Texture").Rotate45 = False
        obj.addProperty("App::PropertyLength","TileSize","Texture").TileSize = 50.0
        obj.addProperty("App::PropertyLength","Groove","Texture").Groove = 1.0
        obj.addProperty("App::PropertyLength","GrooveDepth","Texture").GrooveDepth = 0.5
        obj.Proxy = self

    def execute(self, fp):
        L, W, T = fp.Length.Value, fp.Width.Value, fp.Thickness.Value
        shape = Part.makeBox(L, W, T)
        # 1. FILLET VERTICALI (Raggruppati per raggio per stabilità)
        fillets_v = {}
        for e in shape.Edges:
            v1, v2 = e.Vertexes[0].Point, e.Vertexes[1].Point
            if abs(v1.x - v2.x) < 0.001 and abs(v1.y - v2.y) < 0.001:
                r = 0
                if v1.x == 0 and v1.y == 0: r = fp.FilletFL.Value
                if v1.x == L and v1.y == 0: r = fp.FilletFR.Value
                if v1.x == 0 and v1.y == W: r = fp.FilletBL.Value
                if v1.x == L and v1.y == W: r = fp.FilletBR.Value
                if r > 0:
                    if r not in fillets_v: fillets_v[r] = []
                    fillets_v[r].append(e)
        
        for r, edges in fillets_v.items():
            shape = shape.makeFillet(r, edges)

        shape = shape.removeSplitter() # Pulisce le facce dopo i fillet verticali

        # 2. FILLET SUPERIORI
        fillets_t = {}
        for e in shape.Edges:
            mid = e.valueAt(e.FirstParameter + (e.LastParameter - e.FirstParameter)/2)
            if abs(mid.z - T) < 0.001:
                r = 0
                if abs(mid.y - 0) < 0.001: r = fp.FilletTopFront.Value
                if abs(mid.y - W) < 0.001: r = fp.FilletTopBack.Value
                if abs(mid.x - 0) < 0.001: r = fp.FilletTopLeft.Value
                if abs(mid.x - L) < 0.001: r = fp.FilletTopRight.Value
                if r > 0:
                    if r not in fillets_t: fillets_t[r] = []
                    fillets_t[r].append(e)

        for r, edges in fillets_t.items():
            try: shape = shape.makeFillet(r, edges)
            except: pass

        shape = shape.removeSplitter() # Pulisce prima di tagliare le piastrelle

        # 3. TEXTURE (Ultima operazione)
        if fp.Tiles:
            # Passiamo correttamente i parametri: shape, L, W, dimensione, larghezza fuga, rotazione, profondità
            shape = brick_utils.apply_horizontal_tiles(
                shape, L, W, fp.TileSize.Value, fp.Groove.Value, 
                fp.Rotate45, fp.GrooveDepth.Value
            )
            
        fp.Shape = shape.removeSplitter()
        
