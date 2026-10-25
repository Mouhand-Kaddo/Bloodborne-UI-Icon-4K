# SPDX-License-Identifier: GPL-2.0-or-later
"""Inventory Icons 4K: native UV correction, first confirmed in gameplay on bbport preview-21
(1.9.7), ported to preview-23 (2.1). Original icon geometry is retained. The hook applies only
when UI 4K's interface archive is the one the game loads.
"""
from pathlib import Path
import re,struct,json,hashlib
VTABLE=0x53aee90-0x4000
SITE=0x1f6263b-0x4000
GET=0x1f64250-0x4000
def parse(data):
    h=list(struct.unpack_from('<8s6Q',data));assert h[0]==b'BBPROBE5'
    size,entry,ns,nr,nn,flags=h[1:];i=56+8+32
    nm=struct.unpack_from('<Q',data,i)[0];i+=8+nm*56
    nb=struct.unpack_from('<Q',data,i)[0];i+=8+nb*24
    extra=data[56:i]
    segments=[struct.unpack_from('<3Q',data,i+j*24) for j in range(ns)];i+=ns*24
    names=data[i:i+nn*128];i+=nn*128
    relocs=[struct.unpack_from('<QQqq',data,i+j*32) for j in range(nr)];i+=nr*32
    image=bytearray(data[i:]);assert len(image)==size
    return h,extra,segments,names,relocs,image

def put_rel(code,base,op,target):
    code.extend(op);code.extend(struct.pack('<i',target-(base+len(code)+4)))

PAGE=0x50da000;DATA=PAGE+4096;UV=PAGE+0x100;FACTOR=PAGE+0x180;TABLE=DATA+0x100
SIGNATURE=b'ICUVLOG1'
NATIVE_VTABLE=0x51bbf20
NATIVE_UV=0x24c33f0

def assembly(heights=(4096,)):
    c=bytearray(bytes.fromhex('4883ec08'));put_rel(c,PAGE,b'\xe8',GET)
    c.extend(bytes.fromhex('4883c4084885c0'));jumps=[]
    def branch(op):c.extend(op);jumps.append(len(c));c.extend(bytes(4))
    branch(b'\x0f\x84')
    c.extend(bytes.fromhex('81782c00100000'));branch(b'\x0f\x85')
    if len(heights)==1:
        c.extend(bytes.fromhex('817830')+struct.pack('<I',heights[0]));branch(b'\x0f\x85')
    else:
        matches=[]
        for height in heights:
            c.extend(bytes.fromhex('817830')+struct.pack('<I',height)+b'\x74')
            matches.append(len(c));c.append(0)
        branch(b'\xe9')
        for at in matches:c[at]=len(c)-at-1
    put_rel(c,PAGE,bytes.fromhex('488d0d'),VTABLE)
    c.extend(bytes.fromhex('483908'));branch(b'\x0f\x85')
    c.extend(bytes.fromhex('488b50104885d2'));branch(b'\x0f\x84')
    c.extend(bytes.fromhex('488b32')) # rsi = original native texture vtable
    put_rel(c,PAGE,bytes.fromhex('488d3d'),TABLE)
    c.extend(bytes.fromhex('4839fe'));branch(b'\x0f\x84')
    put_rel(c,PAGE,bytes.fromhex('488d0d'),NATIVE_VTABLE)
    c.extend(bytes.fromhex('4839ce'));branch(b'\x0f\x85')
    c.extend(bytes.fromhex('488b4e40'))
    put_rel(c,PAGE,bytes.fromhex('4c8d05'),NATIVE_UV)
    c.extend(bytes.fromhex('4c39c1'));branch(b'\x0f\x85')
    put_rel(c,PAGE,bytes.fromhex('48890d'),DATA)
    put_rel(c,PAGE,bytes.fromhex('488935'),DATA+0x68)
    put_rel(c,PAGE,bytes.fromhex('488915'),DATA+0x60)
    c.extend(bytes.fromhex('b940000000f348a5')) # copy 64 qwords; rax image and rdx texture preserved
    put_rel(c,PAGE,bytes.fromhex('488d0d'),UV)
    put_rel(c,PAGE,bytes.fromhex('48890d'),TABLE+0x40)
    put_rel(c,PAGE,bytes.fromhex('488d0d'),TABLE)
    c.extend(bytes.fromhex('48890a'))
    end=len(c);c.append(0xc3)
    for at in jumps:
        struct.pack_into('<i',c,at,end-at-4)
    assert len(c)<0x100
    uv=bytearray(bytes.fromhex('534889f3'))
    put_rel(uv,UV,bytes.fromhex('ff15'),DATA) # call original native Texture::GetUVGenMatrix
    uv.extend(bytes.fromhex('0f1003'))
    put_rel(uv,UV,bytes.fromhex('0f1105'),DATA+0x20)
    uv.extend(bytes.fromhex('0f104b10'))
    put_rel(uv,UV,bytes.fromhex('0f110d'),DATA+0x30)
    put_rel(uv,UV,bytes.fromhex('0f5905'),FACTOR)
    put_rel(uv,UV,bytes.fromhex('0f590d'),FACTOR)
    uv.extend(bytes.fromhex('0f11030f114b10'))
    put_rel(uv,UV,bytes.fromhex('0f1105'),DATA+0x40)
    put_rel(uv,UV,bytes.fromhex('0f110d'),DATA+0x50)
    put_rel(uv,UV,bytes.fromhex('f048ff05'),DATA+8)
    uv.extend(bytes.fromhex('5bc3'));assert len(uv)<0x80
    return bytes(c),bytes(uv)

