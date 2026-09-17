"""Paper figure for the implemented FullStackFlow (vector PDF/SVG + PNG).

Run with a Python environment containing Matplotlib. SVG preserves text objects;
PDF embeds TrueType fonts. No network or LLM calls are made.
"""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.path import Path as MPath

OUT = Path(__file__).resolve().parent
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                     'pdf.fonttype': 42, 'ps.fonttype': 42, 'svg.fonttype': 'none'})
INK = '#223044'; MUTED = '#536174'; BLUE = '#2E5B85'; BLUE_FILL = '#EAF2F8'
GRAY = '#718096'; TOOL_FILL = '#F2F4F6'; PURPLE = '#775095'; ORANGE = '#A56520'
GREEN = '#327263'; GREEN_FILL = '#EAF4EF'; WHITE = 'white'
fig, ax = plt.subplots(figsize=(12.6, 6.35))
ax.set(xlim=(0, 18.2), ylim=(0, 9.15)); ax.axis('off')
fig.subplots_adjust(left=0.012, right=0.992, bottom=0.012, top=0.99)


def text(x, y, s, size=11, color=INK, weight='normal', ha='center', **kw):
    return ax.text(x, y, s, fontsize=size * 1.16, color=color, weight=weight,
                   ha=ha, va='center', linespacing=1.35, zorder=6, **kw)


def box(x, y, w, h, title, body='', edge=BLUE, fill=BLUE_FILL, title_size=12.3, body_size=10.4):
    p = FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.018,rounding_size=0.08',
                      facecolor=fill, edgecolor=edge, linewidth=1.1, zorder=3)
    ax.add_patch(p)
    if body:
        text(x+w/2, y+h*0.76, title, title_size, edge, 'bold')
        text(x+w/2, y+h*0.34, body, body_size)
    else:
        text(x+w/2,y+h/2,title,title_size,edge,'bold')
    return p


def arrow(points, color=INK, style='-', width=1.25, head=10, z=2):
    path=MPath(points, [MPath.MOVETO]+[MPath.LINETO]*(len(points)-1))
    p=FancyArrowPatch(path=path,arrowstyle='-|>',mutation_scale=head,
                      linewidth=width,color=color,linestyle=style,
                      joinstyle='round',capstyle='round',zorder=z)
    ax.add_patch(p)


def label(x,y,s,color=MUTED,size=9.5):
    return text(x,y,s,size,color,bbox=dict(facecolor='white',edgecolor='none',pad=1.4))

# User-owned inputs: the library has no incoming write path.
box(.6,7.48,2.55,1.43,'Task','Algorithm + inputs\nQuality, area, clock\nSearch budget',GRAY,'#FAFAFB',11.5,9.9)
box(3.6,7.48,13.95,1.43,'Read-only reference library',
    'Trusted algorithm contracts + independent golden     |     Hardware IP + reference testbenches',GRAY,'#FAFAFB',12.3,10.8)
# Read-only material feeds; golden is not authored by a design agent.
arrow([(1.35,7.48),(1.35,6.20)],GRAY,':',1.3)
arrow([(4.0,7.48),(4.0,7.05),(2.10,7.05),(2.10,6.20)],GRAY,':',1.3)
arrow([(5.75,7.48),(5.75,6.98),(4.25,6.98),(4.25,6.20)],GRAY,':',1.3)
arrow([(14.12,7.48),(14.12,6.20)],GRAY,':',1.3)
label(14.12,6.97,'Independent golden',GRAY,9.5)

# Main pipeline: only accepted module artifacts can reach assembly.
box(.6,4.8,2.35,1.4,'Kernel Agent','Profile sparsity\nSelect config')
box(3.55,4.8,2.65,1.4,'Compiler Agent','Interfaces + tests\nReference binding',body_size=10.2)
# Module sessions are a family of isolated jobs, not a claim of concurrent execution.
outer=FancyBboxPatch((6.8,4.18),3.15,2.28,boxstyle='round,pad=0.02,rounding_size=0.09',
                     facecolor='#FCFDFE',edgecolor='#B6C4D1',linewidth=1.0,zorder=1)
