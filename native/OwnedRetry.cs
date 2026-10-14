// Complete owned bounded interpreter, not an external retriever or AOT proof.
// Standard .NET Framework compiler; no networking, unmanaged code or packages.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Web.Script.Serialization;

public static class OwnedRetry {
  sealed class Outcome { public int Add; public string Failure; }
  sealed class Packet {
    public string Tag; public int Evidence; public int[] Cost;
    public bool Matches(Packet target) {
      if (Tag != target.Tag || Evidence != target.Evidence) return false;
      for(int j=0;j<Cost.Length;j++) if(Cost[j]<target.Cost[j]) return false;
      return true;
    }
  }
  static object[] Array(object x) { return (object[])x; }
  static int Number(object x) { return Convert.ToInt32(x); }
  static int[] Numbers(object x) { return System.Array.ConvertAll(Array(x),Number); }
  static Dictionary<string,object> Object(object x) { return (Dictionary<string,object>)x; }
  static List<Packet> Execute(int initial,Outcome[] oo,int R,int[] feedback,int H,int[] q,int[] b) {
    var active=new HashSet<int>(); active.Add(initial); var done=new List<Packet>();
    for(int step=1;step<=H;step++) {
      var next=new HashSet<int>(); var unique=new HashSet<string>();
      foreach(int owned in active) for(int i=0;i<oo.Length;i++) if((R&(1<<i))!=0) {
        Outcome o=oo[i]; int e=owned|o.Add; var cost=new int[q.Length];
        for(int j=0;j<q.Length;j++) cost[j]=step*q[j]+(o.Failure==null?step:step-1)*b[j];
        var tags=new List<string>();
        if(o.Failure!=null) tags.Add("fail:"+o.Failure);
        else {
          if((feedback[e]&2)!=0) tags.Add("ok");
          if((feedback[e]&1)!=0) { if(step==H)tags.Add("exhausted");else next.Add(e); }
        }
        foreach(string tag in tags) {
          string key=tag+"/"+e+"/"+String.Join(",",cost);
          if(unique.Add(key))done.Add(new Packet { Tag=tag,Evidence=e,Cost=cost });
        }
      }
      active=next;
    }
    return done;
  }
  static bool Relation(List<Packet> source,List<Packet> target) {
    foreach(Packet t in target) { bool found=false;foreach(Packet s in source)if(s.Matches(t)){found=true;break;}if(!found)return false; }
    foreach(Packet s in source) { bool found=false;foreach(Packet t in target)if(s.Matches(t)){found=true;break;}if(!found)return false; }
    return true;
  }
  static IEnumerable<int[]> Feedback(int[] allowed,int index,int[] current) {
    if(index==allowed.Length) {yield return (int[])current.Clone();yield break;}
    for(int v=1;v<=3;v++)if((v&~allowed[index])==0){current[index]=v;foreach(var b in Feedback(allowed,index+1,current))yield return b;}
  }
  public static int Main(string[] args) {
    if(args.Length!=2 && args.Length!=3){Console.Error.WriteLine("cases.jsonl output.jsonl [new-world-checks.csv] required");return 2;}
    // The third argument is a new untimed conformance output, not a replacement
    // for historical measurements. No output path is taken from a case record.
    if(args.Length==3) {
      string worldPath=Path.GetFullPath(args[2]);
      if(String.Equals(worldPath,Path.GetFullPath(args[0]),StringComparison.OrdinalIgnoreCase) ||
         String.Equals(worldPath,Path.GetFullPath(args[1]),StringComparison.OrdinalIgnoreCase))
        throw new ArgumentException("world output must be a distinct new file");
    }
    var timer=Stopwatch.StartNew();var serializer=new JavaScriptSerializer();serializer.MaxJsonLength=16777216;
    long cases=0,worlds=0,checks=0,mismatch=0;
    using(var worldOutput=args.Length==3?new StreamWriter(new FileStream(args[2],FileMode.CreateNew,FileAccess.Write),new System.Text.UTF8Encoding(false)):null)
    using(var output=new StreamWriter(args[1],false,new System.Text.UTF8Encoding(false)))
    {
    if(worldOutput!=null)worldOutput.WriteLine("case,cutoff,retrieval_mask,feedback,source_packets,target_packets,cost_relation");
    foreach(string line in File.ReadLines(args[0])) {
      var row=Object(serializer.DeserializeObject(line));var declaration=Object(row["input"]);var c=Object(declaration["capsule"]);
      int n=Number(c["bits"]), initial=Number(c["initial"]), H=Number(c["horizon"]);
      if(n>4||H>7)throw new ArgumentException("owned finite campaign ceiling");
      var objects=Array(c["outcomes"]);if(objects.Length>6)throw new ArgumentException("owned outcome ceiling");
      var oo=new Outcome[objects.Length];for(int i=0;i<oo.Length;i++){var o=Object(objects[i]);oo[i]=new Outcome{Add=Number(o["add"]),Failure=(string)o["failure"]};}
      int required=0;foreach(int i in Numbers(declaration["required_outcomes"]))required|=1<<i;
      int[] allowed=Numbers(c["feedback"]),q=Numbers(c["query_cost"]),bprice=Numbers(c["feedback_cost"]);
      var results=Array(row["results"]);var truth=new bool[results.Length];for(int j=0;j<truth.Length;j++)truth[j]=true;
      long count=0;
      for(int R=1;R<(1<<oo.Length);R++)if((R&required)==required)
        foreach(int[] B in Feedback(allowed,0,new int[allowed.Length])) {
          count++;var source=Execute(initial,oo,R,B,H,q,bprice);
          for(int j=0;j<results.Length;j++) {
            int K=Number(Object(results[j])["cutoff"]);var target=Execute(initial,oo,R,B,K,q,bprice);
            bool relation=Relation(source,target);truth[j]&=relation;checks++;
            if(worldOutput!=null)worldOutput.WriteLine(String.Join(",",new string[] {
              Number(row["case"]).ToString(System.Globalization.CultureInfo.InvariantCulture),
              K.ToString(System.Globalization.CultureInfo.InvariantCulture),
              R.ToString(System.Globalization.CultureInfo.InvariantCulture),
              String.Concat(System.Array.ConvertAll(B,v=>v.ToString(System.Globalization.CultureInfo.InvariantCulture))),
              source.Count.ToString(System.Globalization.CultureInfo.InvariantCulture),
              target.Count.ToString(System.Globalization.CultureInfo.InvariantCulture),relation?"1":"0" }));
          }
        }
      for(int j=0;j<results.Length;j++)if(truth[j]!=(bool)Object(results[j])["oracle"])mismatch++;
      if(count!=Convert.ToInt64(row["worlds"]))mismatch++;
      output.WriteLine(serializer.Serialize(new { id=Number(row["case"]),worlds=count,valid=truth }));cases++;worlds+=count;
    }
    }
    timer.Stop();var process=Process.GetCurrentProcess();
    Console.WriteLine(serializer.Serialize(new { cases=cases,worlds=worlds,decisions=checks,mismatches=mismatch,
      wall_seconds=timer.Elapsed.TotalSeconds,process_cpu_seconds=process.TotalProcessorTime.TotalSeconds,
      peak_working_set_bytes=process.PeakWorkingSet64,clr=Environment.Version.ToString(),
      scope="Owned complete finite interpreter in a compiled managed Windows process; JIT, not native AOT, third-party validation, retrieval or deployment" }));
    return mismatch==0?0:1;
  }
}
