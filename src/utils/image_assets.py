"""Portable image references shared by text editors and reports."""
from src.utils.ui_translation import tr_ui
import base64
import hashlib
import html
import re

from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QImage


def import_image(assets, image):
    if image.isNull():
        raise ValueError(tr_ui('画像を読み込めません。'))
    if image.width() * image.height() > 40_000_000:
        raise ValueError(tr_ui('画像が大きすぎます（最大4000万画素）。'))
    buffer = QBuffer()
    buffer.open(QIODevice.WriteOnly)
    if not image.save(buffer, 'PNG'):
        raise ValueError(tr_ui('画像を保存できません。'))
    raw = bytes(buffer.data())
    ident = hashlib.sha256(raw).hexdigest()
    assets[ident] = {'media_type': 'image/png', 'data': base64.b64encode(raw).decode('ascii')}
    return ident


def embed_report_images(markup, assets):
    """Resolve only internal image URLs; exported HTML needs no sidecar files."""
    def replace(match):
        ident = match.group(2)
        asset = assets.get(ident)
        if not asset:
            return tr_ui('<span>[添付画像が見つかりません：') + html.escape(ident) + ']</span>'
        raw = base64.b64decode(asset['data'], validate=True)
        image = QImage.fromData(raw)
        if image.isNull():
            return tr_ui('<span>[添付画像を読み込めません]</span>')
        width = min(640, image.width())
        height = round(image.height() * width / image.width())
        alt_match = re.search(r'\balt="([^"]*)"', match.group(0))
        alt = alt_match.group(1) if alt_match else ''
        url = 'data:' + asset['media_type'] + ';base64,' + asset['data']
        return (f'<img src="{url}" alt="{alt}" width="{width}" height="{height}" '
                f'style="max-width:100%;height:auto" /><br/><small>{alt}</small>')
    return re.sub(r'<img\b[^>]*\bsrc=([\"\'])asset:([0-9a-f]{64})\1[^>]*>', replace, markup)
