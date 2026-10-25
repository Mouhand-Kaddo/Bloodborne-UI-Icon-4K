"""Integration tests against Windows PowerShell 5.1 and genuine upstream files.
No game is launched. Fixtures are ordinary copies, not links to game data.
Usage: python tests/test_installer.py --probe PATH_TO_STOCK_bb-probe.exe
"""
from pathlib import Path
import argparse,subprocess,hashlib,shutil,json,tempfile,os
ROOT=Path(__file__).resolve().parents[1]
PS=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
def hashes(folder):
    return {p.relative_to(folder).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--probe',type=Path,required=True);args=ap.parse_args()
    results=[]
    (ROOT/'build').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='bbport-ui4k-',dir=ROOT/'build') as temp:
        work=Path(temp);target=work/'Clean bbport Unicode \u041a\u0438\u0440\u0438\u043b\u043b'
        (target/'scripts').mkdir(parents=True);(target/'bin').mkdir()
        shutil.copyfile(ROOT/'upstream/run.py',target/'run.py')
        shutil.copyfile(ROOT/'upstream/patches.py',target/'scripts/patches.py')
        shutil.copyfile(args.probe,target/'bin/bb-probe.exe')
        (target/'Bloodborne.exe').write_bytes(b'MZ fixture marker; never executed')
        # Prompt mods as the launcher adds them; both must stay as the player chose.
        for name in ('Xbox 360 Prompts (Elden Ring)','Keyboard Prompts (PCBButtons)'):
            (target/'mods'/name/'menu').mkdir(parents=True)
            (target/'mods'/name/'menu/common.tpf.dcx').write_bytes(name.encode())
        (target/'mods.json').write_text(json.dumps({'enabled':['Other Mod'],'disabled':['Keyboard Prompts (PCBButtons)'],
                                                  'order':['Other Mod'],'custom_setting':42}),encoding='utf-8')
        baseline=hashes(target)
        def action(name,okay=True):
            run=subprocess.run([str(PS),'-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'installer/setup.ps1'),
                                '-NoGui','-Action',name,'-Target',str(target)],capture_output=True)
            if (run.returncode==0)!=okay:
                raise AssertionError((name,run.returncode,run.stdout.decode(errors='replace'),run.stderr.decode(errors='replace')))
            return run
        def readiness(path=None):
            run=subprocess.run([str(PS),'-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'installer/setup.ps1'),
                                '-NoGui','-Action','Validate','-Target',str(path or target)],capture_output=True)
            assert run.returncode==0,(run.stdout,run.stderr)
            return json.loads(run.stdout.decode('utf-8-sig'))
        assert readiness()['ready'] and readiness()['mode']=='Install'
        assert hashes(target)==baseline # the temporary access probe must be removed
        assert not readiness(work/'missing folder')['ready']
        empty=work/'wrong folder';empty.mkdir();assert not readiness(empty)['ready']
        action('Install');action('Verify');action('Install')
        assert readiness()['ready'] and readiness()['mode']=='Installed'
        config=json.loads((target/'mods.json').read_text())
        assert config['order']==['Other Mod','Keyboard Prompts (PCBButtons)','Xbox 360 Prompts (Elden Ring)','UI 4K'],config
        assert config['disabled']==['Keyboard Prompts (PCBButtons)'],config
        assert (target/'mods/UI 4K/dvdroot_ps4/menu').is_dir()
        # Files the launch helper makes, listed in its stamp, go with the package.
        made=target/'mods/UI 4K/dvdroot_ps4/menu'
        (made/'common.tpf.dcx').write_bytes(b'made at launch');(made/'title.gfx').write_bytes(b'made at launch')
        (made/'title.gfx.ui4k-tmp').write_bytes(b'interrupted')
        (target/'mods/UI 4K/ui4k/generated.json').write_text(json.dumps({'identity':'test','files':{
            'dvdroot_ps4/menu/common.tpf.dcx':{},'dvdroot_ps4/menu/title.gfx':{}}}),encoding='utf-8')
        action('Verify')
        action('Uninstall');assert hashes(target)==baseline,set(hashes(target))^set(baseline)
        assert not (target/'mods/UI 4K').exists()
        results.append('clean install, verify, repeat install, exact uninstall restore incl. files made at launch; '
                       'UI 4K ordered last, prompt mods kept as chosen; spaces and Cyrillic paths')
        # A modified upstream script must be rejected without changing any target files.
        original=(target/'run.py').read_bytes();(target/'run.py').write_bytes(original+b'\n# unknown edit\n')
        before=hashes(target);action('Install',False);assert hashes(target)==before
        assert not readiness()['ready']
        (target/'run.py').write_bytes(original);results.append('unsupported installation rejected before mutation')
        # A damaged payload must fail preflight, without creating backup state.
        module=ROOT/'integration/inventory_icons.py';raw=module.read_bytes()
        try:
            module.write_bytes(raw+b'\n');action('Install',False);assert hashes(target)==baseline
            assert not readiness()['ready']
        finally:module.write_bytes(raw)
        results.append('corrupted payload rejected before mutation')
        # Verify refusal to overwrite a later user edit during uninstall.
        action('Install');installed=(target/'run.py').read_bytes()
        (target/'run.py').write_bytes(installed+b'\n# keep this edit\n')
        before=hashes(target);action('Uninstall',False);assert hashes(target)==before
        (target/'run.py').write_bytes(installed)
        config=json.loads((target/'mods.json').read_text());config['enabled'].append('Later Mod');config['order'].append('Later Mod')
        (target/'mods.json').write_text(json.dumps(config),encoding='utf-8')
        action('Uninstall');restored=json.loads((target/'mods.json').read_text())
        assert 'Later Mod' in restored['enabled'] and 'Other Mod' in restored['enabled'] and restored['custom_setting']==42
        assert 'UI 4K' not in restored['enabled'] and 'UI 4K' not in restored['order']
        (target/'mods.json').write_text(json.dumps({'enabled':['Other Mod'],'disabled':['Keyboard Prompts (PCBButtons)'],
                                                  'order':['Other Mod'],'custom_setting':42}),encoding='utf-8')
        assert hashes(target)==baseline
        results.append('uninstall protects user edits and preserves later unrelated mod choices')
        # Inject a final verification failure in a test-only session: exercise full rollback.
        fault=work/'rollback.ps1'
        fault.write_text("param([string]$Engine,[string]$Target)\n. $Engine\nfunction Test-Installation([string]$Target) {throw 'Injected final verification failure'}\ntry {Install-Package $Target;exit 99} catch {exit 0}\n",encoding='ascii')
        run=subprocess.run([str(PS),'-NoProfile','-ExecutionPolicy','Bypass','-File',str(fault),
                            '-Engine',str(ROOT/'installer/engine.ps1'),'-Target',str(target)],capture_output=True)
        assert run.returncode==0,(run.stdout,run.stderr)
        assert hashes(target)==baseline
        results.append('post-copy failure restores exact original files and configuration')
        # Reject a manifest traversal before any write.
        manifest=ROOT/'manifest.json';raw=manifest.read_bytes()
        try:
            data=json.loads(raw);data['files'][0]['target']='../escape.py'
            manifest.write_text(json.dumps(data),encoding='utf-8');action('Install',False);assert hashes(target)==baseline
        finally:manifest.write_bytes(raw)
        results.append('manifest path traversal rejected')
        # Windows distributions may use CRLF/BOM, and a first install may have no mods.json.
        (target/'mods.json').unlink()
        for relative in ('run.py','scripts/patches.py'):
            p=target/relative;text=p.read_text(encoding='utf-8-sig')
            p.write_bytes(b'\xef\xbb\xbf'+text.replace('\n','\r\n').encode('utf-8'))
        clean_windows=hashes(target)
        action('Install');action('Uninstall');assert hashes(target)==clean_windows
        results.append('UTF-8 BOM, Windows CRLF, missing mods.json; exact byte restoration')
        # A 1.0.0 (bbport 1.9.7) folder left in place is reported, not merged.
        (target/'mods/Inventory Icons 4K').mkdir();before=hashes(target)
        action('Install',False);assert hashes(target)==before and not readiness()['ready']
        (target/'mods/Inventory Icons 4K').rmdir()
        results.append('leftover 1.0.0 mod folder rejected before mutation')
        source=(ROOT/'installer/setup.ps1').read_text(encoding='utf-8')
        assert 'MessageBox' not in source and '$verify' not in source
        results.append('automatic folder preflight: valid, missing, wrong, modified, corrupt payload and already-installed states; no validation residue or popup code')
    report={'passed':True,'runtime':'Windows PowerShell 5.1','game_started':False,'checks':results}
    (ROOT/'tests/last-results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
