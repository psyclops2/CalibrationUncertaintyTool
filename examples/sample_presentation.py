"""Reader-facing explanations and original diagrams for generated samples.

Only presentation fields are changed. Input values, equations, sources and
evaluation settings remain owned by the numerical sample generators.
"""
import copy
import re
from pathlib import Path
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QImage, QPainter, QPen, QColor, QFont, QFontDatabase, QPolygonF
from src.utils.image_assets import import_image


def ensure_sample_fonts():
    """The offscreen Qt plugin does not enumerate Windows system fonts."""
    if 'Yu Gothic' not in QFontDatabase.families():
        for name in ('YuGothR.ttc','YuGothB.ttc'):
            path=Path('C:/Windows/Fonts')/name
            if path.is_file():QFontDatabase.addApplicationFont(str(path))
    if not any(QFontDatabase.writingSystems(family) and QFontDatabase.Japanese in QFontDatabase.writingSystems(family)
               for family in QFontDatabase.families()):
        raise RuntimeError('Japanese fonts are required to render sample diagrams.')


# Measurement overview, model interpretation, conditions, diagram steps.
CASES = {
'S2': (
 '10 kgの分銅を、校正済みの標準分銅と質量比較器で比較します。置換測定で得た質量差を標準分銅の値に加え、被校正分銅の協定質量を求めます。',
 'msに質量差diffと各補正を加えます。補正の中心値が0でも、その許容範囲は不確かさへ寄与します。diffには3組の実観測と、過去に評価したプール標準偏差25 mgを使います。',
 'プール標準偏差など、原文に自由度が示されない項は無限大と仮定しています。',
 ['標準分銅\n校正値と証明書','置換測定\n標準と被校正分銅を比較','質量差と補正\n繰返し・ドリフト・浮力','協定質量\n値と合成不確かさ']),
'S3': (
 '10 kΩの標準抵抗を参照抵抗と比較し、電圧計で測った比から抵抗値を求めます。参照抵抗の校正後の変化と、両抵抗の温度による補正を考慮します。',
 '参照抵抗rsにドリフトと温度補正を加え、観測比ratioと比の補正係数rcを掛け、被校正抵抗の温度補正を引きます。rcは1を中心とする乗算量です。',
 '数値はΩに統一しています。比の補正係数に三角分布を採用する原文の条件を引き継いでいます。',
 ['参照抵抗\n校正値・ドリフト','電圧比の観測\n5回の比較','比と温度の補正\nrcは乗算係数','被校正抵抗\nΩで評価']),
'S4': (
 '公称50 mmのゲージブロックを、同じ公称長さの標準ブロックと比較します。比較器の長さ差に、校正・ドリフト・温度・測定位置の補正を加えます。',
 '熱補正は平均膨張係数×ブロック間温度差と、膨張係数差×平均温度偏差の二つです。後者は両入力の中心値が0のため、一次感度から求める寄与は0になります。',
 '本モデルは原式の一次評価です。原典に含まれる積の高次寄与を自動加算しません。観測列には事前標準偏差12 nmを使用します。',
 ['標準ブロック\n校正値とドリフト','比較器\n5回の長さ差','温度と接触位置\n二つの熱補正項','基準温度での長さ\n一次近似で評価']),
'S5_temperature': (
 '1000 °Cの炉内で、被校正N熱電対の近くに置いたR熱電対を用いて炉温を評価します。参照熱電対の換算済み温度に、電圧測定と温度の補正を加えます。',
 '電圧補正にはcsを掛けてKへ換算します。基準接点の温度補正には−cs/cs0を掛けます。tsは前処理済み温度と標準不確かさの要約値です。',
 '証明書の温度・電圧換算関数は原文にないため、換算済み温度と局所感度を使用します。起電力段階とは別モデルで、変更は自動転送されません。',
 ['R熱電対\n炉内の参照温度','電圧測定\n電圧計と切替器','温度補正\n校正・基準接点・炉の均一性','炉温\n起電力段階へ渡す値']),
'S5_emf': (
 'N熱電対の観測起電力を、校正点1000 °Cに対応する値へ換算します。電圧計・切替器・補償導線の補正と、炉温偏差・基準接点の補正を加えます。',
 'tempDeviationは校正点温度−炉温として−0.5 Kを採用します。cxで割ると起電力補正は約−19.23 µVになります。炉温の標準不確かさ0.641 Kは前段階の評価済み値です。',
 '原文の定義と最終値に合わせた符号です。提供されたWorkbench例は逆向きの温度差を採用します。炉温uは手動転記で、段階間の共通要因の相関は接続していません。',
 ['N熱電対\n観測起電力','電圧測定の補正\n電圧計・切替器・導線','校正点への換算\n温度差÷感度','1000 °Cの起電力\nVで評価']),
'S6': (
 '18 GHzのRFパワーセンサを、校正済み参照センサとの置換で校正します。参照周波数50 MHzと校正周波数18 GHzの電力比を使って校正係数を求めます。',
 'ksとdriftの和に、四つのミスマッチ係数、電力計補正、観測比を掛けます。ミスマッチ半値幅は、再利用する参照値にある反射係数の積の2倍です。位相不明の条件をU字分布で表します。',
 '原文の反射係数表と報告結果に従い18 GHzを採用します。Workbenchとの小さな差を比べる際は、入力自由度と表示丸めの条件も揃えます。',
 ['参照・被校正センサ\n同じ伝送標準で置換','50 MHz／18 GHz\n電力比を観測','反射係数から評価\n四つのミスマッチ','被校正センサ\n校正係数K']),
'S7': (
 '同軸ステップ減衰器の0 dBと30 dBの設定差を、校正済み減衰器を含む測定系で比較します。電気的な不整合、漏れ、表示・零位検出器の分解能を考慮します。',
 '観測減衰量lossに各補正を加えます。0 dB側の表示・零位補正は引き、30 dB側は加えます。ミスマッチは反射係数と散乱係数から標準不確かさを計算し、U字分布の半値幅へ換算して入力します。',
 '参照式は途中で丸めず評価します。Workbench例の半値幅0.0283 dBは、丸めたu=0.020 dBからの換算値と整合します。dBはこのモデルの数値定義で扱います。',
 ['減衰器\n0 dBと30 dBを切替','比較測定\n4回の設定差','ミスマッチと漏れ\n反射・散乱係数から評価','増分減衰量\ndBで評価']),
'S9': (
 '校正器を100 Vに設定してデジタル電圧計を校正し、指示値−校正器出力から指示誤差を求めます。電圧計の分解能と校正器の仕様を別の補正として扱います。',
 '校正器仕様の半値幅は|Vs|×100×10⁻⁶+0.001 Vです。100 ppmは設定値に対する係数で、レンジ上限への係数ではありません。証明書の拡張不確かさと仕様幅は別に入力します。',
 '仕様の適用条件は18〜23 °C、電源210〜250 V、負荷100 kΩ超、校正後1年以内です。k=1.65は原文の支配的矩形分布近似に基づく指定値です。',
 ['校正器\n100 Vを設定','デジタル電圧計\n指示100.1 V','証明書・仕様・分解能\n参照式で幅を計算','指示誤差\n指示−出力']),
'S10': (
 '150 mmのノギスを鋼製ゲージブロックで校正します。指示値と標準長さとの差に、温度差・表示分解能・機械的影響の補正を加えます。',
 '温度差による長さ補正はlength×alpha×deltaTです。resolutionとmechanicalは0を中心とする加算補正で、幅が合成不確かさへ寄与します。',
 '数値はmで入力します。k=1.83は原文の非正規出力分布に基づく指定で、自動t分布計算ではありません。',
 ['ゲージブロック\n参照長さ150 mm','ノギス\n指示値を読む','温度と器差要因\n分解能・機械的影響','指示誤差\nmで評価']),
'S11': (
 '180 °Cの温度校正ブロックを参照温度計で評価します。温度計の校正・読取りに加え、ブロック内の位置差と時間変動を考慮します。',
 '標準温度に各補正を加えます。radialとaxialは位置による差、instabilityは時間変動、hysteresisは温度履歴に伴う補正です。中心値0の幅も寄与に含まれます。',
 'k=1.81は原文の出力分布に基づく指定値です。手動kを維持したまま入力を大きく変更した場合は、係数の根拠も見直します。',
 ['温度校正ブロック\n180 °C','参照温度計\n温度を観測','位置と時間の変動\n軸方向・径方向・履歴','ブロック温度\n値と不確かさ']),
'S12_staged': (
 '水道メーターを体積標準で校正します。標準器の体積を水温と圧力の条件に換算し、その通過体積とメーター指示から単回の相対指示誤差を求めます。',
 '最初の式で体積vxを評価し、次の式でex=(指示体積+終点補正−始点補正)/vx−1を計算します。途中のvxを元の入力へ展開するため、丸めたuを転記せず伝播します。',
 '圧力はkPa、圧縮率は1/kPaで揃えています。単位の自動換算は行いません。平均誤差のモデルとは別の評価段階です。',
 ['体積標準\n標準体積と首部読取り','温度・圧力換算\n水と標準器の特性','通過体積vx\n同じモデルの中間量','メーター指示と比較\n相対誤差ex']),
'S12_average': (
 '同じ流量で行った水道メーターの3回の試験から、平均相対指示誤差を評価します。単回の評価に共通する不確かさと、試験間のばらつきを分けて扱います。',
 '平均誤差の代表値singleに、平均0の繰返し補正repeatを加えます。repeatは3観測から平均のuを求めます。singleのu=0.00068は共通成分としてそのまま使用し、√3で割りません。',
 'EA表方式では自由度を下側へ切り捨てた掲載係数を使います。別ファイルの数値t分位点方式とは包含係数の丸めが異なります。',
 ['同一流量で3試験\n相対誤差を観測','試験間の繰返し\n平均0の補正を評価','単回評価の共通u\n√3で割らず保持','平均相対誤差\nu・有効自由度・k']),
'S13': (
 '40 mmの設定リングで比較器を零合わせし、公称90 mmのリングゲージを測定します。5か所の読取りから径差を求め、比較器・温度・測定幾何の補正を加えます。',
 'standardとdifferenceから直径を求め、零合わせの不確かさはzeroingで別に加えます。熱補正では標準リング・被校正リング・比較器スケールに共通する周囲温度を一つの量として扱います。',
 '原式を一次近似で評価します。温度の高次寄与は加算していません。中心値には原観測の平均と本文の非同軸補正符号を採用しています。',
 ['40 mm設定リング\n比較器を零合わせ','90 mmリング\n5位置の径差','周囲温度と各部温度\nリング2個・比較器スケール','基準温度の直径\n幾何補正も加算']),
'H1': (
 'ゲージブロックを標準ブロックと比較し、校正証明書・比較器・熱膨張の影響を含めて長さを評価します。GUM附属書H.1の一次評価を扱います。',
 'theta=meanT+cycleTで温度偏差を作り、標準長さと長さ差から熱補正を差し引きます。校正値・比較器の成分には原文の個別の包含係数と自由度を使用します。',
 '原文H.1.7の高次補正は加算していません。標準不確かさ約31.66 nmは原典の一次値32 nmに対応し、高次補正後34 nmとは評価範囲が異なります。',
 ['標準ブロック\n証明書と自由度','長さ差\n比較器の評価済み統計量','平均温度と温度変動\n中間量theta','長さl\n99%の包含設定']),
'H2': (
 '電圧・電流・位相を同時に5組観測し、抵抗R、リアクタンスX、インピーダンスZを求めます。同じ観測組に由来する入力相関を保持して計算します。',
 '手法1は入力の平均から三つの量を計算します。手法2は測定表の各行でR・X・Zを計算してから平均します。位相はradで入力し、電流はAに換算済みです。',
 '同時観測の組を保って編集します。入力量ごとに別々に並べ替えると観測の対応が変わります。二つの手法は厳密には同一結果になりません。',
 ['同時観測5組\n電圧・電流・位相','組を保持した測定表\n平均と共分散','R・X・Zの式\n平均と変換の順序を比較','三つの結果\n出力間相関も評価']),
'H3': (
 '温度計の校正温度と補正値11組から直線回帰を求め、30 °Cにおける補正値とその標準不確かさを評価します。',
 '回帰のxは温度−20 °Cなので、30 °Cはx=10 Kです。predictionには回帰の平均応答を接続し、その値・u・残差自由度9を結果correctionへ伝播します。',
 '30 °Cは観測した校正範囲の外側です。平均応答の不確かさを評価しており、新しい単回観測の予測区間ではありません。xの不確かさは0としています。',
 ['温度計の校正\n温度と補正11組','直線回帰\nx=温度−20 °C','x=10 Kで評価\n30 °Cへの外挿','温度補正\n平均応答のu・自由度9']),
'H4': (
 '放射能濃度の標準試料、ブランク、未知試料を6サイクル測定します。背景計数を差し引いて放射壊変を補正し、標準と未知試料の計数率比から濃度を求めます。',
 '測定表の派生列で補正計数率と比を求めます。手法1は二つの平均計数率の比、手法2はサイクルごとの比の平均を使用します。標準濃度と両試料の質量も式に含めます。',
 '観測列に含まれる計数の変動へ、同じPoisson変動を重ねて加えません。時刻はmin、計数率は1/minで揃え、比を取ります。',
 ['標準・ブランク・試料\n6サイクルの計数','背景差引き・壊変補正\n各サイクルの派生列','標準と試料の比\n平均の順序を比較','放射能濃度Ax\n質量比を含めBq/kgで評価']),
'H5': (
 'ツェナー電圧標準の日ごとの平均値10個から、全体の平均電圧と日間変動を含む標準不確かさを評価します。',
 'dailyMeanは測定表の日平均列に接続します。10個の日平均の標本標準偏差を√10で割り、全体平均のuと自由度9を求めます。',
 '原典の分散分析、日内・日間分散の推定、F検定は実行していません。入力は原文の10個の日平均です。',
 ['日内の電圧測定\n原典で日平均を評価','10日の日平均\n測定表へ入力','日平均間の変動\n平均の標準不確かさ','電圧標準の平均\n自由度9']),
'H6': (
 'ロックウェルC硬さを、平均圧入深さと校正機・標準機・基準片に関する補正から評価します。長さで表す硬さhを、尺度の長さで割ってHRC指数に換算します。',
 '尺度1単位は2 µmです。h=100×scale−補正後の深さ、HRC=h/scaleと定義します。分解能と基準片の不均一さの半値幅には、尺度や深さを参照する式を使います。',
 '深さと機械間補正は評価済み統計量です。原文にない観測列は作成していません。未提示の自由度は無限大と仮定します。',
 ['圧入深さ\n5回測定の要約値','校正機と標準機\n機械間補正','基準片・分解能\n尺度と深さを参照','硬さh → HRC\n2 µmの尺度で換算']),
}

