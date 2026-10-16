"""Render all three manuscript figures directly from retained inputs."""
import argparse,csv,statistics
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
ROOT=Path(__file__).resolve().parents[1]
plt.rcParams.update({"font.family":"STIXGeneral","font.size":9,"mathtext.fontset":"stix",
                     "pdf.fonttype":42,"ps.fonttype":42,"text.usetex":False})
def save(fig,ax,out,name):
    fig.canvas.draw()
    labels=list(ax.texts)
    if ax.axison:
        labels.extend([ax.xaxis.label,ax.yaxis.label])
        labels.extend(t.label1 for t in ax.xaxis.get_major_ticks()
                      if ax.get_xlim()[0]<=t.get_loc()<=ax.get_xlim()[1])
        labels.extend(t.label1 for t in ax.yaxis.get_major_ticks()
                      if ax.get_ylim()[0]<=t.get_loc()<=ax.get_ylim()[1])
    for label in labels:
        if not label.get_visible() or not label.get_text():continue
        box=label.get_window_extent()
        if box.x0<fig.bbox.x0-1 or box.y0<fig.bbox.y0-1 or box.x1>fig.bbox.x1+1 or box.y1>fig.bbox.y1+1:
            raise ValueError("Label outside canvas: "+label.get_text())
    fig.savefig(out/name,metadata={"CreationDate":None,"ModDate":None})
    plt.close(fig)
def support(out):
    fig,ax=plt.subplots(figsize=(5.9,2.55))
    fig.subplots_adjust(left=.01,right=.99,bottom=.02,top=.98)
    ax.set(xlim=(0,6),ylim=(0,2.55));ax.set_axis_off()
    boxes=[(1.45,1.75,3.1,.65,"$S_t(k)=\\varnothing$\nChallenge: return $\\pi$, cost 0"),
           (.12,.12,2.45,.62,"$R_k=\\{0\\}$\nWitness $p_0$: cost 1"),
           (3.43,.12,2.45,.62,"$R_k=\\{1\\}$\nWitness $p_1$: cost 1")]
    for x,y,w,h,text in boxes:
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=.03",
                                   facecolor="white",edgecolor="black",lw=.8))
        ax.text(x+w/2,y+h/2,text,ha="center",va="center")
    for end,label,x in [((1.35,.78),"Choose 0",1.55),((4.65,.78),"Choose 1",4.45)]:
        ax.add_patch(FancyArrowPatch((3,1.71),end,arrowstyle="-|>",mutation_scale=9,lw=.8))
        ax.text(x,1.3,label,ha="center",va="center")
    save(fig,ax,out,"support-cover.pdf")
def encoding(out):
    with (ROOT/"results/current/encoding-scaling.csv").open(newline="",encoding="utf-8") as stream:
        rows=list(csv.DictReader(stream))
    if [int(r["horizon"]) for r in rows]!=list(range(1,13)):
        raise ValueError("Unexpected horizon census")
    if any(int(r[k])<=0 for r in rows for k in ("explicit_bytes","input_bytes","compact_bytes")):
        raise ValueError("Nonpositive byte count")
    fig,ax=plt.subplots(figsize=(5.93,2.36))
    fig.subplots_adjust(left=.12,right=.98,bottom=.23,top=.96)
    for key,label,marker,style in [("explicit_bytes","Explicit trace certificate","o","-"),
           ("input_bytes","Expanded graph input","s","--"),("compact_bytes","One-attempt certificate","^",":")]:
        ax.plot([int(r["horizon"]) for r in rows],[int(r[key]) for r in rows],
                label=label,marker=marker,linestyle=style,color="black",markersize=3,
                markerfacecolor="white",linewidth=.8)
    ax.set(yscale="log",ylim=(10**1.5,10**6.25),xlim=(1,12),xticks=[1,2,4,6,8,10,12],
           xlabel="Source horizon H",ylabel="Serialized bytes")
    ax.grid(color=".87",linewidth=.4);ax.set_axisbelow(True)
    ax.legend(loc="upper left",fontsize=8,framealpha=1,edgecolor="none")
    save(fig,ax,out,"encoding-scaling.pdf")
def costs(out):
    with (ROOT/"results/required/paired-costs.csv").open(newline="",encoding="utf-8") as stream:
        rows=list(csv.DictReader(stream))
    if len(rows)!=93:raise ValueError("Expected all 93 paired medians")
    fig,ax=plt.subplots(figsize=(5.93,2.36))
    fig.subplots_adjust(left=.13,right=.98,bottom=.20,top=.96)
    for center,mode,count in [(1,"collapse",31),(2,"distance",15),(3,"rank",47)]:
        values=sorted(float(r["certificate_over_ordinary"]) for r in rows if r["mode"]==mode)
        if len(values)!=count or not all(10**-1.5<v<10**.4 for v in values):
            raise ValueError("Mode census or axis bounds changed")
        xs=[center-.33+.66*i/max(1,len(values)-1) for i in range(len(values))]
        ax.scatter(xs,values,s=10,facecolors="white",edgecolors="black",linewidths=.5,zorder=3)
        ax.plot([center-.35,center+.35],[statistics.median(values)]*2,color="black",linewidth=1.2)
    ax.set(yscale="log",ylim=(10**-1.5,10**.4),xlim=(.45,3.55),
           xticks=[1,2,3],xticklabels=["Collapse (31)","Distance (15)","Rank (47)"],
           ylabel="Paired median total-time ratio")
    ax.set_yticks([.05,.1,.25,.5,1,2],labels=["0.05","0.1","0.25","0.5","1","2"])
    ax.grid(axis="y",color=".87",linewidth=.4);ax.axhline(1,color=".4",linewidth=.8)
    save(fig,ax,out,"required-costs.pdf")
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("--outdir",type=Path,default=Path(__file__).resolve().parent)
    args=ap.parse_args();args.outdir.mkdir(parents=True,exist_ok=True)
    support(args.outdir);encoding(args.outdir);costs(args.outdir)
    print("Three direct vector PDFs; 12 retained scaling rows and all 93 paired medians.")
if __name__=="__main__":main()
