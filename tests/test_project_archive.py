import base64
import hashlib
import json
import zipfile

import pytest
from PySide6.QtGui import QImage
from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtWidgets import QFileDialog, QMessageBox

from src.utils.project_io import read_project, write_project
from tests.test_project_safety import window


def sample_image():
    image = QImage(2, 2, QImage.Format_RGB32)
    image.fill(0xffffff)
    buffer = QBuffer()
    buffer.open(QIODevice.WriteOnly)
    assert image.save(buffer, 'PNG')
    raw = bytes(buffer.data())
    return hashlib.sha256(raw).hexdigest(), {
        'media_type': 'image/png', 'data': base64.b64encode(raw).decode('ascii')}


@pytest.mark.parametrize('extension', ['json', 'zip', 'cutp'])
def test_roundtrip_with_embedded_image(tmp_path, extension):
    ident, asset = sample_image()
    data = {'last_equation': 'Y = x', 'image_assets': {ident: asset}}
    path = tmp_path / f'project.{extension}'
    write_project(path, data)
    assert read_project(path) == data
    assert 'data' in asset  # Saving must not mutate the in-memory project.
    if extension != 'json':
        with zipfile.ZipFile(path) as archive:
            assert f'images/{ident}.png' in archive.namelist()
            assert 'data' not in json.loads(archive.read('project.json'))['image_assets'][ident]


def test_archive_replace_failure_preserves_original(tmp_path, monkeypatch):
    path = tmp_path / 'project.cutp'
    write_project(path, {'last_equation': 'original'})
    before = path.read_bytes()
    def fail(*args):
        raise OSError('disk failure')
    monkeypatch.setattr('src.utils.project_io.os.replace', fail)
    with pytest.raises(OSError):
        write_project(path, {'last_equation': 'new'})
    assert path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize('fault', ['version', 'missing_image', 'checksum', 'path', 'duplicate', 'oversize'])
def test_invalid_archives_rejected(tmp_path, fault, monkeypatch):
    ident, asset = sample_image()
    path = tmp_path / 'bad.zip'
    metadata = {'image_assets': {ident: {'media_type': 'image/png'}}}
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('manifest.json', json.dumps({
            'format': 'CalibrationUncertaintyTool', 'version': 2 if fault == 'version' else 1}))
        archive.writestr('project.json', json.dumps(metadata))
        if fault != 'missing_image':
            archive.writestr(f'images/{ident}.png', b'wrong' if fault == 'checksum' else base64.b64decode(asset['data']))
        if fault == 'path':
            archive.writestr('../outside.png', b'bad')
        if fault == 'duplicate':
            with pytest.warns(UserWarning):
                archive.writestr('project.json', '{}')
    if fault == 'oversize':
        monkeypatch.setattr('src.utils.project_io.MAX_PROJECT_BYTES', 10)
    with pytest.raises((ValueError, KeyError)):
        read_project(path)
    assert not (tmp_path.parent / 'outside.png').exists()


def test_open_save_recovery_and_reset_preserve_assets(window, tmp_path, monkeypatch):
    ident, asset = sample_image()
    data = window.get_save_data()
    data['image_assets'] = {ident: asset}
    source = tmp_path / 'input.zip'
    write_project(source, data)
    monkeypatch.setattr(QFileDialog, 'getOpenFileName', lambda *a, **k: (str(source), ''))
    monkeypatch.setattr(QMessageBox, 'information', lambda *a: None)
    window.open_file()
    assert window.image_assets == data['image_assets']
    assert window.current_file_path == str(source)
    window.last_equation = 'changed'
    window._recovery_path = tmp_path / 'recovery.cutp'
    window._autosave_recovery()
    assert read_project(window._recovery_path)['image_assets'] == data['image_assets']
    destination = tmp_path / 'saved.cutp'
    window._write_save_data_to_path(destination)
    assert read_project(destination)['image_assets'] == data['image_assets']
    assert not window._check_modified()
    window.new_file()
    assert window.image_assets == {}


def test_corrupt_open_preserves_work(window, tmp_path, monkeypatch):
    path = tmp_path / 'broken.zip'
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('project.json', '{}')
    before = window.get_save_data()
    monkeypatch.setattr(QFileDialog, 'getOpenFileName', lambda *a, **k: (str(path), ''))
    monkeypatch.setattr(QMessageBox, 'critical', lambda *a: None)
    window.open_file()
    assert window.get_save_data() == before
    assert window.current_file_path is None


def test_archive_recovery_restores_images(window, tmp_path, monkeypatch):
    ident, asset = sample_image()
    data = window.get_save_data()
    data['image_assets'] = {ident: asset}
    path = tmp_path / 'recovery-previous.cutp'
    write_project(path, data)
    monkeypatch.setattr(window, 'isVisible', lambda: True)
    monkeypatch.setattr(QMessageBox, 'question', lambda *a: QMessageBox.Yes)
    window._offer_recovery()
    assert window.image_assets == data['image_assets']
    assert window._check_modified()
    assert not path.exists()
    assert read_project(window._recovery_path)['image_assets'] == data['image_assets']
    monkeypatch.setattr(window, 'isVisible', lambda: False)


def test_save_as_defaults_to_cutp(window, tmp_path, monkeypatch):
    path = tmp_path / 'model'
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *a, **k: (str(path), 'Calibration Project (*.cutp)'))
    monkeypatch.setattr(QMessageBox, 'information', lambda *a: None)
    assert window.save_file_as()
    assert window.current_file_path == str(path) + '.cutp'
    assert read_project(window.current_file_path) == window.get_save_data()
