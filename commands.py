import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import FreeCAD as fc  # type: ignore
    import FreeCADGui as fcg  # type: ignore
    import Part  # type: ignore
    import PartDesign  # type: ignore
else:
    try:
        import FreeCAD as fc
        import FreeCADGui as fcg
        import Part
        import PartDesign
    except Exception:
        fc = None
        fcg = None
        Part = None
        PartDesign = None

from PySide2 import QtWidgets   # type: ignore

ICONDIR = os.path.join(fc.getUserAppDataDir(), "Mod", "FingerboardParkPro", "icons")

def setup_obj(name, cls):
    import features
    doc = fc.activeDocument() or fc.newDocument()
    obj = doc.addObject("Part::FeaturePython", name)
    cls(obj)
    if fc.GuiUp:
        features.ViewProviderFB(obj.ViewObject)
        obj.ViewObject.Visibility = True
    doc.recompute()
    fcg.SendMsgToActiveView("ViewFit")

class CmdBake:
    def GetResources(self):
        return {'MenuText': 'Crea Body', 'Pixmap': os.path.join(ICONDIR, 'FB_Bake.svg')}

    def Activated(self):
        selection = fcg.Selection.getSelection()
        if not selection: return
        doc = fc.activeDocument()

        for obj in selection:
            try:
                body = doc.addObject('PartDesign::Body', obj.Name + "_Body")
                if fc.GuiUp:
                    body.ViewObject.ShapeColor = (0.7, 0.7, 0.7)
                fc.Console.PrintMessage(f"Body creato per {obj.Name}. Spostlo al suo interno\n")
            except Exception as e:
                fc.Console.PrintError(f"Bake Fallito: {str(e)}\n")

        doc.recompute()

class CmdKicker:
    def GetResources(self): return {'MenuText': 'Kicker', 'Pixmap': os.path.join(ICONDIR, 'FB_Kicker.svg')}
    def Activated(self): 
        import features
        setup_obj("Kicker", features.FB_Kicker)

class CmdQP:
    def GetResources(self): return {'MenuText': 'QuarterPipe', 'Pixmap': os.path.join(ICONDIR, 'FB_QP.svg')}
    def Activated(self): 
        import features
        setup_obj("QuarterPipe", features.FB_QuarterPipe)

class CmdLedge:
    def GetResources(self): return {'MenuText': 'Ledge', 'Pixmap': os.path.join(ICONDIR, 'FB_Ledge.svg')}
    def Activated(self): 
        import features
        setup_obj("Ledge", features.FB_Ledge)

class CmdSteps:
    def GetResources(self): return {'MenuText': 'Gradini', 'Pixmap': os.path.join(ICONDIR, 'FB_Steps.svg')}
    def Activated(self): 
        import features
        setup_obj("Steps", features.FB_Steps)

class CmdHubba:
    def GetResources(self): return {'MenuText': 'Hubba', 'Pixmap': os.path.join(ICONDIR, 'FB_Hubba.svg')}
    def Activated(self): 
        import features
        setup_obj("Hubba", features.FB_Hubba)

class CmdJersey:
    def GetResources(self): return {'MenuText': 'Jersey', 'Pixmap': os.path.join(ICONDIR, 'FB_Jersey.svg')}
    def Activated(self): 
        import features
        setup_obj("Jersey", features.FB_Jersey)

class CmdBase:
    def GetResources(self): return {'MenuText': 'Pavimento', 'Pixmap': os.path.join(ICONDIR, 'FB_Base.svg')}
    def Activated(self): 
        import features
        setup_obj("BasePark", features.FB_Base)

class CmdTextureToggle:
    def GetResources(self):
        return {
            'MenuText': 'Attiva/Disattiva Texture',
            'Pixmap': os.path.join(ICONDIR, 'FB_TextureToggle.svg'),
            'ToolTip': 'Spegne o accende le texture (rispetta il LockTexture)'
        }

    def Activated(self):
        doc = fc.activeDocument()
        if not doc: return
        
        # Determiniamo il nuovo stato basandoci sul primo oggetto non bloccato
        new_state = None
        for obj in doc.Objects:
            if hasattr(obj, "Texture") and not getattr(obj, "LockTexture", False):
                if new_state is None:
                    new_state = not obj.Texture
                obj.Texture = new_state
        
        doc.recompute()
        fc.Console.PrintMessage(f"Texture globali aggiornate (oggetti bloccati ignorati).\n")

