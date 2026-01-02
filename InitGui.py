import os
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    # Provide typing stubs without importing the actual FreeCAD modules to avoid "missing import" diagnostics in editors.
    FreeCAD: Any
    FreeCADGui: Any
else:
    try:
        import FreeCAD
        import FreeCADGui
    except Exception:
        # Running outside FreeCAD (editor or type-checking); provide stubs to avoid import errors
        FreeCAD = None
        FreeCADGui = None

class FingerboardParkProWorkbench(getattr(FreeCADGui, "Workbench", object)):
    # Usa il nome intero FreeCAD invece di fc per evitare ambiguità
    ICONDIR = os.path.join(FreeCAD.getUserAppDataDir(), "Mod", "FingerboardParkPro", "icons")
    Icon = os.path.join(ICONDIR, "Workbench.svg")
    
    MenuText = "Fingerboard Park Pro"
    def Initialize(self):
        import commands
        # Aggiungi "FB_Split" prima di "FB_Bake"
        self.cmd_list = ["FB_Kicker", "FB_QP", "FB_Ledge", "FB_Steps", "FB_Hubba", "FB_Jersey", "FB_Base", "FB_Proxy", "FB_SplitConfirm", "FB_Bake", "FB_TextureToggle"]    
        self.appendToolbar("Ostacoli V13 Pro", self.cmd_list)

    def GetClassName(self): return "Gui::PythonWorkbench"

if FreeCADGui is not None:
    FreeCADGui.addWorkbench(FingerboardParkProWorkbench())