"""Plot measured placement and pad geometry; no inferred wiring or copper."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/placement'
data=json.loads((OUT/'inventory.json').read_text())
colors=['#157c89','#9264af','#b6781f','#cf5c5c','#398b60','#657b9c','#aa6c95','#5f8c23','#a7734c','#547b81','#805848','#726ca9']
for board,records in data.items():
    fig,ax=plt.subplots(figsize=(10,15.5))
    fig.patch.set_facecolor('#f7f8fa');ax.set_facecolor('#f7f8fa')
    ax.add_patch(Rectangle((20,20),120,200,facecolor='#f2f6ef',edgecolor='#1a2734',linewidth=1.8))
    sheets=sorted({r['sheet'] for r in records});color={s:colors[i%len(colors)] for i,s in enumerate(sheets)}
    for r in records:
        x0,y0,x1,y1=r['box'];c=color[r['sheet']]
        ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,edgecolor=c,facecolor=c+'20',linewidth=.55))
        for p in r['pads']:
            w,h=p['size'];ang=r['angle']%180
            if ang==90:w,h=h,w
            ax.add_patch(Rectangle((p['x']-w/2,p['y']-h/2),w,h,facecolor='#bb9b52',edgecolor='#785e30',linewidth=.1))
            if p['drill'][0]:ax.add_patch(Circle((p['x'],p['y']),p['drill'][0]/2,facecolor='white',edgecolor='#45525a',linewidth=.25))
        ax.text((x0+x1)/2,(y0+y1)/2,r['ref'],fontsize=4.5 if r['ref'].startswith(('C','R','TP')) else 6,
                ha='center',va='center',color='#142531',weight='bold',bbox={'facecolor':'white','alpha':.65,'edgecolor':'none','pad':.2})
    ax.set_xlim(7,153);ax.set_ylim(231,12);ax.set_aspect('equal')
    ax.set_xticks(range(20,141,10));ax.set_yticks(range(20,221,10));ax.grid(alpha=.13)
    ax.set_xlabel('mm — assembled top-view coordinates');ax.set_ylabel('mm')
    title='CONTROLLER — outward top face' if board=='controller' else 'CARRIER — bottom components shown through board'
    ax.set_title(title+'\n120 × 200 mm  |  placement only  |  no routed copper',loc='left',fontsize=13,pad=15)
    fig.tight_layout();fig.savefig(OUT/(board+'_placement.png'),dpi=220);plt.close(fig)
print('Placement review PNGs saved.')
