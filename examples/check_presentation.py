"""Verify sample explanations, embedded images and generated HTML."""
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.utils.project_io import read_project


def check():
    records=[]
    for area in ('ea402','gum','euramet19'):
        for path in sorted((ROOT/'examples'/area/'projects').glob('*.cutp')):
            p=read_project(path)
            document=p['document_info']['description_markdown']
            assert '操作して確認すること' not in document,path
            assert len(document)>200,path
            assets=p.get('image_assets',{})
            assert assets,path
            references=set(re.findall(r'asset:([a-f0-9]{64})',json.dumps(p,ensure_ascii=False)))
            assert references and references<=set(assets),path
            count=0
            for name,info in p['variable_values'].items():
                if info['type']=='result':continue
                assert len(info.get('definition',''))>5,(path,name)
                for value in info['values']:
                    assert len(value.get('description',''))>40,(path,name)
                count+=1
            if area=='ea402':reports=[path.parent.parent/'reports'/f'{path.stem}_tool_report.html']
            elif area=='gum':reports=list((path.parent.parent/'reports').glob(f'{path.stem}_*_tool.html'))
            else:reports=[path.parent.parent/'reports'/f'{path.stem}.html']
            assert reports,path
            for report in reports:
                html=report.read_text(encoding='utf-8')
                assert 'data:image/png;base64,' in html,report
                assert 'src="asset:' not in html,report
                assert '操作して確認すること' not in html,report
            records.append(dict(project=f'{area}/projects/{path.name}',explained_inputs=count,images=len(assets),reports=len(reports)))
    assert len(records)==24
    (ROOT/'examples/presentation-verification.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Presentation checked: {len(records)} models, {sum(r["explained_inputs"] for r in records)} inputs, {sum(r["images"] for r in records)} embedded images.')


if __name__=='__main__':check()
