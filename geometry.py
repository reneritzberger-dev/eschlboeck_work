"""STEP import and mass properties. All internal lengths are millimetres."""
from dataclasses import dataclass
from pathlib import Path
import math

from OCP.BRep import BRep_Tool
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.GProp import GProp_GProps
from OCP.IFSelect import IFSelect_RetDone
from OCP.STEPControl import STEPControl_Reader
from OCP.TopAbs import TopAbs_FACE, TopAbs_SOLID, TopAbs_SHELL
from OCP.TopExp import TopExp_Explorer
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import TopoDS


@dataclass
class Part:
    name: str
    volume: float
    center: tuple[float, float, float]
    vertices: list
    triangles: list


def read_step(path: str | Path, name: str | None = None) -> Part:
    reader = STEPControl_Reader()
    # OCCT converts STEP length units to its default target unit (mm).
    if reader.ReadFile(str(path)) != IFSelect_RetDone:
        raise ValueError('Die Datei konnte nicht als STEP gelesen werden.')
    if reader.TransferRoots() == 0:
        raise ValueError('Die STEP-Datei enthält keine übertragbare Geometrie.')
    shape = reader.OneShape()
    if shape.IsNull() or not BRepCheck_Analyzer(shape).IsValid():
        raise ValueError('Die Geometrie ist leer oder ungültig.')
    solids = TopExp_Explorer(shape, TopAbs_SOLID)
    if not solids.More():
        raise ValueError('Für die Masseberechnung werden geschlossene Volumenkörper benötigt.')
    # Reject free surfaces/shells; otherwise they would silently contribute no mass.
    for kind, ancestor in [(TopAbs_FACE, TopAbs_SOLID), (TopAbs_SHELL, TopAbs_SOLID)]:
        if TopExp_Explorer(shape, kind, ancestor).More():
            raise ValueError('Die Datei enthält Flächen außerhalb geschlossener Volumenkörper.')
    volume = 0.0
    weighted = [0.0, 0.0, 0.0]
    while solids.More():
        solid = TopoDS.Solid_s(solids.Current())
        if not BRep_Tool.IsClosed_s(solid):
            # Solid closure is checked by the boundary shells below.
            shells = TopExp_Explorer(solid, TopAbs_SHELL)
            while shells.More():
                if not BRep_Tool.IsClosed_s(shells.Current()):
                    raise ValueError('Ein Volumenkörper ist nicht geschlossen.')
                shells.Next()
        props = GProp_GProps()
        BRepGProp.VolumeProperties_s(solid, props)
        v = abs(props.Mass())
        c = props.CentreOfMass()
        volume += v
        for i, value in enumerate((c.X(), c.Y(), c.Z())):
            weighted[i] += v * value
        solids.Next()
    if not math.isfinite(volume) or volume <= 1e-9:
        raise ValueError('Die Datei besitzt kein positives Volumen.')
    center = tuple(value / volume for value in weighted)
    BRepMesh_IncrementalMesh(shape, 0.5, False, 0.3, True)
    vertices, triangles = [], []
    faces = TopExp_Explorer(shape, TopAbs_FACE)
    while faces.More():
        loc = TopLoc_Location()
        mesh = BRep_Tool.Triangulation_s(TopoDS.Face_s(faces.Current()), loc)
        if mesh is not None:
            offset = len(vertices)
            for i in range(1, mesh.NbNodes() + 1):
                p = mesh.Node(i).Transformed(loc.Transformation())
                vertices.append((p.X(), p.Y(), p.Z()))
            for i in range(1, mesh.NbTriangles() + 1):
                triangles.append(tuple(offset + j - 1 for j in mesh.Triangle(i).Get()))
        faces.Next()
    if not triangles:
        raise ValueError('Die Geometrie konnte nicht für die Anzeige vernetzt werden.')
    return Part(name or Path(path).name, volume, center, vertices, triangles)


def assembly_properties(parts, offsets, densities):
    if not parts or len(parts) != len(offsets) or len(parts) != len(densities):
        raise ValueError('Bauteile, Positionen und Dichten müssen vollständig sein.')
    masses, centers = [], []
    for part, offset, density in zip(parts, offsets, densities):
        if not math.isfinite(density) or density <= 0 or len(offset) != 3 or not all(math.isfinite(x) for x in offset):
            raise ValueError('Dichten müssen positiv und Koordinaten endlich sein.')
        masses.append(part.volume * density / 1e9)  # mm³ * kg/m³ -> kg
        centers.append(tuple(a + b for a, b in zip(part.center, offset)))
    mass = sum(masses)
    center = tuple(sum(m * c[i] for m, c in zip(masses, centers)) / mass for i in range(3))
    return mass, center, masses, centers
