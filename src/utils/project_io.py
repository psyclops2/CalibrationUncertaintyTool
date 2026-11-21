"""Project validation and atomic JSON / ZIP persistence."""
import base64
import copy
import hashlib
import json
import os
import tempfile
import math
import re
import zipfile
from pathlib import Path
from decimal import Decimal


MAX_PROJECT_BYTES = 256 * 1024 * 1024
_IMAGE_TYPES = {'image/png': 'png', 'image/jpeg': 'jpg'}


def validate_assets(assets):
    """Images are addressed by SHA-256; no external paths are followed."""
    if not isinstance(assets, dict):
        raise ValueError('image_assets: expected an object')
    decoded = {}
    total = 0
    for ident, asset in assets.items():
        if not isinstance(ident, str) or not re.fullmatch(r'[0-9a-f]{64}', ident):
            raise ValueError('Invalid image ID')
        if not isinstance(asset, dict) or asset.get('media_type') not in _IMAGE_TYPES:
            raise ValueError('Unsupported image media type')
        if not isinstance(asset.get('data'), str) or len(asset['data']) > (MAX_PROJECT_BYTES + 2) // 3 * 4:
            raise ValueError('Invalid or oversized image data')
        try:
            raw = base64.b64decode(asset['data'], validate=True)
        except (KeyError, ValueError, TypeError) as error:
            raise ValueError('Invalid image data') from error
        total += len(raw)
        if total > MAX_PROJECT_BYTES:
            raise ValueError('Project images exceed size limit')
        is_png = raw.startswith(b'\x89PNG\r\n\x1a\n')
        is_jpeg = raw.startswith(b'\xff\xd8\xff')
        if not (is_png if asset['media_type'] == 'image/png' else is_jpeg):
            raise ValueError('Image signature does not match media type')
        if hashlib.sha256(raw).hexdigest() != ident:
            raise ValueError('Image checksum mismatch')
        decoded[ident] = raw
    return decoded


def read_project(path):
    """Read legacy JSON or a versioned ZIP without extracting files to disk."""
    if not zipfile.is_zipfile(path):
        if Path(path).stat().st_size > MAX_PROJECT_BYTES:
            raise ValueError('Project exceeds size limit')
        with open(path, encoding='utf-8-sig') as stream:
            data = json.load(stream)
    else:
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            names = [entry.filename for entry in entries]
            if len(names) != len(set(names)):
                raise ValueError('Duplicate ZIP entries')
            if sum(entry.file_size for entry in entries) > MAX_PROJECT_BYTES:
                raise ValueError('Project exceeds size limit')
            manifest = json.loads(archive.read('manifest.json'))
            if manifest.get('format') != 'CalibrationUncertaintyTool' or manifest.get('version') != 1:
                raise ValueError('Unsupported project archive version')
            data = json.loads(archive.read('project.json'))
            if not isinstance(data, dict):
                raise ValueError('Project must be an object')
            assets = data.get('image_assets', {})
            if not isinstance(assets, dict):
                raise ValueError('image_assets: expected an object')
            expected = {'manifest.json', 'project.json'}
            for ident, asset in assets.items():
                if not re.fullmatch(r'[0-9a-f]{64}', ident) or not isinstance(asset, dict):
                    raise ValueError('Invalid image reference')
                extension = _IMAGE_TYPES.get(asset.get('media_type'))
                if extension is None or set(asset) != {'media_type'}:
                    raise ValueError('Invalid archived image metadata')
                name = f'images/{ident}.{extension}'
                expected.add(name)
                asset['data'] = base64.b64encode(archive.read(name)).decode('ascii')
            if set(names) != expected:
                raise ValueError('Unexpected project archive entries')
    validate_project(data)
    return data


def write_project(path, data):
    """Persist JSON or ZIP atomically; standalone JSON embeds any images."""
    validate_project(data)
    if Path(path).suffix.lower() == '.json':
        encoded = json.dumps(data, indent=4, ensure_ascii=False, allow_nan=False,
            default=lambda v: str(v) if isinstance(v, Decimal) else _unsupported(v))
        if len(encoded.encode('utf-8')) > MAX_PROJECT_BYTES:
            raise ValueError('Project exceeds size limit')
        atomic_write_json(path, data)
        return
    payload = copy.deepcopy(data)
    images = validate_assets(payload.get('image_assets', {}))
    for asset in payload.get('image_assets', {}).values():
        asset.pop('data')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=Path(path).resolve().parent,
                                         prefix='.project-', suffix='.tmp', delete=False) as stream:
            temporary = stream.name
            with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('manifest.json', json.dumps({
                    'format': 'CalibrationUncertaintyTool', 'version': 1}))
                archive.writestr('project.json', json.dumps(payload, ensure_ascii=False,
                    indent=2, allow_nan=False, default=lambda v: str(v) if isinstance(v, Decimal) else _unsupported(v)))
                for ident, raw in images.items():
                    extension = _IMAGE_TYPES[payload['image_assets'][ident]['media_type']]
                    archive.writestr(f'images/{ident}.{extension}', raw)
            stream.flush()
            os.fsync(stream.fileno())
        if sum(e.file_size for e in _archive_entries(temporary)) > MAX_PROJECT_BYTES:
            raise ValueError('Project exceeds size limit')
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def _archive_entries(path):
    with zipfile.ZipFile(path) as archive:
        return archive.infolist()


