import re

from PySide6.QtCore import QMimeData, QUrl
from PySide6.QtGui import QImage, QTextDocument
from PySide6.QtWidgets import QInputDialog, QFileDialog

from src.utils.image_assets import import_image, embed_report_images
from src.utils.markdown_renderer import render_markdown_to_html
from src.utils.project_io import read_project
from tests.test_project_safety import window


def picture():
    image = QImage(100, 60, QImage.Format_RGB32)
    image.fill(0x44aacc)
    return image


def test_paste_save_reload_and_render(window, tmp_path, monkeypatch):
    project = {'variables':['Y','x'],'result_variables':['Y'],'last_equation':'Y = x',
        'value_names':['P1'],'value_count':1,'variable_values':{
            'Y':{'type':'result','unit':'V','values':[{}]},
            'x':{'type':'fixed','unit':'V','definition':'共通説明','values':[{'central_value':'1','description':'点の説明'}]}}}
    assert window.load_data(project,show_message=False)
    handlers = window.variables_tab.handlers
    handlers.current_variable = 'x'
    editor = window.variables_tab.definition_input
    editor.setPlainText('共通説明')
    monkeypatch.setattr(QInputDialog,'getText',lambda *a: ('独自図 [測定配置]','yes'))
    mime = QMimeData(); mime.setImageData(picture())
    assert editor.canInsertFromMimeData(mime)
    editor.insertFromMimeData(mime)
    text = editor.toPlainText()
    assert 'asset:' in text
    assert window.variable_values['x']['definition'] == text
    # Reusing identical pixels stores just one image payload.
    editor.insertFromMimeData(mime)
    assert len(window.image_assets) == 1
    path = tmp_path/'with-image.cutp'
    window._write_save_data_to_path(path)
    assert window.load_data(read_project(path),show_message=False)
    markup = window.report_tab.generate_report_html('Y = x')
    assert 'data:image/png;base64,' in markup
    assert 'src="asset:' not in markup
    assert '独自図 [測定配置]' in markup
    # Images from common definitions must not stretch the variable list table.
    assert not re.search(r'<td[^>]*>[^<]*<p><img src="data:image',markup)
    document = QTextDocument(); document.setHtml(markup)
    urls = re.findall(r'src="(data:image/png;base64,[^"]+)"',markup)
    resource = document.resource(QTextDocument.ImageResource,QUrl(urls[0]))
    assert resource is not None and not resource.isNull()


def test_cancel_paste_leaves_project_unchanged(window, monkeypatch):
    editor = window.variables_tab.definition_input
    before = window.get_save_data()
    monkeypatch.setattr(QInputDialog,'getText',lambda *a: ('',False))
    mime = QMimeData(); mime.setImageData(picture())
    editor.insertFromMimeData(mime)
    assert window.get_save_data() == before


def test_visible_insert_button_opens_file_picker(window, tmp_path, monkeypatch):
    editor = window.variables_tab.definition_input
    window.variables_tab.settings_group.setEnabled(True)
    path = tmp_path / 'figure.png'
    assert picture().save(str(path))
    selections = []
    def choose(*args):
        selections.append(args)
        return str(path), 'Images (*.png *.jpg *.jpeg)'
    monkeypatch.setattr(QFileDialog, 'getOpenFileName', choose)
    monkeypatch.setattr(QInputDialog, 'getText', lambda *a: ('測定図', True))
    editor.resize(400,100)
    assert not editor.insert_image_button.isHidden()
    assert editor.insert_image_button.geometry().bottom() < editor.viewportMargins().top()
    editor.insert_image_button.click()
    assert len(selections) == 1
    assert '![測定図](asset:' in editor.toPlainText()
    assert len(window.image_assets) == 1


def test_missing_asset_is_visible_and_caption_is_escaped(window):
    ident = 'a'*64
    missing = embed_report_images(render_markdown_to_html(f'![図](asset:{ident})'),{})
    assert '添付画像が見つかりません' in missing
    assets = {}
    ident = import_image(assets,picture())
    caption = '&lt;script&gt; &quot;証明書&quot;'
    markup = embed_report_images(f'<img alt="{caption}" src="asset:{ident}" />',assets)
    assert '<script>' not in markup
    assert caption in markup
