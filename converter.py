import csv
import io

WELLS = [f'{r}{c:02}' for c in range(1, 13) for r in 'ABCDEFGH']
FIELDS = 'Well SampleName InjectionProtocol Application DyeSet RunModule1 SizeStandard AnalysisSettings FileNameConvention ResultsGroup SampleType Panel CustomFields1 AutoAnalysisGroupName'.split()
DEFAULTS = dict(zip(FIELDS[2:], ['INV24plex', 'HID', 'BT6', 'INV24plex', 'BTO', 'HID_6Dye_Default', 'HID_DNAxpress', 'HID_SHSU', 'Sample', '', '', '']))
PLATE_DEFAULTS = dict(zip('PsmVersion InstrumentModel PlateName PlateApplicationType PlateFormat NumCaps CapillaryLength Polymer Barcode Owner AutoAnalysis'.split(), ['2', '3600', '', 'HID', '96', '8', '36', 'POP4', '', '', 'FALSE']))

ASSAY_SETTINGS = {
    'IdentiFiler Plus': {'RunModule1': 'HID_G5_36_POP4', 'InjectionProtocol': 'HID_Protocol_G5_36_POP4', 'DyeSet': 'G5 (DS-33)', 'SizeStandard': 'GS600_LIZ_(60-460)'},
    'Investigator 24Plex': {'RunModule1': 'INV24plex Inst', 'InjectionProtocol': 'INV24plex INST', 'DyeSet': 'BT6', 'SizeStandard': 'BTO'},
    'GlobalFiler': {'RunModule1': 'HID_J6_36_POP4', 'InjectionProtocol': 'HID_Protocol_J6_36_POP4', 'DyeSet': 'J6 (DS-36)', 'SizeStandard': 'GS600_LIZ_(60-460)'},
}

def assay_key(value):
    key = value.strip().casefold()
    return 'identifiler plus' if key == 'identifiler' else key


def parse_text(data):
    text = None
    for encoding in ('utf-8-sig', 'utf-16', 'cp1252'):
        try:
            text = data.decode(encoding)
            break
        except UnicodeError:
            pass
    if text is None:
        raise ValueError('Unable to decode the text file.')
    rows = list(csv.reader(io.StringIO(text), delimiter='\t'))
    plate, samples, header = PLATE_DEFAULTS.copy(), {}, None
    for i, row in enumerate(rows):
        if not row or not any(row):
            continue
        if row[0] == 'Plate Name' and i + 1 < len(rows):
            source = dict(zip(row, rows[i + 1]))
            for old, new in [('Plate Name', 'PlateName'), ('Application Type', 'PlateApplicationType'), ('Capillary Length (cm)', 'CapillaryLength'), ('Polymer', 'Polymer'), ('Owner Name', 'Owner'), ('Barcode Number', 'Barcode')]:
                plate[new] = source.get(old, plate[new])
            if source.get('Number of Wells', '96') != '96':
                raise ValueError('Only 96-well plates are supported.')
        elif row[0] == 'Well':
            header = row
            if not {'Well', 'Sample Name', 'Sample Type'}.issubset(header):
                raise ValueError('The table needs Well, Sample Name, and Sample Type columns.')
        elif header:
            source = dict(zip(header, row))
            well = source.get('Well', '').strip().upper()
            if len(well) >= 2 and well[1:].isdigit():
                well = f'{well[0]}{int(well[1:]):02}'
            if well not in WELLS:
                raise ValueError(f'Invalid well: {well}')
            if well in samples:
                raise ValueError(f'Duplicate well: {well}')
            if not source.get('Sample Name', '').strip():
                raise ValueError(f'Missing sample name at {well}.')
            samples[well] = {**DEFAULTS, **next((settings for assay, settings in ASSAY_SETTINGS.items() if assay_key(assay) == assay_key(source.get('Assay', ''))), {}), '_Assay': source.get('Assay', '').strip(), 'SampleName': source['Sample Name'], 'SampleType': source.get('Sample Type') or 'Sample'}
    if not header or not samples:
        raise ValueError('No populated well table was found.')
    return plate, samples

def move_sample(samples, source, destination):
    if source not in samples or destination not in WELLS:
        raise ValueError('Choose a populated source and a valid destination.')
    if source == destination:
        return
    moving = samples.pop(source)
    if destination in samples:
        samples[source] = samples[destination]
    samples[destination] = moving

def export_csv(plate, samples, separators=True):
    buffer = io.StringIO(newline='')
    writer = csv.writer(buffer, lineterminator='\r\n')
    def padded(row):
        writer.writerow(row + [''] * (14 - len(row)))
    for key in ('PsmVersion', 'InstrumentModel'):
        padded(['#' + key])
        padded([plate[key]])
    keys = list(PLATE_DEFAULTS)[2:]
    padded(['#' + key for key in keys])
    padded([plate[key] for key in keys])
    writer.writerow(['#' + key for key in FIELDS])
    previous = None
    for well in WELLS:
        if well not in samples:
            continue
        if separators and previous is not None and previous != well[1:]:
            padded([])
        writer.writerow([well] + [samples[well].get(key, '') for key in FIELDS[1:]])
        previous = well[1:]
    return buffer.getvalue()


def move_group(samples, sources, anchor, destination):
    sources = set(sources)
    if not sources or anchor not in sources or destination not in WELLS or not sources.issubset(samples):
        raise ValueError('Select populated wells and a valid destination.')
    if len(sources) == 1:
        move_sample(samples, anchor, destination)
        return
    dr = ord(destination[0]) - ord(anchor[0])
    dc = int(destination[1:]) - int(anchor[1:])
    targets = {}
    for source in sources:
        row, col = ord(source[0]) + dr, int(source[1:]) + dc
        if not ord('A') <= row <= ord('H') or not 1 <= col <= 12:
            raise ValueError('The entire group must fit inside the plate.')
        target = f'{chr(row)}{col:02}'
        if target in samples and target not in sources:
            raise ValueError(f'{target} contains an unselected sample. Choose an empty area or include that sample in your selection.')
        targets[target] = samples[source]
    for source in sources:
        del samples[source]
    samples.update(targets)




def apply_assay_settings(samples, original_samples, output_assay=None):
    """Update assay defaults without changing current sample names or well positions."""
    if output_assay is not None and output_assay not in ASSAY_SETTINGS:
        raise ValueError('Unknown output assay.')
    original_assays = {s['_Assay'] for s in original_samples.values()}
    for sample in samples.values():
        assay = sample.get('_Assay')
        if not assay:
            matches = {s['_Assay'] for s in original_samples.values()
                       if s['SampleName'] == sample['SampleName'] and s['SampleType'] == sample['SampleType']}
            if len(matches) == 1:
                assay = next(iter(matches))
            elif len(original_assays) == 1:
                assay = next(iter(original_assays))
        if assay:
            sample['_Assay'] = assay
            target_assay = output_assay or assay
            settings = next((v for k, v in ASSAY_SETTINGS.items() if assay_key(k) == assay_key(target_assay)), {})
            sample.update({key: DEFAULTS[key] for key in ('InjectionProtocol', 'RunModule1', 'DyeSet', 'SizeStandard')})
            sample.update(settings)