# Per-case meanings take precedence over shared names such as drift and ratio.
MEANINGS = {
'S2':'ms=参照分銅の協定質量|drift=参照分銅の校正後のドリフト補正|diff=被校正分銅と参照分銅の観測質量差|comparator=比較器の偏置・磁気影響の補正|buoyancy=両分銅の空気浮力差の補正',
'S3':'rs=参照抵抗の校正値|drift=参照抵抗の校正後のドリフト補正|thermalS=参照抵抗の温度補正|thermalX=被校正抵抗の温度補正|ratio=比較で観測した電圧比|rc=電圧比に掛ける補正係数',
'S4':'ls=標準ゲージブロックの校正長さ|drift=標準ブロックの経時変化の補正|diff=被校正ブロックと標準ブロックの長さ差|comparator=比較器の非直線性・オフセット補正|length=両ブロックの公称長さ|alpha=両ブロックの平均線膨張係数|deltaT=両ブロックの温度差|variation=中央からの接触位置ずれの補正|deltaAlpha=両ブロックの線膨張係数の差|meanT=平均温度の基準温度からの偏差',
'S5_temperature':'ts=参照熱電対から換算した炉温|vcal=電圧計の校正補正|vres=電圧計の有限分解能による補正|switch=切替器の寄生熱起電力補正|cold=参照熱電対の基準接点温度補正|cert=参照熱電対の校正による温度補正|drift=参照熱電対の経時変化による補正|furnace=炉内の温度不均一による補正|cs=炉温付近の温度対電圧感度|cs0=基準接点付近の温度対電圧感度',
'S5_emf':'vobs=被校正熱電対の観測起電力|vcal=電圧計の校正補正|vres=電圧計の有限分解能による補正|switch=切替器の寄生熱起電力補正|cable=補償導線の起電力補正|tempDeviation=校正点温度から炉温を引いた温度差|cold=被校正熱電対の基準接点温度補正|cx=校正点付近の温度対電圧感度|cx0=基準接点付近の温度対電圧感度',
'S6':'ks=参照パワーセンサの校正係数|drift=参照センサの校正係数のドリフト補正|msr=参照センサの50 MHzでのミスマッチ係数|msc=参照センサの18 GHzでのミスマッチ係数|mxr=被校正センサの50 MHzでのミスマッチ係数|mxc=被校正センサの18 GHzでのミスマッチ係数|pcr=参照周波数の電力計補正係数|pcc=校正周波数の電力計補正係数|ratio=再接続を含む3回の観測電力比',
'S7':'loss=0 dBと30 dBの設定間の観測減衰量|cert=参照減衰器の校正補正|drift=参照減衰器のドリフト補正|mismatch=測定系と減衰器のミスマッチ補正|leak=入出力間の漏れ信号による補正|resA=0 dB側の参照検出器の分解能補正|resB=30 dB側の参照検出器の分解能補正|nullA=0 dB側の零位検出器の補正|nullB=30 dB側の零位検出器の補正',
'S9':'Vix=被校正電圧計の指示値|Vs=校正器の出力値と証明書の不確かさ|dVix=被校正電圧計の表示分解能補正|dVs=校正器の仕様による出力補正',
'S10':'indication=ノギスの指示値|standard=ゲージブロックの参照長さ|length=温度補正に使用する公称長さ|alpha=鋼の線膨張係数|deltaT=ノギスと標準の温度差|resolution=ノギスの表示分解能補正|mechanical=測定面等の機械的影響による補正',
'S11':'standard=参照温度計による温度|resistance=参照温度計の抵抗読取りの補正|drift=参照系の経時変化の補正|resolution=温度表示の分解能補正|radial=径方向の温度分布による補正|axial=軸方向の温度分布による補正|hysteresis=昇温・降温履歴による補正|instability=測定中の温度変動による補正',
'S12_staged':'volume=体積標準の校正体積|neck=体積標準の首部読取りの補正|alphaS=体積標準の体膨張係数|ts=体積標準内の水温|t0=体積標準の基準温度|alphaW=水の体膨張係数|tx=水道メーター内の水温|compressibility=水の圧縮率|px=メーター側の圧力|ps=体積標準側の圧力|indication=メーターの指示体積|resStart=始点での表示分解能補正|resEnd=終点での表示分解能補正',
'S12_average':'repeat=試験間の繰返しによる平均誤差の補正|single=平均誤差の代表値と単回評価の共通不確かさ',
'S13':'standard=設定リングの校正直径|difference=被校正リングと設定リングの観測径差|zeroing=比較器の零合わせによる補正|comparator=比較器の残留指示誤差補正|coaxial=プローブの非同軸による補正|elastic=接触による弾性変形差の補正|abbe=比較器のアッベ誤差差分の補正|ds=設定リングの公称直径|dxnom=被校正リングの公称直径|alphaS=設定リングの線膨張係数|alphaX=被校正リングの線膨張係数|alphaR=比較器スケールの線膨張係数|ambient=周囲温度の基準温度からの偏差|tempS=設定リングの周囲温度からの温度差|tempX=被校正リングの周囲温度からの温度差|tempR=比較器スケールの周囲温度からの温度差',
'H1':'ls=標準ブロックの校正長さ|difference=評価済みの平均長さ差|random=比較器校正の偶然成分の補正|systematic=比較器校正の系統成分の補正|alpha=熱補正に使用する線膨張係数|meanT=平均温度の基準温度からの偏差|cycleT=温度周期変動による偏差|deltaAlpha=二つのブロックの線膨張係数差|deltaT=二つのブロックの温度差',
'H2':'voltage=同時観測した交流電圧|current=同時観測した交流電流|phase=電圧と電流の位相差（rad）|rObs=各観測組から計算した抵抗|xObs=各観測組から計算したリアクタンス|zObs=各観測組から計算したインピーダンス',
'H3':'prediction=回帰から予測した30 °Cでの温度補正',
'H4':'activity=標準試料の基準時刻での放射能濃度|massStandard=標準溶液の質量|massSample=未知試料の質量|rateSample=背景・壊変補正後の未知試料の計数率|rateStandard=背景・壊変補正後の標準試料の計数率|ratio=各サイクルの補正計数率比',
'H5':'dailyMean=10日間の日平均電圧',
'H6':'scale=ロックウェルC尺度1単位に相当する長さ|depth=5回測定の平均圧入深さ|resolution=深さ表示の分解能補正|standardCorrection=標準機の平均圧入深さに関する補正成分|calibrationCorrection=校正機の平均圧入深さに関する補正成分|heterogeneity=基準片の硬さの不均一による補正|national=国家標準機と硬さの定義に伴う補正',
'volume':'m=満水時と空容器の秤量差|t=水と容器の温度|rhoW=校正温度での水密度|rhoA=測定時の空気密度|rhoB=基準分銅の密度|gamma=容器の体膨張係数|dMen=メニスカス位置の補正|dRep=繰返し測定による平均体積の補正|tref=体積を表示する基準温度',
}


