import html
import re


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
                sup { font-size: 0.8em; vertical-align: super; }
            </style>
        """
        self._operator_tokens = {"+", "-", "*", "/", "(", ")", ",", "="}

    def format_equation(self, equation):
        """Format equation text as HTML."""
        equations = [eq.strip() for eq in (equation or "").split(',') if eq.strip()]
        formatted_parts = []
        result_vars = set()
        parsed_equations = []

        for eq in equations:
            if '=' not in eq:
                continue
            left_side, right_side = eq.split('=', 1)
            left_side = left_side.strip()
            right_side = right_side.strip()
            parsed_equations.append((left_side, right_side))
            result_token = self._first_identifier_token(left_side)
            if result_token:
                result_vars.add(result_token)

        for left_side, right_side in parsed_equations:
            left_html = self._format_side(left_side, result_vars, force_result=True)
            right_html = self._format_side(right_side, result_vars, force_result=False)
            formatted_parts.append(f"{left_html} = {right_html}")

        return '<br>'.join(formatted_parts)

    def _tokenize_side(self, text):
        tokens = []
        current = ''
        delimiters = set("+-*/^()_=,")
        for char in text:
            if char.isspace():
                if current:
                    tokens.append(current)
                    current = ''
                continue
            if char in delimiters:
                if current:
                    tokens.append(current)
                    current = ''
                tokens.append(char)
                continue
            current += char
        if current:
            tokens.append(current)
        return tokens

    def _first_identifier_token(self, text):
        for token in self._tokenize_side(text):
            if token in self._operator_tokens or token in {'^', '_'}:
                continue
            if self._is_number(token):
                continue
            return token
        return ''

    def _is_number(self, token):
        return bool(re.fullmatch(r'\d+(\.\d+)?', token or ''))

    def _format_side(self, text, result_vars, force_result=False):
        tokens = self._tokenize_side(text)
        html_parts = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token in self._operator_tokens:
                html_parts.append(f'<span class="operator">{html.escape(token)}</span>')
                i += 1
                continue
            if token in {'^', '_'}:
                html_parts.append(f'<span class="operator">{token}</span>')
                i += 1
                continue

            html_parts.append(self._format_atom(token, result_vars, force_result))
            i += 1

            while i < len(tokens) and tokens[i] == '_':
                sub_text, i = self._consume_marker_expression(tokens, i + 1)
                if sub_text:
                    html_parts.append(f'<sub>{sub_text}</sub>')

            if i < len(tokens) and tokens[i] == '^':
                sup_text, i = self._consume_marker_expression(tokens, i + 1)
                if sup_text:
                    html_parts.append(f'<sup>{sup_text}</sup>')

        return ''.join(html_parts)

    def _consume_marker_expression(self, tokens, start_index):
        if start_index >= len(tokens):
            return '', start_index

        token = tokens[start_index]
        if token != '(':
            return html.escape(token), start_index + 1

        # Parenthesized group: keep as plain text inside sub/sup.
        depth = 0
        parts = []
        i = start_index
        while i < len(tokens):
            current = tokens[i]
            parts.append(html.escape(current))
            if current == '(':
                depth += 1
            elif current == ')':
                depth -= 1
                if depth == 0:
                    return ''.join(parts), i + 1
            i += 1
        return ''.join(parts), i

    def _format_atom(self, token, result_vars, force_result=False):
        escaped = html.escape(token)
        if self._is_number(token):
            return f'<span class="number">{escaped}</span>'
        var_class = 'result-variable' if force_result or token in result_vars else 'input-variable'
        return f'<span class="{var_class}">{escaped}</span>'

    def _format_variables(self, text):
        """Backward-compatible helper."""
        words = text.split()
        formatted_words = []
        for word in words:
            if len(word) == 1 and word.isalpha():
                formatted_words.append(f'<span class="variable">{word}</span>')
            else:
                formatted_words.append(word)
        return ' '.join(formatted_words)

    def _format_operators(self, text):
        """Backward-compatible helper."""
        operators = ['+', '-', '*', '/', '^']
        for op in operators:
            text = text.replace(op, f'<span class="operator">{op}</span>')
        return text

    def _format_numbers(self, text):
        """Backward-compatible helper."""
        numbers = re.findall(r'\d+\.?\d*', text)
        for num in numbers:
            text = text.replace(num, f'<span class="number">{num}</span>')
        return text

    def get_style_sheet(self):
        """Return style sheet."""
        return self.style_sheet
