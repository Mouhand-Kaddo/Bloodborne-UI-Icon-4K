"""Render honest, equal-size comparisons from decoded source/final DDS textures.
Requires Pillow only for maintainers; the installer does not use this script.
"""
from pathlib import Path
import argparse,json
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
FONT=Path('C:/Windows/Fonts/segoeui.ttf')
def font(size):return ImageFont.truetype(str(FONT),size)
def flattened(im):
    result=Image.new('RGBA',im.size,(18,21,24,255));result.alpha_composite(im.convert('RGBA'));return result.convert('RGB')
def sheet(rows,title,path):
    # Both columns show exactly the same source region and the same final display size.
    width=1000;rowheight=390
    canvas=Image.new('RGB',(width,140+rowheight*len(rows)),(16,19,23));d=ImageDraw.Draw(canvas)
    d.text((28,18),title,font=font(28),fill='#f0eee8')
    d.text((28,65),'BEFORE / ДО',font=font(21),fill='#bdc5cf')
    d.text((520,65),'AFTER / ПОСЛЕ',font=font(21),fill='#b8dca8')
    d.text((28,104),'Texture comparison - not an in-game screenshot',font=font(16),fill='#929aa4')
    meta=[]
    for index,(name,before,after,box,factor) in enumerate(rows):
        original=before.crop(box);scaled=after.crop(tuple(v*factor for v in box))
        display=(400,300)
        # Contain both crops at the same aspect ratio, no additional sharpening.
        ratio=min(display[0]/original.width,display[1]/original.height)
        size=(round(original.width*ratio),round(original.height*ratio))
        a=original.resize(size,Image.Resampling.BILINEAR)
        b=scaled.resize(size,Image.Resampling.BILINEAR) if scaled.size!=size else scaled
        y=145+index*rowheight
        for x,im in [(28,a),(520,b)]:
            canvas.paste(flattened(im),(x,y));d.rectangle((x-1,y-1,x+size[0],y+size[1]),outline='#343b44')
        d.text((28,y+310),name,font=font(19),fill='#eeeeee')
        d.text((28,y+342),f'{original.width} x {original.height} source; bilinear enlargement',font=font(15),fill='#929aa4')
        d.text((520,y+342),f'{scaled.width} x {scaled.height} upscaled texture crop',font=font(15),fill='#929aa4')
        meta.append(dict(texture=name,source_crop=list(box),factor=factor,baseline_filter='bilinear',display_size=list(size)))
    canvas.save(path,optimize=True)
    return meta
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--icons-work',type=Path,required=True);ap.add_argument('--previous-ui',type=Path,required=True)
    args=ap.parse_args();out=ROOT/'docs/images';out.mkdir(parents=True,exist_ok=True)
    report={}
    before=Image.open(args.icons_work/'atlas-png/MENU_Icon_00001.png').convert('RGBA')
    after=Image.open(args.icons_work/'all-tpf/MENU_Icon_00001.dds').convert('RGBA')
    rows=[('MENU_Icon_00001: cell 24',before,after,(0,160,80,240),4),
          ('MENU_Icon_00001: cell 21',before,after,(720,80,800,160),4),
          ('MENU_Icon_00001: cell 11',before,after,(880,0,960,80),4)]
    report['inventory-consumables.png']=sheet(rows,'Inventory icons / Иконки предметов',out/'inventory-consumables.png')
    rows=[]
    for name in ('MENU_Icon_02001','MENU_Icon_03001','MENU_Icon_04001'):
        a=Image.open(args.icons_work/('atlas-png/'+name+'.png')).convert('RGBA')
        b=Image.open(args.icons_work/('all-tpf/'+name+'.dds')).convert('RGBA')
        # Select the first occupied 80px cell, without inferring its item identity.
        box=None
        for y in range(0,a.height-79,80):
            for x in range(0,a.width-79,80):
                tile=a.crop((x,y,x+80,y+80))
                if sum(tile.getchannel('A').histogram()[64:])>2500:
                    box=(x,y,x+80,y+80);break
            if box:break
        assert box,name
        rows.append((name,a,b,box,4))
    report['inventory-more.png']=sheet(rows,'More inventory atlases / Другие атласы',out/'inventory-more.png')
    # Original earlier comparison: preserve its actual picture pixels, replace only its old test heading.
    previous=Image.open(args.previous_ui).convert('RGB')
    picture=previous.crop((0,58,previous.width,previous.height))
    canvas=Image.new('RGB',(previous.width,picture.height+105),(16,19,23));canvas.paste(picture,(0,105));d=ImageDraw.Draw(canvas)
    d.text((18,12),'UI decorations / Декор интерфейса',font=font(28),fill='white')
    d.text((18,59),'BEFORE / ДО',font=font(23),fill='#bdc5cf')
    d.text((previous.width//2+18,59),'AFTER / ПОСЛЕ',font=font(23),fill='#b8dca8')
    canvas.save(out/'ui-decorations.png',optimize=True)
    report['ui-decorations.png']={'source':'Previously generated source/final PS4 texture comparison; original image pixels preserved below the headings.'}
    (out/'comparison-method.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Rendered 3 comparison sheets from real source/final texture crops.')
if __name__=='__main__':main()
