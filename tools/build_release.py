"""Create the complete portable release ZIP and a source-only GitHub upload ZIP."""
from pathlib import Path
import hashlib,json,zipfile,sys,re
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
    for entry in manifest['files']:
        path=ROOT/entry['source']
        assert path.is_file() and sha(path)==entry['sha256'],entry['source']
    for path in (ROOT/'integration').glob('*.py'):compile(path.read_text(encoding='utf-8'),str(path),'exec')
    for readme in ('README.md','README.ru.md'):
        text=(ROOT/readme).read_text(encoding='utf-8')
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if '://' not in target and not target.startswith('#'):
                assert (ROOT/target.split('#')[0]).is_file(),(readme,target)
    report=json.loads((ROOT/'tests/last-results.json').read_text())
    assert report['passed'] and not report['game_started']
    dist=ROOT/'dist';dist.mkdir(exist_ok=True)
    paths=[]
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file():continue
        rel=path.relative_to(ROOT)
        if rel.parts[0] in ('build','dist','.git') or '__pycache__' in rel.parts or path.suffix=='.pyc':continue
        paths.append((path,rel))
    names=[]
    for source_only,name in [(False,f'Bloodborne-UI-4K-v{manifest["version"]}.zip'),
                              (True,f'Bloodborne-UI-4K-v{manifest["version"]}-github-source.zip')]:
        output=dist/name
        with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for path,rel in paths:
                if source_only and rel.parts[0]=='payload':continue
                z.write(path,(Path('Bloodborne-UI-4K')/rel).as_posix())
        with zipfile.ZipFile(output) as z:
            assert z.testzip() is None
            if not source_only:
                for entry in manifest['files']:
                    assert hashlib.sha256(z.read('Bloodborne-UI-4K/'+entry['source'])).hexdigest()==entry['sha256']
        names.append(name)
        print(name,round(output.stat().st_size/1048576,2),'MiB')
    sums=''.join(sha(dist/name)+'  '+name+'\n' for name in names)
    (dist/'SHA256SUMS.txt').write_text(sums,encoding='ascii')
    print('Both ZIPs and every release payload member passed verification.')
if __name__=='__main__':main()
