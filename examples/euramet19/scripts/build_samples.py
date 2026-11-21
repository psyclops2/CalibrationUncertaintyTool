"""Rebuild two image-bearing cg-19 models and verify with independent derivatives."""
from pathlib import Path
import base64
import copy
from decimal import Decimal
import html
import json
import math
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QPainter, QPen, QColor, QFont, QTextDocument, QPainterPath
from PySide6.QtCore import Qt, QRectF, QUrl
from src.main_window import MainWindow
from examples.current_format import current_format
from src.utils.image_assets import import_image
from src.utils.project_io import read_project, write_project
from examples.sample_presentation import enrich_project, ensure_sample_fonts
from src.utils.language_manager import LanguageManager

BASE = Path(__file__).resolve().parents[1]
SOURCE = 'https://www.euramet.org/Media/docs/Publications/calguides/I-CAL-GUI-019_Calibration_Guide_No._19_web.pdf'
FORMULA = 'V20 = m/(rhoW-rhoA)*(1-rhoA/rhoB)*(1-gamma*(t-tref))+dMen+dRep'


def diagram(kind):
    image = QImage(1100, 640, QImage.Format_RGB32)
    image.fill(QColor('#ffffff'))
    p = QPainter(image)
    p.setRenderHint(QPainter.Antialiasing)
    def text(x, y, w, h, content, size=22, color='#17334c'):
        p.setPen(QColor(color)); p.setFont(QFont('Yu Gothic', size))
        p.drawText(QRectF(x, y, w, h), Qt.TextWordWrap | Qt.AlignVCenter, content)
    def box(x, y, w, h, content):
        p.setPen(QPen(QColor('#6386a3'), 2)); p.setBrush(QColor('#eef5fa'))
        p.drawRoundedRect(QRectF(x, y, w, h), 12, 12)
        text(x+18,y+6,w-36,h-12,content,15)
    text(35,20,1020,65,'重量法による体積校正' if kind=='flow' else 'メニスカス位置と読み取りの不確かさ',28)
    if kind == 'flow':
        box(35,115,300,112,'空容器・満水容器を秤量\nm = I_full − I_empty')
        box(400,115,300,112,'密度・浮力の補正係数\n1 / (ρW − ρA)\n× (1 − ρA / ρB)')
        box(765,115,300,112,'基準温度20 °Cへ換算\n× {1 − γ × (t − 20)}')
        text(343,135,55,65,'→',27); text(708,135,55,65,'→',27)
        box(35,290,470,115,'要因の不確かさを一次伝播\n質量・温度・密度・熱膨張係数')
        box(590,290,475,115,'体積の補正項を加算\nメニスカス dMen ／ 繰返し dRep')
        text(35,443,1030,94,'V20 = m / (ρW − ρA) × (1 − ρA / ρB)\n           × {1 − γ × (t − 20)} + dMen + dRep',23)
        text(35,560,1030,50,'cg-19 式(1)を基にした独自説明図。容器や装置の実物写真ではありません。',15)
    else:
        p.setPen(QPen(QColor('#345878'),5)); p.drawLine(180,130,180,440); p.drawLine(420,130,420,440)
        water = QPainterPath(); water.moveTo(184,282); water.cubicTo(242,360,358,360,416,282)
        water.lineTo(416,436); water.lineTo(184,436); water.closeSubpath()
        p.setBrush(QColor('#c9e8f4')); p.setPen(Qt.NoPen); p.drawPath(water)
        curve = QPainterPath(); curve.moveTo(184,282); curve.cubicTo(242,360,358,360,416,282)
        p.setBrush(Qt.NoBrush); p.setPen(QPen(QColor('#28789b'),4)); p.drawPath(curve)
        p.setPen(QPen(QColor('#d46c33'),3,Qt.DashLine)); p.drawLine(110,340,485,340)
        text(70,450,450,60,'標線とメニスカス下端を合わせる',18)
        box(555,130,500,135,'フラスコ：読み取り範囲 ±0.015 mL\n矩形分布を仮定\nu(dMen) = 0.015 / √3 mL')
        box(555,305,500,125,'ピクノメータ：原文で無視した項\ndMen = 0 mL（不確かさも0）')
        text(555,460,500,82,'ゼロの補正量でも、不確かさはゼロとは限りません。',20)
        text(35,560,1030,50,'cg-19 §7.1.1.7、§7.2.1.7を説明する独自模式図。原図の転載ではありません。',15)
    p.end()
    return image


