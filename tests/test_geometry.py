import pytest
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCP.IFSelect import IFSelect_RetDone
from geometry import read_step, assembly_properties


def test_step_import_and_weighted_assembly(tmp_path):
    path = tmp_path / 'box.step'
    writer = STEPControl_Writer()
    writer.Transfer(BRepPrimAPI_MakeBox(10, 20, 30).Shape(), STEPControl_AsIs)
    assert writer.Write(str(path)) == IFSelect_RetDone
    part = read_step(path)
    assert part.volume == pytest.approx(6000)
    assert part.center == pytest.approx((5, 10, 15))
    assert part.triangles
    mass, center, masses, _ = assembly_properties([part, part], [(0, 0, 0), (100, -20, 40)], [1000, 3000])
    assert masses == pytest.approx([0.006, 0.018])
    assert mass == pytest.approx(0.024)
    assert center == pytest.approx((80, -5, 45))
    with pytest.raises(ValueError):
        assembly_properties([part], [(0, 0, 0)], [0])


def test_invalid_step(tmp_path):
    path = tmp_path / 'broken.stp'
    path.write_text('not a STEP file')
    with pytest.raises(ValueError):
        read_step(path)
