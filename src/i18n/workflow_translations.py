"""English translations for shared workflow UI source messages."""

WORKFLOW_EN = {'{0}\n中心値 {1:.12g} / u {2:.8g} / 自由度 {3}\n{4}\n単位：{5}（自動換算はしません）': '{0}\n'
                                                                    'Central value {1:.12g} / u {2:.8g} / df '
                                                                    '{3}\n'
                                                                    '{4}\n'
                                                                    'Unit: {5} (no automatic conversion)',
 '{0}: 平均={1:.8g}, u={2:.6g}': '{0}: mean={1:.8g}, u={2:.6g}',
 '使用した観測組 {0} / 自由度 {1}\n': 'Observation rows used: {0} / df {1}\n',
 '参照先をダブルクリックすると、最後に選択した式の末尾へ挿入します。': 'Double-click a reference to append it to the last selected '
                                      'expression.',
 '参照式は各校正点で評価します。数値は表示した単位で扱います。単位の自動換算は行いません。': 'Expressions are evaluated per calibration point in the '
                                                 'displayed units. Unit conversion is not automatic.',
 '量：{0} / 校正点：{1}\n適用範囲：この量の現在の校正点': 'Quantity: {0} / Calibration point: {1}\n'
                                     'Scope: current calibration point of this quantity',
 '文字を挿入': 'Insert character',
 '数式を挿入': 'Insert function',
 '小文字': 'Lowercase',
 '大文字': 'Uppercase',
 '異体字': 'Variants',
 '円周率': 'Pi',
 '正弦': 'Sine',
 '余弦': 'Cosine',
 '正接': 'Tangent',
 '逆正弦': 'Inverse sine',
 '逆余弦': 'Inverse cosine',
 '逆正接': 'Inverse tangent',
 '2引数の逆正接': 'Two-argument inverse tangent',
 '双曲線正弦': 'Hyperbolic sine',
 '双曲線余弦': 'Hyperbolic cosine',
 '双曲線正接': 'Hyperbolic tangent',
 '指数関数': 'Exponential',
 '自然対数': 'Natural logarithm',
 '平方根': 'Square root',
 '絶対値': 'Absolute value',
 '行を追加': 'Add row',
 '選択行を削除': 'Delete selected rows',
 '画像を挿入…': 'Insert image…',
 '画像の説明': 'Image caption',
 'キャプション・出典（省略可）': 'Caption / source (optional)',
 '画像の挿入': 'Insert image',
 '画像ファイルを挿入': 'Insert image file',
 '画像ファイルを挿入…': 'Insert image file…',
 '画像を読み込めません。': 'Cannot read the image.',
 '画像を保存できません。': 'Cannot save the image.',
 '画像が大きすぎます（最大4000万画素）。': 'Image exceeds the limit of 40 million pixels.',
 '説明文（画像は「画像を挿入」またはCtrl+V）': 'Description (use Insert image or Ctrl+V for images)',
 '「画像を挿入」でPNG・JPEGを選択できます。画像もプロジェクトに保存します。': 'Select PNG or JPEG with Insert image. Images are saved in the '
                                             'project.',
 '画像ファイルを選択し、説明文のカーソル位置へ挿入します': 'Choose an image file to insert at the cursor position',
 '<span>[添付画像が見つかりません：': '<span>[Missing attached image: ',
 '<span>[添付画像を読み込めません]</span>': '<span>[Cannot read the attached image]</span>',
 'Type Aの評価方法': 'Type A evaluation method',
 '評価方法': 'Evaluation method',
 '入力を確認してください': 'Check the input',
 'プール標準偏差の自由度': 'Degrees of freedom of pooled standard deviation',
 'プール標準偏差（量と同じ単位）': 'Pooled standard deviation (same unit as the quantity)',
 '評価済み中心値': 'Evaluated central value',
 '評価済み標準不確かさ': 'Evaluated standard uncertainty',
 '評価済み自由度': 'Evaluated degrees of freedom',
 '評価の根拠': 'Evaluation rationale',
 '観測列は元の入力欄に保持します。プール標準偏差の自由度は、\n今回の観測数ではなく、標準偏差を推定したデータに基づき指定します。': 'Observations are retained in their '
                                                                     'original field. Specify the degrees of '
                                                                     'freedom of the pooled standard '
                                                                     'deviation\n'
                                                                     'from the data used to estimate it, not '
                                                                     'the number of current observations.',
 '包含係数の評価方法（現在の結果・校正点）': 'Coverage method (current result and calibration point)',
 '出力分布が正規分布で近似できるか確認して方法を選択します。\nEA表にない自由度は下側の掲載値を使います（有限の自由度50超ではk=2.05）。\n係数の指定だけでは包含確率を検証したことにはなりません。': 'Select '
                                                                                                           'a '
                                                                                                           'method '
                                                                                                           'after '
                                                                                                           'checking '
                                                                                                           'whether '
                                                                                                           'a '
                                                                                                           'normal '
                                                                                                           'approximation '
                                                                                                           'is '
                                                                                                           'appropriate.\n'
                                                                                                           'For '
                                                                                                           'degrees '
                                                                                                           'of '
                                                                                                           'freedom '
                                                                                                           'missing '
                                                                                                           'from '
                                                                                                           'the '
                                                                                                           'EA '
                                                                                                           'table, '
                                                                                                           'the '
                                                                                                           'lower '
                                                                                                           'listed '
                                                                                                           'value '
                                                                                                           'is '
                                                                                                           'used '
                                                                                                           '(k=2.05 '
                                                                                                           'for '
                                                                                                           'finite '
                                                                                                           'df '
                                                                                                           'above '
                                                                                                           '50).\n'
                                                                                                           'Specifying '
                                                                                                           'a '
                                                                                                           'factor '
                                                                                                           'alone '
                                                                                                           'does '
                                                                                                           'not '
                                                                                                           'verify '
                                                                                                           'the '
                                                                                                           'coverage '
                                                                                                           'probability.',
 '有効自由度を下側の整数へ切り捨てる': 'Round effective degrees of freedom down to an integer',
 '包含確率 [%]': 'Coverage probability [%]',
 '指定する包含係数': 'Specified coverage factor',
 '採用根拠': 'Rationale',
 '包含係数を確認してください': 'Check the coverage factor',
 '評価値の入力元': 'Source of evaluated values',
 '入力元': 'Input source',
 '直接入力': 'Direct input',
 '回帰の平均応答': 'Mean regression response',
 '測定表の列の平均': 'Mean of a measurement-table column',
 '回帰モデル': 'Regression model',
 '回帰タブでデータを編集…': 'Edit data in the Regression tab…',
 '評価するxの入力': 'Input for x',
 '固定の数値・式': 'Fixed number or expression',
 '固定量の現在点': 'Current point of a fixed quantity',
 '評価するx（回帰のxと同じ単位）': 'Evaluation x (same unit as regression x)',
 '固定量': 'Fixed quantity',
 '測定表': 'Measurement table',
 '使用する列': 'Column to use',
 '測定表を作成…': 'Create measurement table…',
 '選択した測定表を編集…': 'Edit selected measurement table…',
 '接続中の評価値を統計量として固定し、根拠を残す': 'Freeze linked values as evaluated statistics and record their source',
 '評価値を確認': 'Preview evaluated values',
 '回帰タブでモデルを登録してください。': 'Create a model in the Regression tab.',
 '評価する固定量を選択してください': 'Select the fixed quantity to evaluate',
 '回帰モデルを登録・選択してください': 'Create and select a regression model',
 '測定表と列を選択してください': 'Select a measurement table and column',
 '直接入力へ戻します。保存してある直接入力を復元します。': 'Return to direct input and restore the saved direct values.',
 '現在の評価値を固定し、自動更新を解除します。': 'Freeze the current evaluated values and stop automatic updates.',
 ' / 固定した時点 ': ' / Frozen at ',
 '同時観測の測定表': 'Paired-observation table',
 '同じ行が同じ観測組です。欠測のある組は、行全体を除外してください。派生列は行ごとに計算します。': 'Each row is one set of paired observations. Exclude the '
                                                    'entire row if any observation is missing. Derived '
                                                    'columns are evaluated per row.',
 '列名（量名）': 'Column name (quantity)',
 '単位': 'Unit',
 '派生列の式（元データ列は空欄）': 'Derived-column expression (blank for raw data)',
 '列の式は同じ行の量名で記述します。数値の単位換算は自動ではありません。': 'Use quantity names from the same row in column expressions. Numeric '
                                        'unit conversion is not automatic.',
 '列を追加': 'Add column',
 '列を削除': 'Delete column',
 'CSVを取り込む…': 'Import CSV…',
 'CSVを取り込む': 'Import CSV',
 '観測組を追加': 'Add observation row',
 '観測組を削除': 'Delete observation row',
 '評価を確認': 'Preview evaluation',
 '除外': 'Exclude',
 'CSVの列数が見出しと一致していません': 'The CSV column count does not match the header',
 'CSVの見出しには、重複しない量名を指定してください': 'Use unique quantity names for CSV headers',
 'CSVを確認してください': 'Check the CSV',
 '表を置き換える': 'Replace table',
 '編集中の測定表をCSVの内容で置き換えますか？': 'Replace the table being edited with the CSV contents?',
 '取り込んだ列の単位と行の対応を確認してください。': 'Check the units of imported columns and the pairing of rows.',
 '結果どうしの共分散・相関': 'Covariance and correlation between outputs',
 '校正点：': 'Calibration point: ',
 ' / 一次伝播': ' / First-order propagation',
 '共分散（行の単位 × 列の単位）': 'Covariance (row unit × column unit)',
 '相関係数': 'Correlation',
 '未定義（u=0）': 'Undefined (u=0)',
 'この校正点のレポートに出力間の共分散・相関を含める': 'Include output covariance and correlation in the report for this point',
 '参照値とType B参照式': 'Reference values and Type B expressions',
 '半値幅式を空欄にすると直接入力へ戻ります。既存の手動計算式は自動変換しません。': 'Clear the half-width expression to return to direct input. '
                                            'Existing manual formulas are not converted automatically.',
 '参照先をダブルクリックすると、最後に選択した式の末尾へ挿入します。\n参照式は各校正点で評価します。数値は表示した単位で扱います。単位の自動換算は行いません。': 'Double-click a '
                                                                                    'reference to append it '
                                                                                    'to the last selected '
                                                                                    'expression.\n'
                                                                                    'Expressions are '
                                                                                    'evaluated at each '
                                                                                    'calibration point using '
                                                                                    'the displayed units. '
                                                                                    'Unit conversion is not '
                                                                                    'automatic.',
 '名前': 'Name',
 '共通値／式': 'Common value / expression',
 '適用範囲': 'Scope',
 '選択点の上書き値／式': 'Override value / expression for selected point',
 '説明': 'Description',
 '参照値を追加': 'Add reference value',
 '選択した参照値を削除': 'Delete selected reference value',
 'Type B変数': 'Type B quantity',
 '全点共通の半値幅式': 'Common half-width expression',
 '選択点の上書き式': 'Override expression for selected point',
 '上書き対象点': 'Point to override',
 '全点の計算結果を確認': 'Preview results for all points',
 '変数': 'Quantity',
 '校正点': 'Calibration point',
 '半値幅': 'Half-width',
 '標準不確かさ': 'Standard uncertainty',
 '状態': 'Status',
 '参照値': 'Reference value',
 '全点共通': 'All points',
 '校正点ごと': 'Per point',
 '削除済み: ': 'Deleted: ',
 ' / 校正点：': ' / Calibration point: ',
 ' / 現在点の中心値': ' / Central value at current point',
 ' の中心値': ' central value',
 '量：': 'Quantity: ',
 '\n単位：': '\nUnit: ',
 '\n適用範囲：この量の現在の校正点': '\nScope: current calibration point of this quantity',
 '適用範囲は common または point を指定してください': 'Specify common or point for the scope',
 '点ごとの上書きを使う参照値は point にしてください': 'Use point scope for reference values with per-point overrides',
 '入力エラー': 'Input error',
 '一次近似を点検': 'Check first-order approximation',
 '一次近似：未点検': 'First-order approximation: not checked',
 '結果どうしの相関…': 'Output correlation…',
 '包含係数の評価方法…': 'Coverage method…',
 '試行結果を保存…': 'Save trial results…',
 '乱数シード': 'Random seed',
 '詳細な試行条件': 'Advanced trial settings',
 '空欄は自動。再現する場合は保存した乱数シードを指定': 'Leave blank for an automatic seed. Use a saved seed to reproduce a trial.',
 '参照式を設定': 'Set reference expression',
 '入力元を確認してください：': 'Check the input source: ',
 'モデル式を入力してください': 'Enter a model equation',
 '一次感度が0でも二次の寄与があり得る項：': 'Terms with possible second-order contributions despite zero first-order '
                         'sensitivity: ',
 '。必要に応じてMC等で確認してください。この点検ではuを補正していません。': '. Check with Monte Carlo or another method if needed. This check '
                                          'does not correct u.',
 '該当する二次の項は検出されませんでした。一次近似全体の妥当性を保証する点検ではありません。': 'No matching second-order terms were found. This check '
                                                  'does not establish the overall validity of the '
                                                  'first-order approximation.',
 '一次近似を点検できません：': 'Cannot check the first-order approximation: ',
 '未評価': 'Not evaluated',
 '包含条件を評価できません：': 'Cannot evaluate coverage conditions: ',
 '相関付き推定量の自由度を評価できません。': 'Degrees of freedom of correlated estimates could not be evaluated. ',
 '指定したkを使用しています。': 'Using the specified k.',
 'uは計算済みですが、自動方式のk・Uは未評価です。': 'u has been calculated, but automatic k and U have not been evaluated.',
 '寄与率は相関項を両方の量へ半分ずつ割り当てています。負になる場合があります。': 'Half of each covariance term is assigned to each quantity in the '
                                           'contribution percentages; percentages may be negative.',
 'モデル式を確認してください': 'Check the model equation',
 '未入力: ': 'Missing input: ',
 '計算できません': 'Cannot calculate',
 '校正点の結果一覧': 'Results by calibration point',
 '結果値': 'Result',
 '合成標準不確かさ': 'Combined standard uncertainty',
 '包含係数': 'Coverage factor',
 '拡張不確かさ': 'Expanded uncertainty',
 '行をダブルクリックすると、その校正点の詳細を表示します。': 'Double-click a row to view details for that calibration point.',
 'Type A評価：': 'Type A evaluation: ',
 '包含方法・採用根拠': 'Coverage method and rationale',
 '包含方法': 'Coverage method',
 '全校正点の結果一覧': 'Results for all calibration points',
 'Type A評価': 'Type A evaluation',
 '入力元：直接入力…': 'Input source: direct input…',
 '入力元：': 'Input source: ',
 '回帰…': 'Regression…',
 '測定表…': 'Measurement table…',
 '評価方法：': 'Evaluation method: ',
 '観測列から評価': 'Evaluate from observations',
 'プール標準偏差を使用': 'Use pooled standard deviation',
 '評価済み統計量を入力': 'Enter evaluated statistics',
 '従来互換（自由度10以上はk=2）': 'Legacy (k=2 for df of 10 or more)',
 't分布（設定ファイルの表）': 'Student t (configured table)',
 'EA-4/02 表E.1（95.45%・自由度切捨て）': 'EA-4/02 Table E.1 (95.45%, df rounded down)',
 '包含係数を指定（根拠を記録）': 'Specify a coverage factor (record rationale)',
 '包含確率から計算（t分布／正規分布近似）': 'Calculate from coverage probability (Student t / normal approximation)',
 '／表にない自由度は下側の掲載値を使用（保守的）': ' / Use the lower listed df when missing from the table (conservative)',
 't分布': 'Student t',
 '・自由度切捨て': ' / df rounded down',
 '・自由度をそのまま使用': ' / use unrounded df',
 '計算結果': 'Result quantity',
 '入力量': 'Input quantity',
 '入力': 'Input',
 'このソフトについて': 'About',
 'バージョン：': 'Version: ',
 'プロジェクトのリポジトリ': 'Project repository',
 'Qtのライセンス・モジュール別条件': 'Qt licensing options / module conditions',
 '同梱コードの表示も参照': 'see also bundled-component notices',
 '閉じる': 'Close',
 'ライセンス': 'License',
 '依存ライブラリ': 'Dependencies',
 '第三者ライセンス表示': 'Third-party license notices',
 '本体はMITライセンスです。第三者のライブラリ・資料には各権利者の条件が適用されます。':
     'The application is licensed under MIT. Third-party libraries and reference materials retain their respective terms.'}