ax.add_patch(outer)
box(7.13,5.63,2.55,.58,'',fill='#F5F8FB',edge='#ACC1D1')
box(7.04,5.54,2.55,.58,'',fill='#F0F5F9',edge='#ACC1D1')
box(6.96,5.37,2.55,.73,'Module UArch $i$','Chisel / Verilog',title_size=11.4,body_size=9.8)
box(6.96,4.42,2.55,.65,'Module check','Elaborate / Verilator',GRAY,TOOL_FILL,10.7,9.3)
arrow([(8.23,5.37),(8.23,5.07)])
text(8.36,3.98,'DAG dispatch · serial default',9.4,MUTED)
box(10.5,4.8,2.20,1.4,'Assembly UArch','Connect modules\nElaborate top',title_size=9.9,body_size=10)
box(13.25,4.8,1.95,1.4,'System E2E','Output + mask\nMeasured cycles',GRAY,TOOL_FILL,11.1,9.9)
box(15.78,4.8,1.77,1.4,'Hammer PPA','Yosys\nOpenROAD',GRAY,TOOL_FILL,10.2,9.5)
arrow([(2.95,5.50),(3.55,5.50)])
arrow([(6.20,5.73),(6.96,5.73)])
arrow([(9.55,4.75),(10.18,4.75),(10.18,5.50),(10.5,5.50)])
label(10.17,5.15,'Pass',size=9)
arrow([(12.70,5.50),(13.25,5.50)])
arrow([(15.20,5.50),(15.78,5.50)])
label(15.49,5.15,'Pass',size=9)

# Bounded local repairs. Escalation belongs to Compiler diagnosis, not Critic.
arrow([(6.96,4.72),(6.61,4.72),(6.61,5.73),(6.96,5.73)],ORANGE,'--',1.2,9,z=4)
label(6.50,4.31,'Fail: repair',ORANGE,8.8)
box(6.86,2.04,3.18,1.18,'Compiler diagnosis','Inspect failures\nRepair or request replan',ORANGE,'#FFF6E9',11.4,10.1)
arrow([(7.50,4.42),(7.50,3.22)],ORANGE,'--',1.2,9)
label(8.0,3.57,'Repeated / contract failures',ORANGE,9)
arrow([(6.86,2.70),(4.92,2.70),(4.92,4.80)],ORANGE,'--',1.2,9)
label(5.12,3.40,'Replan',ORANGE,9.5)
arrow([(6.46,2.70),(6.46,5.18),(6.61,5.18)],ORANGE,'--',1.2,9)
ax.plot(6.46,2.70,'o',ms=3,color=ORANGE,zorder=4)
label(6.43,3.16,'Repair',ORANGE,9)
# System failure returns to the assembly worker. Planner diagnosis supplies repairs.
arrow([(13.93,4.80),(13.93,3.78),(11.80,3.78),(11.80,4.80)],ORANGE,'--',1.2,9)
label(12.92,3.78,'Fail: repair assembly',ORANGE,9)
arrow([(10.90,4.80),(10.90,3.46),(9.50,3.46),(9.50,3.22)],ORANGE,'--',1.2,9)
arrow([(10.04,2.82),(11.20,2.82),(11.20,4.80)],ORANGE,'--',1.2,9)
label(10.61,3.13,'Repair',ORANGE,9)

# Complete physical measurements trigger cross-layer optimization.
box(11.87,1.76,2.90,1.25,'Critic Agent','Attribute bottlenecks\nChoose intervention',PURPLE,'#F2EDF7',12.0,10.4)
arrow([(16.66,4.80),(16.66,3.55),(13.32,3.55),(13.32,3.01)])
label(15.52,3.55,'Complete PPA',size=9.4)
box(15.38,1.76,2.17,1.25,'Pareto set','Latency ↓\nQueries/J ↑',GREEN,GREEN_FILL,10.8,10.0)
arrow([(14.77,2.37),(15.38,2.37)])
label(15.11,3.24,'Stop / budget',size=9)

# One outer feedback rail with explicit, independent K/C/U re-entry targets.
arrow([(12.72,1.76),(12.72,.85),(.22,.85),(.22,6.64),(8.80,6.64),(8.80,6.22)],PURPLE,(0,(5,3)),1.55,10)
arrow([(2.65,6.64),(2.65,6.20)],PURPLE,(0,(5,3)),1.55,10)
arrow([(5.80,6.64),(5.80,6.20)],PURPLE,(0,(5,3)),1.55,10)
for x in [2.65,5.8]: ax.plot(x,6.64,'o',ms=3.1,color=PURPLE,zorder=5)
label(3.95,6.65,'Selective re-entry',PURPLE,10.2)
label(6.54,.85,'Cross-layer optimization: Kernel / Compiler / UArch',PURPLE,11)

# Small method legend and persistent provenance strip.
for x,color,style,caption in [(.65,INK,'-','Design / evidence'),(4.52,GRAY,':','Read-only reference'),
                               (8.67,ORANGE,'--','Local repair / replan'),(13.18,PURPLE,(0,(5,3)),'Optimization feedback')]:
    ax.plot([x,x+.50],[.30,.30],color=color,ls=style,lw=1.35)
    text(x+.62,.30,caption,9.1,MUTED,ha='left')
label(8.80,1.32,'FullStackFlow: bounded attempts · reference/source hashes · complete execution records',MUTED,9.4)

for fmt in ['pdf','svg','png']:
    fig.savefig(OUT/f'fast_agentflow.{fmt}',dpi=300,facecolor='white',bbox_inches='tight',pad_inches=.06)
plt.close(fig)
print(OUT/'fast_agentflow.pdf')