def build_image(source,dest,sites=None,heights=(4096,)):
    raw=source.read_bytes();h,extra,segments,names,relocs,image=parse(raw)
    if sites is None:sites={SITE:'MENU_Icon_00001'}
    assert any(a==0 and n==84776668 and flags==5 for a,n,flags in segments)
    assert all(PAGE+8192<=a or a+((n+4095)&~4095)<=PAGE for a,n,_ in segments)
    assert image[PAGE:PAGE+8192]==bytes(8192)
    originals={site:bytes(image[site:site+5]) for site in sites}
    for site,old in originals.items():
        assert old[0]==0xe8 and site+5+struct.unpack_from('<i',old,1)[0]==GET
    assert any(t==NATIVE_VTABLE+0x40 and k==0 and v+a==NATIVE_UV for t,k,v,a in relocs)
    c,uv=assembly(heights);image[PAGE:PAGE+len(c)]=c;image[UV:UV+len(uv)]=uv
    image[FACTOR:FACTOR+16]=struct.pack('<4f',4,4,4,1)
    image[DATA+0x80:DATA+0x88]=SIGNATURE
    for site in sites:image[site:site+5]=b'\xe8'+struct.pack('<i',PAGE-(site+5))
    segments.extend([(PAGE,4096,5),(DATA,4096,6)]);h[3]=len(segments)
    out=bytearray(struct.pack('<8s6Q',*h));out.extend(extra)
    for s in segments:out.extend(struct.pack('<3Q',*s))
    out.extend(names)
    for r in relocs:out.extend(struct.pack('<QQqq',*r))
    out.extend(image)
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(out)
    undo=bytearray(parse(out)[5]);undo[PAGE:PAGE+8192]=bytes(8192)
    for site,old in originals.items():undo[site:site+5]=old
    assert undo==parse(raw)[5]
    assert source.read_bytes()==raw
    report=dict(source_sha256=hashlib.sha256(raw).hexdigest(),output_sha256=hashlib.sha256(out).hexdigest(),
                textures=list(sites.values()),hook='Native Texture::GetUVGenMatrix; shared by subimages',
                geometry='Original 80px icon rectangles, source coordinates and game scripts unchanged',
                original_boot_unchanged=True,gameplay_verified=False)
    dest.with_suffix('.json').write_text(json.dumps(report,indent=2));return report

def find_sites(image):
    expected={'MENU_Icon_03001', 'MENU_Icon_00001', 'MENU_Icon_03008', 'MENU_Icon_00002', 'MENU_Icon_06001', 'MENU_Icon_03005', 'MENU_Icon_07001', 'MENU_Icon_03007', 'MENU_Icon_04001', 'MENU_Icon_01001', 'MENU_Icon_02001', 'MENU_Icon_02002', 'MENU_Icon_03002', 'MENU_Icon_03004', 'MENU_Icon_03009', 'MENU_Icon_03003', 'MENU_Icon_04002', 'MENU_Icon_05001', 'MENU_Icon_03006', 'MENU_Icon_00003'}
    sites={}
    # Exact instruction sequence used by the game: lea rsi,name; mov rdi,r12; call GetImage.
    for match in re.finditer(rb'\x48\x8d\x35....\x4c\x89\xe7\xe8',bytes(image),re.DOTALL):
        at=match.start();name_at=at+7+struct.unpack_from('<i',image,at+3)[0]
        if not 0<=name_at<len(image):continue
        name=bytes(image[name_at:name_at+15]).split(b'\0')[0].decode('ascii',errors='replace')
        if name not in expected:continue
        site=at+10
        assert site+5+struct.unpack_from('<i',image,site+1)[0]==GET
        sites[site]=name
    assert len(sites)==20 and set(sites.values())==expected,sites
    return sites

def build(source,dest):
    sites=find_sites(parse(source.read_bytes())[5])
    return build_image(source,dest,sites=sites,heights=(4096,2048,1024,512))


def boot_for_archive(out,game,archive_sha256):
    """The boot image to start: with the UV correction when the merged game view `game` loads
    UI 4K's interface archive (SHA-256 `archive_sha256`, ui4k_assets.prepare), else the port's."""
    original=Path(out)/'boot-linked.bin'
    if not archive_sha256:return original
    common=Path(game)/'dvdroot_ps4/menu/common.tpf.dcx'
    if not common.is_file() or hashlib.sha256(common.read_bytes()).hexdigest()!=archive_sha256:
        print('UI 4K: another mod after UI 4K replaces common.tpf.dcx; the 4x inventory icons and '
              'their correction are not used. Put UI 4K last in the mod order.')
        return original
    target=Path(out)/'boot-inventory-icons.bin'
    build(original,target)
    print('UI 4K: 20 inventory atlases at 4x; native UV correction enabled')
    return target
