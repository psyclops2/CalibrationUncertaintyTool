from src.utils.markdown_renderer import render_markdown_to_html


SAMPLE_MARKDOWN = """# 見出し1
## 見出し2
### 見出し3
#### 見出し4
##### 見出し5
###### 見出し6

- リスト1
    - ネスト リスト1_1
        - ネスト リスト1_1_1
        - ネスト リスト1_1_2
    - ネスト リスト1_2
- リスト2
- リスト3

normal **bold** normal
normal __bold__ normal

|header1|header2|header3|
|:--|--:|:--:|
|align left|align right|align center|
|a|b|c|
"""


def test_markdown_renderer_renders_expected_structures():
    html = render_markdown_to_html(SAMPLE_MARKDOWN)

    # headings
    assert "<h1>見出し1</h1>" in html
    assert "<h2>見出し2</h2>" in html
    assert "<h3>見出し3</h3>" in html
    assert "<h4>見出し4</h4>" in html
    assert "<h5>見出し5</h5>" in html
    assert "<h6>見出し6</h6>" in html

    # nested lists
    assert html.count("<ul>") >= 3
    assert "<li>リスト1" in html
    assert "<li>ネスト リスト1_1" in html
    assert "<li>ネスト リスト1_1_1</li>" in html
    assert "<li>ネスト リスト1_1_2</li>" in html
    assert "<li>ネスト リスト1_2</li>" in html
    assert "<li>リスト2</li>" in html
    assert "<li>リスト3</li>" in html

    # bold
    assert html.count("<strong>bold</strong>") == 2

    # table + alignment
    assert "<table>" in html
    assert '<th style="text-align: left;">header1</th>' in html
    assert '<th style="text-align: right;">header2</th>' in html
    assert '<th style="text-align: center;">header3</th>' in html
    assert '<td style="text-align: left;">align left</td>' in html
    assert '<td style="text-align: right;">align right</td>' in html
    assert '<td style="text-align: center;">align center</td>' in html