# Reference formula editor
WORKFLOW_EN.update({'参照する値を選択': 'Choose a reference',
 '登録した参照値': 'Registered values',
 '量の中心値': 'Quantity central values',
 '名前・説明で検索': 'Search names and descriptions',
 '式に挿入': 'Insert into formula',
 '入力幅の参照式': 'Width reference formula',
 '参照式で計算': 'Calculate from a reference formula',
 '直接入力へ戻す': 'Return to direct input',
 '入力方法': 'Input method',
 '全校正点の基本式': 'Default formula for all points',
 'この校正点だけ別の式': 'Different formula for this point',
 '式の適用先': 'Apply formula to',
 '参照する値を挿入…': 'Insert reference…',
 '関数を挿入': 'Insert function',
 'この点を基本式に戻す': 'Use default formula for this point',
 '入力幅の計算式': 'Width formula',
 '追加': 'Add',
 '削除': 'Delete',
 '値の適用範囲': 'Value scope',
 '値または式': 'Value or formula',
 '選択した校正点だけ値を変える': 'Use a different value at the selected point',
 '参照値の登録・編集': 'Reference values',
 '計算する校正点': 'Point being calculated',
 '値': 'Value',
 '計算する量': 'Quantity to calculate',
 '校正点ごとの計算結果': 'Results by calibration point',
 '仕様係数など、式から使う数値を名前と単位で登録します。': 'Register named values and units for use in formulas, such as '
                                'specification coefficients.',
 'すべての校正点で参照式を解除し、直接入力へ戻します。': 'Remove this quantity’s formula at all points and return to direct '
                               'input.',
 '{0}を計算します。単位：{1}。数値の単位は自動換算しません。': 'Calculate {0}. Unit: {1}. Units are not converted '
                                     'automatically.',
 'この点の式を設定します。ほかの点の設定は変わりません。': 'Set the formula for this point. Settings at other points are '
                                'unchanged.',
 '各校正点の値を使って計算します。個別の式がある点では、その式を優先します。': 'Evaluate using each point’s values. A point-specific '
                                          'formula takes precedence where set.',
 '新しい参照値': 'New reference value',
 '校正点：{0}': 'Calibration point: {0}',
 '{0} / {1}：{2}': '{0} / {1}: {2}',
 '参照値の名前を入力してください。': 'Enter a name for each reference value.',
 '値を代入した式：{0}': 'Formula with values substituted: {0}',
 '参照先が見つかりません': 'Missing reference',
 '削除された校正点': 'Deleted calibration point',
 '{0}の中心値 / {1}': 'Central value of {0} / {1}',
 'キャンセル': 'Cancel',
 '保存': 'Save',
 '全点共通で保存すると、校正点ごとの値は解除されます。': 'Saving as a common value removes its point-specific values.',
 '値：{0} {1}': 'Value: {0} {1}',
 '{0}：{1}': '{0}: {1}'})

