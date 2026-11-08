from pathlib import Path
import hashlib
import re
import importlib
import json
import converter
importlib.reload(converter)
import streamlit as st
import streamlit.components.v1 as components
from converter import WELLS, FIELDS, parse_text, move_sample, move_group, export_csv, ASSAY_SETTINGS, apply_assay_settings

st.set_page_config(page_title='CE Plate Planner', page_icon='🧬', layout='wide')
plate_view = components.declare_component('ce_plate', path=str(Path(__file__).parent / 'plate'))
st.title('CE Plate Planner')
st.caption('Upload a 3500 text layout, arrange your plate, and export the CSV.')
output_assay_choice = st.selectbox('Output assay', ['Use assay from text file', 'Investigator 24Plex', 'GlobalFiler', 'IdentiFiler Plus'], help='Choose the kit settings for the CSV. Sample names and well positions stay as arranged.')
output_assay = None if output_assay_choice == 'Use assay from text file' else output_assay_choice
upload = st.file_uploader('Plate layout text file', type=['txt'])
if upload is None:
    st.info('Upload a text file to populate the 96-well plate.')
    st.stop()
data = upload.getvalue()
digest = hashlib.sha256(data).hexdigest()
if st.session_state.get('upload_digest') != digest:
    try:
        plate, samples = parse_text(data)
    except ValueError as error:
        st.error(str(error))
        st.stop()
    st.session_state.update(upload_digest=digest, plate=plate, samples=samples, last_move=None, revision=0)
plate, samples = st.session_state.plate, st.session_state.samples
settings_version = hashlib.sha256(json.dumps(ASSAY_SETTINGS, sort_keys=True).encode()).hexdigest()
if st.session_state.get('assay_settings_version') != (digest, settings_version, output_assay):
    _, original_samples = parse_text(data)
    apply_assay_settings(samples, original_samples, output_assay)
    st.session_state.assay_settings_version = (digest, settings_version, output_assay)
    st.session_state.revision += 1
st.caption(f'{len(samples)} occupied wells · {96-len(samples)} empty wells')
st.write('Hold the left mouse button and drag across wells to select samples. Release, then drag from a selected sample to move the group while preserving its arrangement. Click an empty well to clear selection. Single samples still swap with occupied wells.')
event = plate_view(samples=samples, key='plate_' + digest, default=None)
if event and event.get('id') != st.session_state.last_move:
    st.session_state.last_move = event.get('id')
    try:
        move_group(samples, event.get('sources', [event.get('source')]), event.get('source'), event.get('destination'))
        st.session_state.revision += 1
    except ValueError as error:
        st.session_state.move_error = str(error)
    st.rerun()
if st.session_state.get('move_error'):
    st.warning(st.session_state.pop('move_error'))
st.subheader('CSV settings')
st.caption('Kit settings follow the output assay choice. Plate metadata comes from the uploaded text where available. Sample names and types are preserved. You can edit the settings below.')
with st.expander('Plate and instrument settings', expanded=True):
    columns = st.columns(3)
    for i, (key, value) in enumerate(plate.items()):
        plate[key] = columns[i % 3].text_input(key, value=value, key=f'{digest}_plate_{key}')
with st.expander('Sample names and per-well settings', expanded=True):
    records = [{'Well': w, **{key: samples[w].get(key, '') for key in FIELDS[1:]}} for w in WELLS if w in samples]
    edited = st.data_editor(records, disabled=['Well'], column_order=FIELDS, hide_index=True, width='stretch', key=f'editor_{digest}_{st.session_state.revision}')
    changed = False
    for record in edited:
        updated = {key: str(record.get(key) or '') for key in FIELDS[1:]}
        if any(samples[record['Well']].get(key, '') != value for key, value in updated.items()):
            samples[record['Well']].update(updated)
            changed = True
    if changed:
        st.rerun()
separators = True
invalid = any(not sample['SampleName'].strip() or not sample['SampleType'].strip() for sample in samples.values())
if plate['PlateFormat'] != '96' or invalid:
    st.error('PlateFormat must be 96. Every occupied well needs a sample name and sample type.')
    st.stop()
csv_text = export_csv(plate, samples, separators)
plate_filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', plate['PlateName'].strip()).rstrip(' .') or 'ce_plate'
st.download_button('Download plate CSV', csv_text.encode('utf-8'), file_name=plate_filename + '.csv', mime='text/csv')
with st.expander('Preview exact CSV contents'):
    st.code(csv_text, language='csv')