def case_id(area, key):
    if area == 'euramet19': return 'volume'
    if key.startswith('S4'): return 'S4'
    if key.startswith('S13'): return 'S13'
    if key == 'S12_probability': return 'S12_average'
    if key.startswith('H2'): return 'H2'
    if key.startswith('H4'): return 'H4'
    return key


def flow_image(title, steps):
    image = QImage(1200, 650, QImage.Format_RGB32); image.fill(QColor('#f7fafc'))
    p = QPainter(image); p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QColor('#18384e')); p.setFont(QFont('Yu Gothic', 22, QFont.Bold))
    p.drawText(QRectF(35, 15, 1130, 80), Qt.AlignCenter|Qt.TextWordWrap, title)
    rects = [QRectF(45,110,500,150),QRectF(655,110,500,150),QRectF(655,365,500,150),QRectF(45,365,500,150)]
    for i,rect in enumerate(rects):
        p.setBrush(QColor('white'));p.setPen(QPen(QColor('#427a98'),3));p.drawRoundedRect(rect,15,15)
        p.setPen(QColor('#18384e'));p.setFont(QFont('Yu Gothic',19))
        p.drawText(rect.adjusted(20,12,-20,-12),Qt.AlignCenter|Qt.TextWordWrap,f'{i+1}. '+steps[i])
    for start,end in [(QPointF(555,185),QPointF(640,185)),(QPointF(905,275),QPointF(905,345)),(QPointF(640,440),QPointF(560,440))]:
        p.setPen(QPen(QColor('#427a98'),5));p.drawLine(start,end)
        direction=end-start
        size=(direction.x()**2+direction.y()**2)**.5;ux,uy=direction.x()/size,direction.y()/size
        p.setBrush(QColor('#427a98'));p.drawPolygon(QPolygonF([end,QPointF(end.x()-18*ux+9*uy,end.y()-18*uy-9*ux),QPointF(end.x()-18*ux-9*uy,end.y()-18*uy+9*ux)]))
    p.setPen(QColor('#425766'));p.setFont(QFont('Yu Gothic',13))
    p.drawText(QRectF(45,550,1110,70),Qt.AlignCenter|Qt.TextWordWrap,'矢印は測定・評価の順序を示します（配線図ではありません）。\n本プロジェクトの独自作図。原資料の図版の転載ではありません。')
    p.end();return image


