from unittest.mock import patch
from io import BytesIO
from streamlit.testing.v1 import AppTest
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs


def test_app_upload_and_reposition(tmp_path):
    path = tmp_path / 'box.step'
    writer = STEPControl_Writer()
    writer.Transfer(BRepPrimAPI_MakeBox(10, 20, 30).Shape(), STEPControl_AsIs)
    writer.Write(str(path))
    upload = BytesIO(path.read_bytes())
    upload.name = 'box.step'
    upload.file_id = 'test-box'
    with patch('streamlit.file_uploader', return_value=[upload]):
        app = AppTest.from_file('app.py').run(timeout=30)
        assert not app.exception
        assert app.metric[1].value == '5.000 mm'
        app.number_input[0].set_value(100.0).run(timeout=30)
        assert not app.exception
        assert app.metric[1].value == '105.000 mm'
        assert len(app.get('plotly_chart')) == 1