def make_project(kind):
    flask = kind == 'flask'
    title = '1000 mL メスフラスコ' if flask else '100 mL ピクノメータ'
    section = '7.1' if flask else '7.2'
    # Table 2/4 standard uncertainties, except the rectangular meniscus and gamma
    # components, which are evaluated from their stated bounds using references.
    inputs = {
        'm': ('996.9505' if flask else '99.7500', '0.00127' if flask else '0.000114', 'g', '秤量差（満水−空容器）', '50'),
        't': ('19.11' if flask else '18.94', '0.0152' if flask else '0.017', 'degC', '水と容器の温度', 'inf'),
        'rhoW': ('0.9984', '3.09e-6', 'g/mL', '水密度（表の丸め値）', 'inf'),
        'rhoA': ('0.0012', '1.76e-6' if flask else '1.74e-6', 'g/mL', '空気密度', 'inf'),
        'rhoB': ('8.00', '0.0346', 'g/mL', '基準分銅の密度', 'inf'),
        'gamma': ('1e-5', str(Decimal('5e-7')/Decimal(3).sqrt()), '1/degC', '容器の体膨張係数', 'inf'),
    }
    assets = {}
    flow = import_image(assets, diagram('flow'))
    meniscus = import_image(assets, diagram('meniscus'))
    notes = (
        f'EURAMET cg-19 v4.1 (12/2025), §{section}、式(1)、表'+('2' if flask else '4')+'に基づく独立した試算。\n'
        f'原資料：[EURAMET cg-19]({SOURCE})。入力の中心値と評価済み標準不確かさは表を採用。'
        '元の観測列は掲載されていないため作成しない。Type Aは評価済み要約値を入力。\n'
        '原文同様に入力間の共分散を0と仮定。水密度内の温度成分との共分散は再構成していない。'
        '実務モデルへ転用するときは温度の共通性と相関を再評価すること。\n'
        '包含係数は厳密な95%両側t分位点を有効自由度の下側整数から計算する。原文の「約95%」とは条件が異なる。\n'
        '原文の基準分銅密度uは本文0.03 g/mLと表0.0346 g/mLが不一致。本モデルは表を採用。\n'
        + ('原文の中心値999.628 mLに対し、表の丸め済み密度を式(1)へ入れると約999.609 mL。'
           '熱膨張係数の感度は式(1)から正となるが、表2の寄与は負。原文k=2.15は自由度19のt分布で約95.54%に対応し、厳密な95%とは異なる。'
           if flask else
           '原文の中心値100.014 mLに対し、表の丸め済み密度では約100.016 mL。'
           '有効自由度の原文掲載値13に対し本モデルは約13.295。原文k=2.21は自由度13のt分布で約95.43%に対応し、厳密な95%とは異なる。')
        + '\n画像は本サンプル用の独自説明図であり、EURAMET原図の転載ではない。'
    )
    variables = {'V20': {'type':'result','unit':'mL','definition':'20 °Cでの体積','values':[{
        'coverage':{'method':'student','probability':0.95,'floor_df':True,'note':'95%両側t分位点。原文との係数差は文書説明参照。'}}]}}
    refs = {'version':1,'variables':{},'points':['point1'],'values':{},'rules':{}}
    for name,(central,u,unit,label,df) in inputs.items():
        divisor = str(Decimal(3).sqrt()) if name == 'gamma' else '1'
        bound = '5e-7' if name == 'gamma' else u
        variables[name] = {'type':'B','unit':unit,'definition':label,'distribution':
            'RECTANGULAR_DISTRIBUTION' if name=='gamma' else 'NORMAL_DISTRIBUTION',
            'divisor':divisor,'values':[{'central_value':central,'half_width':bound,
            'divisor':divisor,'standard_uncertainty':u,'degrees_of_freedom':df,
            'description':f'cg-19 §{section}、表の評価済み入力。'+('正規分布の除数1：入力値は標準不確かさ。' if name!='gamma' else 'メーカー値の±5%を矩形分布で評価。')}]}
        if name == 'gamma':
            expression = 'abs(@{variable:gamma:central_value:current})*0.05'
        else:
            ident = 'u-'+name
            refs['values'][ident] = {'name':label+'：標準不確かさ','scope':'common','unit':unit,'expression':u,'description':'cg-19 表の評価済み値'}
            expression = '@{value:'+ident+'}'
        refs['rules'][name] = {'expression':expression,'overrides':{}}
    variables['m']['definition'] += f'\n![重量法の計算手順：本サンプル独自作図](asset:{flow})'
    men_bound = '0.015' if flask else '0'
    variables['dMen'] = {'type':'B','unit':'mL','definition':'メニスカス位置の補正量',
        'distribution':'RECTANGULAR_DISTRIBUTION','divisor':str(Decimal(3).sqrt()),'values':[{
        'central_value':'0','half_width':men_bound,'divisor':str(Decimal(3).sqrt()),
        'standard_uncertainty':str(Decimal(men_bound)/Decimal(3).sqrt()),'degrees_of_freedom':'inf',
        'description':f'cg-19 §{section}.1.7。補正量とその不確かさを区別する。\n![メニスカスの読み取り：本サンプル独自作図](asset:{meniscus})'}]}
    refs['values']['men-bound']={'name':'メニスカス半値幅','scope':'common','unit':'mL','expression':men_bound}
    refs['rules']['dMen']={'expression':'@{value:men-bound}','overrides':{}}
    variables['dRep']={'type':'A','unit':'mL','definition':'繰返しによる平均体積の不確かさ','values':[{
        'evaluation_mode':'summary','central_value':'0','standard_uncertainty':'0.014' if flask else '0.0008',
        'degrees_of_freedom':'9','evaluation_note':'n=10。原文の表に掲載された平均の標準不確かさ（丸め済み）。',
        'description':f'cg-19 §{section}.1.9。平均の不確かさを採用。観測値は生成していない。'}]}
    variables['tref']={'type':'fixed','unit':'degC','definition':'基準温度','values':[{'central_value':'20','description':'20 °C'}]}
    refs['variables']={name:name for name in variables}
    return {'document_info':{'document_number':'EURAMET19-'+kind,'document_name':title+'（画像付き）',
        'version_info':'cg-19 v4.1 / sample 1','description_markdown':notes,'revision_history':''},
        'last_equation':FORMULA,'variables':list(variables),'result_variables':['V20'],
        'value_names':[title],'value_count':1,'current_value_index':0,'variable_values':variables,
        'correlation_coefficients':{},'regressions':{},'value_references':refs,'image_assets':assets}