def describe_evaluation(info, value):
    unit=info.get('unit','1')
    if info['type']=='fixed':
        return f'固定量として使用します。入力単位は{unit}です。この量の不確かさは伝播に含めません。'
    if value.get('input_source'):
        source=value['input_source']
        if source['kind']=='table':
            return f'測定表の列「{source["column"]}」の平均へ接続します。表の有効な観測組から平均のuと自由度を計算し、同じ表の別の接続量との共分散も伝播します。入力単位は{unit}です。'
        return f'回帰の平均応答へ接続します。評価位置での予測値・u・残差自由度を使用します。出力単位は{unit}です。'
    if info['type']=='A':
        mode=value.get('evaluation_mode','sample')
        if mode=='sample':return f'観測列から算術平均と平均の標準不確かさ（標本標準偏差÷√観測数）を計算します。自由度は観測数−1です。観測値の単位は{unit}です。'
        if mode=='pooled':return f'観測列の平均に、事前に評価したプール標準偏差÷√観測数を組み合わせます。保存したプール自由度を使用します。観測値の単位は{unit}です。'
        return f'原資料の評価済み中心値・標準不確かさ・自由度を要約値として入力します。単位は{unit}です。架空の繰返し観測は追加していません。'
    distribution={'NORMAL_DISTRIBUTION':'正規分布','RECTANGULAR_DISTRIBUTION':'矩形分布','TRIANGULAR_DISTRIBUTION':'三角分布','U_DISTRIBUTION':'U字分布'}[info['distribution']]
    divisor=value.get('divisor',info.get('divisor'))
    divisor_label={'RECTANGULAR_DISTRIBUTION':'√3','TRIANGULAR_DISTRIBUTION':'√6','U_DISTRIBUTION':'√2'}.get(info['distribution'],str(divisor))
    width_label='拡張不確かさ' if info['distribution']=='NORMAL_DISTRIBUTION' else '半値幅'
    return f'{distribution}を採用します。{width_label}を除数{divisor_label}で割って標準不確かさへ換算します。入力単位は{unit}です。'