WORKFLOW_EN.update({
 '入力幅の計算式を設定': 'Set input width formula',
 '量：{0} / 計算対象：{1} / 単位：{2}': 'Quantity: {0} / Calculate: {1} / Unit: {2}',
 '式に使う値を名前で記入し、次の画面で取得方法を指定します。': 'Name the inputs in the formula, then choose their sources on the next page.',
 '式を変更': 'Edit formula',
 '入力の対応を変更': 'Edit input bindings',
 '点ごとの別式を保持しています。別式のある点では、その式を優先します。': 'Point-specific formulas are retained and take precedence at those points.',
 '点ごとの別式を編集': 'Edit point-specific formulas',
 '戻る': 'Back', '次へ': 'Next', '適用': 'Apply',
 '必要な入力：{0}': 'Required inputs: {0}', 'なし': 'None',
 '式の構文を確認してください。': 'Check the formula syntax.',
 'この式には対応付けが必要な入力はありません。': 'This formula needs no input bindings.',
 '全点共通の数値': 'Number shared by all points',
 '校正点ごとの数値': 'Number for each point',
 '登録済みの参照値': 'Registered reference value',
 '選択してください': 'Select an item', '参照値': 'Reference value', '量': 'Quantity',
 '入力を確認してください：{0}': 'Check the inputs: {0}',
 '1. 計算式': '1. Formula', '2. 入力の対応付け': '2. Input bindings',
 '3. 計算結果の確認': '3. Review results',
 '入力幅': 'Input width',
 '未入力・参照先を確認': 'Missing input or reference',
})

WORKFLOW_EN.update({
 '複数の式で共有する値を登録します。式の手入力値は各量の設定で編集します。': 'Register values to share between formulas. Edit manual formula inputs in the quantity settings.',
 '適用する校正点：{0}': 'Applies to calibration point: {0}',
})

WORKFLOW_EN.update({
 '物理定数など、すべての式・校正点で同じ値を使う参照値を登録します。': 'Register constants with the same value across all formulas and calibration points.',
 '旧形式の点別・測定値参照は保持しています。変更は対象量の入力の対応付けで行ってください。': 'Legacy point-dependent references are retained. Change their use in the quantity input bindings.',
 '（旧形式・読取専用）': ' (legacy, read-only)',
 '参照値の式には全点共通の参照値だけを使用できます。': 'Reference expressions may use only project-wide constants.',
})
