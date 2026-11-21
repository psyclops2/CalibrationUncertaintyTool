"""Rebuild all current samples, or check the generated deliverables."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.utils.project_io import read_project


def check_deliverables():
    for area, count in (('ea402', 14), ('gum', 8), ('euramet19', 2)):
        base = ROOT / 'examples' / area
        projects = sorted((base / 'projects').glob('*.cutp'))
        assert len(projects) == count, (area, len(projects))
        for path in projects:
            project = read_project(path)
            assert project['model_notation'] == 'workbench', path
            assert project['result_variables'], path
            from src.utils.value_references import is_constant_reference
            refs = project.get('value_references') or {}
            assert all('parameter_setup' in rule for rule in refs.get('rules', {}).values()), path
            assert all(is_constant_reference(refs, ident) for ident in refs.get('values', {})), path
            if area == 'euramet19':
                assert len(project['image_assets']) >= 2, path
        # Check generated indexes and documentation, without following remote URLs.
        for path in [*base.rglob('*.md'), *base.joinpath('reports').glob('*.html')]:
            content = path.read_text(encoding='utf-8')
            links = (re.findall(r'href="([^"]+)"', content) if path.suffix == '.html'
                     else re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)', content))
            for link in links:
                if ':' in link or link.startswith('#'):
                    continue
                assert (path.parent / link.split('#')[0]).exists(), (path, link)
        print(f'{area}: {count} .cutp projects and local links checked', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    if not args.check_only:
        env = dict(os.environ, QT_QPA_PLATFORM='offscreen', PYTHONUTF8='1')
        commands = [
            ['-m', 'src.i18n.generate_translations'],
            ['examples/ea402/scripts/verify_improvements.py'],
            ['examples/ea402/scripts/verify_references.py'],
            ['examples/gum/scripts/verify_workflow.py'],
            ['examples/euramet19/scripts/build_samples.py'],
            ['examples/voltage_comparison/build_sample.py'],
            ['examples/check_formula_ui.py'],
            ['examples/audit_numerics.py'],
            ['examples/diagnose_sources.py'],
        ]
        for command in commands:
            subprocess.run([sys.executable, *command], cwd=ROOT, env=env, check=True)
    check_deliverables()
    from examples.check_presentation import check
    check()


if __name__ == '__main__':
    main()
