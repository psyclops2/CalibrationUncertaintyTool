"""Record installed dependency metadata and copy unmodified license notices.

Run with the project development environment. This is an inventory, not a
certification of distribution compliance or a dependency lock file.
"""
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path, PurePosixPath
import re
import sys

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'licenses'


def requirements(path):
    return [Requirement(line.strip()) for line in path.read_text(encoding='utf-8').splitlines()
            if line.strip() and not line.lstrip().startswith('#')]


def closure(roots):
    found = {}
    pending = list(roots)
    while pending:
        requirement = pending.pop()
        if requirement.marker and not requirement.marker.evaluate({'extra':''}):
            continue
        key = canonicalize_name(requirement.name)
        if key in found:
            continue
        distribution = metadata.distribution(requirement.name)
        found[key] = distribution
        pending.extend(Requirement(value) for value in distribution.requires or [])
    return found


def write_notice_index(records, python_notice):
    """Generate the recipient-facing index, without collection/audit instructions."""
    lines = ['# ライセンス原文一覧', '',
        '依存ライブラリと開発・テスト用ツールの著作権表示・ライセンス原文を収録しています。',
        '各文書の内容は権利者が提供した原文です。本体のMITライセンスに置き換えるものではありません。', '',
        '[第三者ライセンス表示に戻る](../THIRD_PARTY_LICENSES.md)', '']
    for usage,title in (('runtime','実行用ライブラリ'),('development','開発・テスト用ツール')):
        lines.extend(['## '+title,''])
        for record in records:
            if record['usage'] != usage:
                continue
            lines.extend(['### '+record['name'], '', '原文の版：'+record['version'], ''])
            for notice in record['notices']:
                path = Path(notice['path']).relative_to('licenses').as_posix()
                lines.append(f'- [{Path(path).name}]({path})')
            lines.append('')
    if python_notice:
        lines.extend(['## Python', '', '[著作権表示・ライセンス原文](python/LICENSE.txt)', ''])
    lines.extend(['## GNUライセンス原文', '',
        '- [GNU Lesser General Public License v3](upstream/LGPL-3.0.txt)',
        '- [GNU General Public License v2](upstream/GPL-2.0.txt)',
        '- [GNU General Public License v3](upstream/GPL-3.0.txt)', ''])
    (OUT/'README.md').write_text('\n'.join(lines),encoding='utf-8')


def main():
    runtime = closure(requirements(ROOT/'requirements.txt'))
    development = closure(requirements(ROOT/'requirements-dev.txt'))
    packages = dict(development,**runtime)
    OUT.mkdir(exist_ok=True)
    records = []
    notice_name = re.compile(r'^(licen[sc]e|copying|notice|authors|copyright)(?:[._-].*)?$',re.I)
    for key,distribution in sorted(packages.items()):
        notices = []
        for entry in distribution.files or []:
            relative = PurePosixPath(str(entry).replace('\\','/'))
            if not (notice_name.fullmatch(relative.name) or relative.name.startswith('LicenseRef-')) or '..' in relative.parts or relative.is_absolute():
                continue
            source = Path(distribution.locate_file(entry))
            if not source.is_file():
                continue
            # Keep each version separate; a later collection does not delete older notices.
            target = OUT/'third-party'/(key+'-'+distribution.version)/Path(*relative.parts)
            target.parent.mkdir(parents=True,exist_ok=True)
            raw = source.read_bytes();target.write_bytes(raw)
            notices.append({'path':target.relative_to(ROOT).as_posix(),
                            'sha256':hashlib.sha256(raw).hexdigest()})
        info = distribution.metadata
        records.append({'name':info['Name'],'version':distribution.version,
            'usage':'runtime' if key in runtime else 'development',
            'license_expression':info.get('License-Expression'),
            'license_metadata':info.get('License'),
            'project_urls':info.get_all('Project-URL') or [],
            'notices':notices})
    python_license = Path(sys.base_prefix)/'LICENSE.txt'
    python_notice = None
    if python_license.is_file():
        target = OUT/'python'/'LICENSE.txt';target.parent.mkdir(exist_ok=True)
        raw = python_license.read_bytes();target.write_bytes(raw)
        python_notice={'path':target.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(raw).hexdigest()}
    inventory={'scope':'Installed Python packages; bundled native components are not exhaustively enumerated.',
        'python_version':sys.version.split()[0],'python_notice':python_notice,'packages':records}
    (OUT/'dependency-inventory.json').write_text(json.dumps(inventory,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    write_notice_index(records,python_notice)
    print(f'{len(records)} distributions, {sum(len(p["notices"]) for p in records)} notice files recorded.')


if __name__=='__main__':
    main()
