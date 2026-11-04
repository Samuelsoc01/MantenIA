import csv, json, statistics, time
from pathlib import Path
import httpx

ROOT=Path(__file__).resolve().parents[1]
for name in ('finops','latency','billing','licenses'):
    (ROOT/'reports'/name).mkdir(parents=True, exist_ok=True)
base='http://127.0.0.1:8000'
payload={'Type':'L','Air temperature [K]':300.0,'Process temperature [K]':310.0,'Rotational speed [rpm]':1500.0,'Torque [Nm]':40.0,'Tool wear [min]':20.0}
rows=[]
with httpx.Client(timeout=30) as c:
    for i in range(100):
        t=time.perf_counter(); r=c.post(base+'/predict',json=payload,headers={'X-Client-ID':'cliente_demo_01'}); rows.append(('individual',i+1,1,r.status_code,(time.perf_counter()-t)*1000))
    data='Type,Air temperature [K],Process temperature [K],Rotational speed [rpm],Torque [Nm],Tool wear [min]\n'+'\n'.join('L,300,310,1500,40,20' for _ in range(1000))
    for i in range(100):
        t=time.perf_counter(); r=c.post(base+'/predict/csv',files={'file':('batch.csv',data,'text/csv')},headers={'X-Client-ID':'cliente_demo_01'}); rows.append(('csv',i+1,1000,r.status_code,(time.perf_counter()-t)*1000))
with (ROOT/'reports/latency/latency_results.csv').open('w',newline='') as f:
    w=csv.writer(f); w.writerow(['kind','iteration','billable_units','status_code','total_latency_ms']); w.writerows(rows)
def stat(v):
    v=sorted(v); return {'count':len(v),'mean_ms':statistics.mean(v),'p50_ms':statistics.median(v),'p95_ms':v[int(.95*(len(v)-1))],'max_ms':max(v),'percent_le_5s':sum(x<=5000 for x in v)/len(v)*100}
summary={k:stat([r[4] for r in rows if r[0]==k]) for k in ('individual','csv')}; summary['total_requests']=len(rows); summary['total_units']=sum(r[2] for r in rows)
(ROOT/'reports/latency/latency_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
(ROOT/'reports/finops/finops_summary.csv').write_text('project,environment,component,resource,cost_rate_mxn,total_billable_units,estimated_cost_mxn\nMantenIA,development,backend,cpu,0.7333,%s,%.2f\n'%(summary['total_units'],0.7333*summary['total_units']),encoding='utf-8')
