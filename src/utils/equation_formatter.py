import html
import re
from .model_expression import split_equations, FUNCTIONS
from .quantity_notation import IDENTIFIER, decode_greek, format_quantity_name


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
        equations = split_equations(equation)
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
        pattern = r'(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?|'+IDENTIFIER+r'|\*\*|[^\s]'
        return re.findall(pattern, decode_greek(text))

    def _first_identifier_token(self, text):
        for token in self._tokenize_side(text):
            if token in self._operator_tokens or token in {'^', '_'}:
                continue
            if self._is_number(token):
                continue
            return token
        return ''

    def _is_number(self, token):
        return bool(re.fullmatch(r'(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?', token or ''))

    def _format_side(self, text, result_vars, force_result=False):
        tokens = self._tokenize_side(text)
        def group(index, stop=False):
            parts = []
            while index < len(tokens) and not (stop and tokens[index] == ')'):
                value, index = power(index)
                parts.append(value)
            return ''.join(parts), index

        def atom(index):
            if index >= len(tokens):
                return '', index
            token = tokens[index]
            if token == '(':
                content, end = group(index+1, True)
                return '('+content+(')' if end < len(tokens) else ''), min(end+1,len(tokens))
            if token in self._operator_tokens or token in {'^','**'}:
                return html.escape('·' if token == '*' else token), index+1
            if token in FUNCTIONS and index+1 < len(tokens) and tokens[index+1]=='(':
                return html.escape(token), index+1
            return self._format_atom(token,result_vars,force_result), index+1

        def power(index):
            content, end = atom(index)
            if end < len(tokens) and tokens[end] in {'^','**'}:
                end += 1
                sign = ''
                if end < len(tokens) and tokens[end] in {'+','-'}:
                    sign = tokens[end]; end += 1
                exponent, end = power(end)
                # Parentheses remain visible to make the exponent's extent explicit.
                exponent = re.sub(r'</?span\b[^>]*>', '', exponent)
                content += '<sup>'+sign+exponent+'</sup>'
            return content, end

        return group(0)[0]

    def _format_atom(self, token, result_vars, force_result=False):
        escaped = html.escape(token)
        if self._is_number(token):
            return f'<span class="number">{escaped}</span>'
        var_class = 'result-variable' if force_result or token in result_vars else 'input-variable'
        notation = getattr(self.parent, 'model_notation', 'legacy')
        formatted = format_quantity_name(token,notation)
        base, sep, suffix = formatted.partition('<sub>')
        return f'<span class="{var_class}">{base}</span>'+ (sep+suffix if sep else '')

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