def enrich_project(project, area, key):
    """Enrich a fresh generator payload without changing its numerical data."""
    original=copy.deepcopy(project)
    cid=case_id(area,key)
    meanings=dict(part.split('=',1) for part in MEANINGS[cid].split('|'))
    refs=project.get('value_references') or {}
    for name,info in project['variable_values'].items():
        if info['type']=='result':continue
        label=meanings[name]
        old=info.get('definition','')
        images=re.findall(r'!\[[^\]]*\]\(asset:[^)]+\)',old)
        info['definition']=label+('。\n\n'+'\n'.join(images) if images else '。')
        for value in info['values']:
            old_description=value.get('description','')
            images=re.findall(r'!\[[^\]]*\]\(asset:[^)]+\)',old_description)
            source=re.search(r'(?:S\d+\.\d+|H\.\d+(?:\.\d+)*)',old+' '+old_description)
            description=label+'。\n\n'+describe_evaluation(info,value)
            ident=refs.get('variables',{}).get(name)
            if ident in refs.get('rules',{}):
                description+='\n\n入力幅は、参照値と量の中心値を用いた参照式から計算します。'
            if source:description+='\n\n出典：'+source[0]+'（本プロジェクトの出典資料）。'
            if images:description+='\n\n'+'\n'.join(images)
            value['description']=description
    if cid!='volume':
        overview,model,limits,steps=CASES[cid]
        if key=='S12_probability':limits='包含確率95.45%と有効自由度の下側整数からt分位点を数値計算します。EA表の丸めた掲載係数を使う方式とは区別します。'
        if key.startswith('H2'):model+=' このファイルは'+('手法1（入力平均から計算）' if key.endswith('approach1') else '手法2（各組で変換後に平均）')+'です。'
        if key.startswith('H4'):model+=' このファイルは'+('手法1（平均計数率の比）' if key.endswith('approach1') else '手法2（サイクル比の平均）')+'です。'
        assets=project.setdefault('image_assets',{})
        ident=import_image(assets,flow_image(project['document_info']['document_name'],steps))
        source=('EA-4/02 M:2022 rev03 / '+key.split('_')[0]+ '\nhttps://www.accredia.it/wp-content/uploads/2013/09/EA-4-02_2022-incertezza-nelle-tarature.pdf'
                if area=='ea402' else 'JCGM 100:2008 Annex '+key.split('_')[0].replace('H','H.')+'\nhttps://www.bipm.org/en/doi/10.59161/jcgm100-2008e')
        project['document_info']['description_markdown']=(f'## 測定の概要\n\n{overview}\n\n![測定と評価の流れ：本サンプル独自作図](asset:{ident})\n\n'
            f'## モデル式と入力\n\n{model}\n\n'
            f'## 評価条件\n\n{limits}\n\n## 出典\n\n{source}')
    else:
        project['document_info']['description_markdown']+='\n\n## モデル式の読み方\n\n秤量差mを水と空気の密度差で割り、基準分銅に関する浮力補正を掛け、容器の体膨張係数で20 °Cの体積に換算します。メニスカスと繰返しの補正は最後に加算します。\n\n体膨張係数の半値幅は中心値の5%です。水密度は原典表の丸め済み値を直接入力し、温度からの再計算は行っていません。'
    # Presentation editing must never change the numerical definition.
    for field in ('last_equation','variables','result_variables','value_names','correlation_coefficients','value_references','regressions','measurement_tables'):
        assert project.get(field)==original.get(field),field
    for name,info in project['variable_values'].items():
        before=copy.deepcopy(original['variable_values'][name]);after=copy.deepcopy(info)
        for item in (before,after):
            item.pop('definition',None)
            for value in item['values']:value.pop('description',None)
        assert before==after,name
    return project