def independent_check(project):
    values = project['variable_values']
    x = {name:float(info['values'][0]['central_value']) for name,info in values.items() if name != 'V20'}
    m,w,a,b,g,t,t0 = (x[name] for name in ('m','rhoW','rhoA','rhoB','gamma','t','tref'))
    c = 1-g*(t-t0)
    v = m/(w-a)*(1-a/b)*c
    sensitivities = {'m':v/m, 't':-m/(w-a)*(1-a/b)*g,
        'rhoW':-v/(w-a), 'rhoA':v*(1/(w-a)-1/(b-a)),
        'rhoB':m/(w-a)*c*a/b**2, 'gamma':-m/(w-a)*(1-a/b)*(t-t0), 'dMen':1, 'dRep':1}
    contributions = {name:derivative*float(values[name]['values'][0]['standard_uncertainty']) for name,derivative in sensitivities.items()}
    u = math.sqrt(sum(contribution**2 for contribution in contributions.values()))
    denominator = sum(contribution**4/float(values[name]['values'][0]['degrees_of_freedom']) for name,contribution in contributions.items())
    return {'central':v,'u':u,'df':u**4/denominator,'sensitivities':sensitivities}


def main():
    app = QApplication.instance() or QApplication([])
    ensure_sample_fonts()
    lang = LanguageManager(); lang.current_language = 'ja'; lang.load_language()
    MainWindow._offer_recovery = lambda self: None
    window = MainWindow(lang)
    window._change_timer.stop(); window._recovery_timer.stop()
    records = []
    try:
        for kind in ('flask','pycnometer'):
            project = make_project(kind)
            enrich_project(project, 'euramet19', kind)
            assert window.load_data(current_format(project),show_message=False)
            tab = window.uncertainty_calculation_tab
            tab.on_result_changed('V20')
            assert not tab.warning_label.text(), tab.warning_label.text()
            expected = independent_check(window.get_save_data())
            result = copy.deepcopy(window.calculation_results['V20'][window.value_names[0]])
            assert math.isclose(result['result_central_value'],expected['central'],rel_tol=1e-12)
            assert math.isclose(result['result_standard_uncertainty'],expected['u'],rel_tol=1e-10)
            assert math.isclose(result['effective_df'],expected['df'],rel_tol=1e-10)
            path = BASE/'projects'/f'{kind}.cutp'
            window._write_save_data_to_path(path)
            assert window.load_data(read_project(path),show_message=False)
            tab.on_result_changed('V20')
            assert window.calculation_results['V20'][window.value_names[0]] == result
            window.report_tab.result_combo.setCurrentText('V20')
            report = window.report_tab.generate_report_html(FORMULA)
            assert report.count('data:image/png;base64,') >= 2
            assert 'src="asset:' not in report
            (BASE/'reports'/f'{kind}.html').write_text(report,encoding='utf-8')
            records.append({'case':kind,'independent':expected,'tool':result,'save_reload':True})
            print(kind, {key:result[key] for key in ('result_central_value','result_standard_uncertainty','effective_df','coverage_factor','expanded_uncertainty')}, flush=True)
        (BASE/'reports'/'verification.json').write_text(json.dumps(records,indent=2,ensure_ascii=False,default=str),encoding='utf-8')
        diagram('flow').save(str(ROOT/'tmp'/'euramet-flow-preview.png'))
        diagram('meniscus').save(str(ROOT/'tmp'/'euramet-meniscus-preview.png'))
        document = QTextDocument()
        document.setHtml(report); document.setTextWidth(950)
        block = document.begin()
        positions = []
        while block.isValid():
            fragment = block.begin()
            while not fragment.atEnd():
                fmt = fragment.fragment().charFormat()
                if fmt.isImageFormat():
                    url = fmt.toImageFormat().name()
                    resource = document.resource(QTextDocument.ImageResource, QUrl(url))
                    assert resource is not None and not resource.isNull(), 'Report image did not load in Qt'
                    positions.append(document.documentLayout().blockBoundingRect(block).top())
                fragment += 1
            block = block.next()
        assert len(positions) >= 2
        for i, y in enumerate(positions):
            preview = QImage(960,640,QImage.Format_RGB32); preview.fill(QColor('white'))
            painter=QPainter(preview); painter.translate(0,-max(0,y-35))
            document.drawContents(painter); painter.end()
            preview.save(str(ROOT/'tmp'/f'euramet-report-image-{i+1}.png'))
    finally:
        window.hide(); window.close()


if __name__ == '__main__':
    main()
