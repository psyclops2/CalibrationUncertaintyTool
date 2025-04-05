class EquationFormatter:
    def __init__(self, parent=None):
        self.parent = parent
        self.style_sheet = """
            <style>
                .input-variable { color: #0000FF; font-weight: bold; }
                .result-variable { color: #808080; font-weight: bold; }
                .operator { color: #000000; }
                .number { color: #000000; }
                sub { font-size: 0.8em; vertical-align: sub; }
            </style>
        """
        
    def format_equation(self, equation):
        """方程式をHTML形式で表示"""
        try:
            print(f"【デバッグ】方程式のフォーマット開始: '{equation}'")
            # 方程式を分割
            equations = [eq.strip() for eq in equation.split(',')]
            formatted_parts = []
            
            # 計算結果の変数を収集（左辺の変数）
            result_vars = set()
            for eq in equations:
                if '=' not in eq:
                    continue
                left_side = eq.split('=', 1)[0].strip()
                result_vars.add(left_side)
            
            print(f"【デバッグ】計算結果の変数: {result_vars}")
            
            for eq in equations:
                if '=' not in eq:
                    continue
                    
                left_side, right_side = eq.split('=', 1)
                left_side = left_side.strip()
                right_side = right_side.strip()
                print(f"【デバッグ】分割: 左辺='{left_side}', 右辺='{right_side}'")
                
                # 右辺のトークン化（下付き文字に対応）
                tokens = []
                current_token = ''
                i = 0
                while i < len(right_side):
                    char = right_side[i]
                    if char in '+-*/^()':
                        if current_token:
                            tokens.append(current_token)
                            current_token = ''
                        tokens.append(char)
                        i += 1
                    elif char == '_':
                        # 下付き文字の処理
                        if current_token:
                            tokens.append(current_token)
                            current_token = ''
                        tokens.append('_')
                        i += 1
                    else:
                        current_token += char
                        i += 1
                if current_token:
                    tokens.append(current_token)
                
                print(f"【デバッグ】トークン化結果: {tokens}")
                
                # トークンをHTMLに変換
                html_parts = []
                i = 0
                while i < len(tokens):
                    token = tokens[i]
                    if token == '_' and i + 1 < len(tokens):
                        # 下付き文字の処理
                        base_var = html_parts[-1].split('>')[1].split('<')[0]  # 直前の変数名を取得
                        html_parts[-1] = f'<span class="{"result-variable" if base_var in result_vars else "input-variable"}">{base_var}</span>'
                        html_parts.append(f'<sub>{tokens[i+1]}</sub>')
                        i += 2
                        continue
                    elif token in '+-*/^()':
                        html_parts.append(f'<span class="operator">{token}</span>')
                    elif token.replace('.', '').isdigit():
                        html_parts.append(f'<span class="number">{token}</span>')
                    else:
                        # 変数の処理（計算結果かどうかで色を変える）
                        var_class = "result-variable" if token in result_vars else "input-variable"
                        html_parts.append(f'<span class="{var_class}">{token}</span>')
                    i += 1
                
                # 左辺の処理（常に計算結果変数）
                left_tokens = []
                current_token = ''
                i = 0
                while i < len(left_side):
                    char = left_side[i]
                    if char == '_':
                        if current_token:
                            left_tokens.append(current_token)
                            current_token = ''
                        left_tokens.append('_')
                        i += 1
                    else:
                        current_token += char
                        i += 1
                if current_token:
                    left_tokens.append(current_token)
                
                # 左辺のHTML変換
                left_html = []
                i = 0
                while i < len(left_tokens):
                    token = left_tokens[i]
                    if token == '_' and i + 1 < len(left_tokens):
                        left_html.append(f'<sub>{left_tokens[i+1]}</sub>')
                        i += 2
                        continue
                    else:
                        # 左辺は常に計算結果変数
                        left_html.append(f'<span class="result-variable">{token}</span>')
                    i += 1
                
                formatted_parts.append(f"{''.join(left_html)} = {''.join(html_parts)}")
            
            html_content = '<br>'.join(formatted_parts)
            print(f"【デバッグ】最終HTML: '{html_content}'")
            return html_content
            
        except Exception as e:
            print(f"【デバッグ】方程式のフォーマットエラー: {str(e)}")
            raise
            
    def _format_variables(self, text):
        """変数をイタリック体に"""
        # 単一の文字を変数として扱う
        words = text.split()
        formatted_words = []
        
        for word in words:
            if len(word) == 1 and word.isalpha():
                formatted_words.append(f'<span class="variable">{word}</span>')
            else:
                formatted_words.append(word)
                
        return ' '.join(formatted_words)
        
    def _format_operators(self, text):
        """演算子を太字に"""
        # 既にフォーマットされた部分を保護
        protected_parts = []
        current_pos = 0
        
        # 既存のHTMLタグを保護
        while True:
            start = text.find('<', current_pos)
            if start == -1:
                break
            end = text.find('>', start)
            if end == -1:
                break
            protected_parts.append((start, end + 1))
            current_pos = end + 1
            
        # 保護された部分を一時的に置換
        for i, (start, end) in enumerate(protected_parts):
            placeholder = f'__PROTECTED_{i}__'
            text = text[:start] + placeholder + text[end:]
            
        # 演算子をフォーマット
        operators = ['+', '-', '*', '/', '^']
        for op in operators:
            text = text.replace(op, f'<span class="operator">{op}</span>')
            
        # 保護された部分を元に戻す
        for i, (start, end) in enumerate(protected_parts):
            placeholder = f'__PROTECTED_{i}__'
            text = text.replace(placeholder, text[start:end])
            
        return text
        
    def _format_numbers(self, text):
        """数値を青色に"""
        import re
        # 数値（小数点を含む）を検出
        numbers = re.findall(r'\d+\.?\d*', text)
        for num in numbers:
            text = text.replace(num, f'<span class="number">{num}</span>')
        return text
        
    def get_style_sheet(self):
        """スタイルシートを取得"""
        return self.style_sheet 