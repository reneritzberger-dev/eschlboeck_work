"""Local STEP assembly centre-of-mass viewer."""
import tempfile
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from geometry import read_step, assembly_properties

st.set_page_config(page_title='Baugruppen-Schwerpunkt', layout='wide')
st.title('Baugruppen-Schwerpunkt')
st.write('STEP-Dateien laden, Bauteile verschieben und den gemeinsamen Schwerpunkt berechnen.')
st.info('Längen und Verschiebungen: mm · Dichte: kg/m³ · Masse: kg. Jedes geladene Modell hat eine einheitliche Dichte. Überlappende Körper werden als separate Massen addiert.')


@st.cache_data(show_spinner=False)
def load_part(data, name):
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / 'model.step'
        path.write_bytes(data)
        return read_step(path, name)


uploads = st.file_uploader('Bauteile auswählen', type=['stp', 'step'], accept_multiple_files=True)
parts, offsets, densities = [], [], []
for index, upload in enumerate(uploads):
    try:
        with st.spinner(f'{upload.name} wird geladen …'):
            part = load_part(upload.getvalue(), upload.name)
    except Exception as exc:
        st.error(f'{upload.name}: Import fehlgeschlagen. {exc}')
        continue
    with st.expander(f'{index + 1}. {part.name}', expanded=True):
        columns = st.columns(4)
        offset = tuple(columns[i].number_input(f'{axis} [mm]', value=0.0, key=f'{index}_{upload.file_id}_{axis}') for i, axis in enumerate('XYZ'))
        density = columns[3].number_input('Dichte [kg/m³]', min_value=0.001, value=7850.0, key=f'{index}_{upload.file_id}_density')
        st.caption(f'Volumen: {part.volume / 1000:,.3f} cm³ · Lokaler Schwerpunkt: ' + ', '.join(f'{v:.3f}' for v in part.center) + ' mm')
    parts.append(part)
    offsets.append(offset)
    densities.append(density)

if parts:
    mass, center, masses, centers = assembly_properties(parts, offsets, densities)
    if len(parts) != len(uploads):
        st.warning('Die Berechnung enthält nur die erfolgreich importierten Dateien.')
    columns = st.columns(4)
    columns[0].metric('Gesamtmasse', f'{mass:.4f} kg')
    for i, axis in enumerate('XYZ'):
        columns[i + 1].metric(f'Schwerpunkt {axis}', f'{center[i]:.3f} mm')
    figure = go.Figure()
    for part, offset in zip(parts, offsets):
        vertices = [tuple(p[i] + offset[i] for i in range(3)) for p in part.vertices]
        x, y, z = zip(*vertices)
        a, b, c = zip(*part.triangles)
        figure.add_trace(go.Mesh3d(x=x, y=y, z=z, i=a, j=b, k=c, name=part.name, opacity=0.7, showlegend=True))
    figure.add_trace(go.Scatter3d(x=[center[0]], y=[center[1]], z=[center[2]], mode='markers', marker=dict(size=8, color='red', symbol='diamond'), name='Gesamtschwerpunkt'))
    figure.update_layout(scene=dict(aspectmode='data', xaxis_title='X [mm]', yaxis_title='Y [mm]', zaxis_title='Z [mm]'), height=650, uirevision='assembly')
    st.plotly_chart(figure, use_container_width=True)
    st.dataframe([{'Bauteil': p.name, 'Masse [kg]': m, 'Schwerpunkt X [mm]': c[0], 'Schwerpunkt Y [mm]': c[1], 'Schwerpunkt Z [mm]': c[2]} for p, m, c in zip(parts, masses, centers)], hide_index=True)
else:
    st.write('Lade mindestens einen geschlossenen STEP-Volumenkörper hoch.')