class CmdCreateSplitProxy:
    def GetResources(self):
        return {
            'MenuText': '1. Crea Piano con Mirino',
            'Pixmap': os.path.join(ICONDIR, 'FB_Proxy.svg'),
            'ToolTip': 'Il centro della croce indica dove nascerà il perno'
        }

    def Activated(self):
        doc = fc.activeDocument() or fc.newDocument()
        for o in doc.Objects:
            if "SplitProxy" in o.Name: doc.removeObject(o.Name)
            
        # --- CREAZIONE PROXY CON MIRINO ---
        size = 150.0
        # 1. Il piano (box sottile)
        plane = Part.makeBox(1.0, size, size)
        plane.translate(fc.Vector(-0.5, -size/2, -size/2))
        
        # 2. Il Mirino (Croce)
        line_v = Part.LineSegment(fc.Vector(0, 0, -size/2), fc.Vector(0, 0, size/2)).toShape()
        line_h = Part.LineSegment(fc.Vector(0, -size/2, 0), fc.Vector(0, size/2, 0)).toShape()
        
        # Uniamo tutto in un unico oggetto
        proxy_shape = Part.Compound([plane, line_v, line_h])
        
        proxy = doc.addObject("Part::Feature", "SplitProxy")
        proxy.Shape = proxy_shape
        
        if fc.GuiUp:
            proxy.ViewObject.Transparency = 70
            proxy.ViewObject.ShapeColor = (1.0, 0.2, 0.2) # Rosso
            proxy.ViewObject.LineColor = (1.0, 1.0, 1.0)  # Croce bianca
            proxy.ViewObject.LineWidth = 3
            fcg.Selection.clearSelection()
            fcg.Selection.addSelection(proxy)
            fcg.runCommand("Std_TransformManip") 
        
        fc.Console.PrintMessage("Posiziona il centro della croce dove vuoi l'incastro.\n")

class CmdConfirmSplit:
    def GetResources(self):
        return {
            'MenuText': '2. Conferma Split',
            'Pixmap': os.path.join(ICONDIR, 'FB_SplitConfirm.svg'),
            'ToolTip': 'Taglia e inserisce il perno esattamente al centro del mirino'
        }

    def Activated(self):
        selection = fcg.Selection.getSelection()
        proxy = None
        target = None

        for s in selection:
            if "SplitProxy" in s.Name: proxy = s
            elif hasattr(s, "Shape") and not "SplitProxy" in s.Name: target = s

        if not proxy or not target:
            QtWidgets.QMessageBox.warning(None, "Split", "Seleziona l'ostacolo e il piano con la croce!")
            return

        doc = fc.activeDocument()
        
        # 1. Volume di taglio basato sul piano del Proxy
        bbox = target.Shape.BoundBox
        c_size = max(bbox.XLength, bbox.YLength, bbox.ZLength) * 2
        
        cutter_vol = Part.makeBox(c_size, c_size, c_size)
        cutter_vol.Placement = proxy.Placement
        # Spostiamo il volume in modo che la faccia coincida con lo 0 del proxy
        cutter_vol.translate(proxy.Placement.Rotation.multVec(fc.Vector(-c_size, -c_size/2, -c_size/2)))

        part_a = target.Shape.common(cutter_vol)
        part_b = target.Shape.cut(cutter_vol)

        # 2. Creazione Giunti Smussati (Joints)
        tol = 0.2 # Tolleranza per il taglio
        jw, jl, jh = 5.0, 3.0, 30.0 # Dimensioni fisse del giunto
        ch = 1.5 # Smusso

        def make_joint(w, l, h, c, t=0):
            # Crea il box centrato sul suo 0,0,0
            j = Part.makeBox(l + t, w + t, h + t)
            j.translate(fc.Vector(-(l+t)/2, -(w+t)/2, -(h+t)/2))
            if c > 0: j = j.makeChamfer(c, j.Edges)
            return j

        pin = make_joint(jw, jl, jh, ch)
        hole = make_joint(jw, jl, jh, ch, tol)

        # Il perno prende ESATTAMENTE il placement del proxy. 
        # Siccome il perno è creato centrato e il mirino è al centro del proxy,
        # l'allineamento è matematicamente perfetto.
        pin.Placement = proxy.Placement
        hole.Placement = proxy.Placement

        # 3. Operazioni finali
        obj_a = doc.addObject("Part::Feature", target.Name + "_Part_A")
        obj_a.Shape = part_a.fuse(pin)
        
        obj_b = doc.addObject("Part::Feature", target.Name + "_Part_B")
        obj_b.Shape = part_b.cut(hole)

        # Pulizia
        doc.removeObject(proxy.Name)
        target.ViewObject.Visibility = False
        doc.recompute()
        fc.Console.PrintMessage("Split eseguito\n")

fcg.addCommand('FB_Proxy', CmdCreateSplitProxy())
fcg.addCommand('FB_SplitConfirm', CmdConfirmSplit())
fcg.addCommand('FB_TextureToggle', CmdTextureToggle())
fcg.addCommand('FB_Hubba', CmdHubba())
fcg.addCommand('FB_Bake', CmdBake())
fcg.addCommand('FB_Kicker', CmdKicker())
fcg.addCommand('FB_QP', CmdQP())
fcg.addCommand('FB_Ledge', CmdLedge())
fcg.addCommand('FB_Steps', CmdSteps())
fcg.addCommand('FB_Jersey', CmdJersey())
fcg.addCommand('FB_Base', CmdBase())