def atomic_write_json(path, data):
    text = json.dumps(data, indent=4, ensure_ascii=False,
                      default=lambda value: str(value) if isinstance(value, Decimal) else _unsupported(value),
                      allow_nan=False)
    directory = os.path.dirname(os.path.abspath(path))
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory,
                                         prefix=".project-", suffix=".tmp", delete=False) as stream:
            temporary = stream.name
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def _unsupported(value):
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def validate_project(data):
    if not isinstance(data, dict):
        raise ValueError("Project must be a JSON object")
    validate_assets(data.get('image_assets', {}))
    if data.get('model_notation', 'legacy') not in ('legacy', 'workbench'):
        raise ValueError('Unknown model notation')
    if data.get('kind')=='monte_carlo_trial':
        raise ValueError('これはモデルではなくMCの試行記録です。モデルのスナップショットはproject項目に保存されています。')
    for key in ("variables", "result_variables", "value_names"):
        if key in data and (not isinstance(data[key], list) or
                            any(not isinstance(v, str) or not v.strip() for v in data[key])):
            raise ValueError(f"{key}: expected a list of nonempty names")
        if key in data and len(data[key]) != len(set(data[key])):
            raise ValueError(f"{key}: duplicate names")
    for key in ("document_info", "variable_values", "correlation_coefficients", "regressions"):
        if key in data and not isinstance(data[key], dict):
            raise ValueError(f"{key}: expected an object")
    for key in ("value_count", "current_value_index"):
        if key in data and (type(data[key]) is not int or data[key] < (1 if key == "value_count" else 0)):
            raise ValueError(f"{key}: invalid index/count")
    if "value_names" in data and not data["value_names"]:
        raise ValueError("value_names: at least one point is required")
    if not isinstance(data.get("last_equation", ""), str):
        raise ValueError("last_equation: expected text")
    for name, info in data.get("variable_values", {}).items():
        if not isinstance(info, dict):
            raise ValueError(f"variable_values.{name}: expected an object")
        if info.get("type", "A") not in ("A", "B", "fixed", "result"):
            raise ValueError(f"variable_values.{name}.type: unknown type")
        values = info.get("values", [])
        if not isinstance(values, list) or any(not isinstance(v, dict) for v in values):
            raise ValueError(f"variable_values.{name}.values: expected objects")
        for value in values:
            if 'coverage' in value:
                from .coverage import validate_coverage
                validate_coverage(value['coverage'])
            if 'evaluation_mode' in value:
                from .variable_utils import TYPE_A_MODES
                if value['evaluation_mode'] not in TYPE_A_MODES:
                    raise ValueError(f'{name}: unknown Type A evaluation mode')
            if 'input_source' in value:
                if info.get('type')!='A':
                    raise ValueError(f'{name}: linked statistical estimates require Type A')
                source = value['input_source']
                if not isinstance(source, dict) or source.get('kind') not in ('regression', 'table'):
                    raise ValueError(f'{name}: invalid input source')
                fields = ('model_id', 'x_expression') if source['kind']=='regression' else ('table_id','column')
                if any(not isinstance(source.get(field),str) or not source[field].strip() for field in fields):
                    raise ValueError(f'{name}: incomplete input source')
            if 'direct_input' in value and not isinstance(value['direct_input'],dict):
                raise ValueError(f'{name}: invalid saved direct input')
        for field in ("unit", "definition", "distribution"):
            if field in info and not isinstance(info[field], str):
                raise ValueError(f"variable_values.{name}.{field}: expected text")
    for name, model in data.get("regressions", {}).items():
        if not isinstance(model, dict):
            raise ValueError(f"regressions.{name}: expected an object")
        if 'id' in model and (not isinstance(model['id'],str) or not model['id']):
            raise ValueError(f'regressions.{name}: invalid ID')

    for key, value in data.get("document_info", {}).items():
        if not isinstance(value, str):
            raise ValueError(f"document_info.{key}: expected text")
    coefficients = data.get("correlation_coefficients", {})
    for name, row in coefficients.items():
        if not isinstance(row, dict):
            raise ValueError(f"correlation_coefficients.{name}: expected an object")
        for other, value in row.items():
            try:
                number = float(value)
            except (ValueError, TypeError):
                raise ValueError(f"correlation_coefficients.{name}.{other}: invalid coefficient")
            if not math.isfinite(number) or abs(number) > 1:
                raise ValueError(f"correlation_coefficients.{name}.{other}: coefficient out of range")
    declared = set(data.get("variables", [])) | set(data.get("result_variables", []))
    if any(name not in declared for name in data.get("variable_values", {})):
        raise ValueError("variable_values: undeclared variable")

    if "value_references" in data:
        from .value_references import validate_references
        validate_references(data["value_references"], len(data.get("value_names", [""])))
    tables = data.get('measurement_tables', {})
    if not isinstance(tables,dict) or any(not isinstance(table,dict) or not isinstance(table.get('columns'),list)
            or not isinstance(table.get('rows'),list) for table in tables.values()):
        raise ValueError('measurement_tables: expected named tables with columns and rows')
    for ident,table in tables.items():
        if not isinstance(ident,str) or not isinstance(table.get('name',''),str):
            raise ValueError('measurement_tables: invalid ID or name')
        for column in table['columns']:
            if not isinstance(column,dict) or not isinstance(column.get('id'),str) or any(
                    not isinstance(column.get(field,''),str) for field in ('unit','expression')):
                raise ValueError('measurement_tables: invalid column definition')
        if any(not isinstance(row,dict) or type(row.get('excluded',False)) is not bool for row in table['rows']):
            raise ValueError('measurement_tables: invalid observation row or exclusion flag')
