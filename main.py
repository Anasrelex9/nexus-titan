from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import math

app = FastAPI(title="NEXUS TITAN", version="1.0.0")

class MatchInput(BaseModel):
    home: str = Field(default="الفريق الأول", max_length=60)
    away: str = Field(default="الفريق الثاني", max_length=60)
    xg_home: float = Field(ge=0, le=6)
    xg_away: float = Field(ge=0, le=6)

def poisson(lam: float, k: int) -> float:
    return math.exp(-lam) * (lam ** k) / math.factorial(k)

@app.get("/", response_class=HTMLResponse)
def home():
    return PAGE

@app.get("/health")
def health():
    return {"status": "ok", "app": "NEXUS TITAN", "version": "1.0.0"}

@app.post("/api/analyze")
def analyze(data: MatchInput):
    n = 10
    ph = [poisson(data.xg_home, i) for i in range(n + 1)]
    pa = [poisson(data.xg_away, i) for i in range(n + 1)]
    hw = dr = aw = over25 = btts = 0.0
    scores = []
    for h, hp in enumerate(ph):
        for a, ap in enumerate(pa):
            prob = hp * ap
            if h > a: hw += prob
            elif h == a: dr += prob
            else: aw += prob
            if h + a >= 3: over25 += prob
            if h > 0 and a > 0: btts += prob
            scores.append((prob, h, a))
    total = hw + dr + aw
    scores.sort(reverse=True)
    return {
        "home": data.home, "away": data.away,
        "probabilities": {
            "home_win": round(hw / total * 100, 1),
            "draw": round(dr / total * 100, 1),
            "away_win": round(aw / total * 100, 1),
            "over_2_5": round(over25 * 100, 1),
            "btts": round(btts * 100, 1)
        },
        "top_scores": [
            {"score": f"{h}-{a}", "probability": round(p * 100, 1)}
            for p, h, a in scores[:5]
        ],
        "note": "تقدير مبسط يعتمد فقط على معدلي الأهداف اللذين أدخلتهما. لا يستخدم بيانات مباشرة ولا يضمن النتيجة."
    }

PAGE = r'''<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#09111f"><title>NEXUS TITAN</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#09111f;color:#edf3ff;font-family:Arial,sans-serif}
main{max-width:760px;margin:auto;padding:22px}header{padding:18px 0 24px}
h1{font-size:30px;margin:0;color:#73b7ff;letter-spacing:1px}.sub,.note{color:#aebed3}
.panel{background:#111d30;border:1px solid #263956;border-radius:18px;padding:18px;margin:14px 0}
label{display:block;color:#c8d6eb;margin:12px 0 7px}
input{width:100%;padding:13px;border-radius:10px;border:1px solid #405675;background:#0a1424;color:white;font-size:16px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
button{width:100%;padding:14px;border:0;border-radius:11px;background:#2477d4;color:white;font-weight:bold;font-size:17px;margin-top:18px}
.result{display:none}.metric{background:#0b1728;border-radius:12px;padding:13px}
.metric b{display:block;font-size:23px;color:#80c0ff;margin-top:7px}
.scores{display:flex;gap:8px;flex-wrap:wrap}.score{background:#203653;border-radius:9px;padding:10px}
.note{font-size:13px;line-height:1.7}.error{color:#ffb1b1}
@media(max-width:480px){.grid{grid-template-columns:1fr}}
</style></head><body><main>
<header><h1>NEXUS TITAN</h1><div class="sub">مختبر تحليل مباريات FC 26 وكرة القدم</div></header>
<section class="panel"><h2>تحليل مباراة</h2>
<p class="note">أدخلي تقديرك لمعدل الأهداف المتوقع لكل فريق. سيحسب النظام احتمالات رياضية تقريبية.</p>
<label>اسم الفريق الأول</label><input id="home" value="الفريق الأول">
<label>اسم الفريق الثاني</label><input id="away" value="الفريق الثاني">
<div class="grid">
<div><label>الأهداف المتوقعة للفريق الأول (0 إلى 6)</label><input id="xh" type="number" min="0" max="6" step="0.1" value="1.5"></div>
<div><label>الأهداف المتوقعة للفريق الثاني (0 إلى 6)</label><input id="xa" type="number" min="0" max="6" step="0.1" value="1.2"></div>
</div><button onclick="runAnalysis()">ابدئي التحليل</button><p id="err" class="error"></p></section>
<section id="result" class="panel result"><h2>نتيجة التحليل</h2><div class="grid" id="metrics"></div>
<h3>أكثر النتائج احتمالاً</h3><div class="scores" id="scores"></div><p class="note" id="note"></p></section>
<p class="note">تنبيه: هذه نسخة أولية تعليمية. لا تتصل بمصادر نتائج أو أسعار مباشرة، ولا تضمن الفوز أو الربح.</p>
</main><script>
async function runAnalysis(){
 const err=document.getElementById('err');err.textContent='';
 const xh=Number(document.getElementById('xh').value), xa=Number(document.getElementById('xa').value);
 if(!Number.isFinite(xh)||!Number.isFinite(xa)||xh<0||xa<0||xh>6||xa>6){err.textContent='أدخلي رقماً بين 0 و6 لكل فريق.';return}
 try{
 const r=await fetch('/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({home:document.getElementById('home').value||'الفريق الأول',away:document.getElementById('away').value||'الفريق الثاني',xg_home:xh,xg_away:xa})});
 if(!r.ok)throw new Error('تعذر إجراء التحليل');const d=await r.json();
 const labels=[['فوز '+d.home,d.probabilities.home_win],['تعادل',d.probabilities.draw],['فوز '+d.away,d.probabilities.away_win],['أكثر من 2.5 هدف',d.probabilities.over_2_5],['الفريقان يسجلان',d.probabilities.btts]];
 document.getElementById('metrics').innerHTML=labels.map(x=>`<div class="metric">${x[0]}<b>${x[1]}%</b></div>`).join('');
 document.getElementById('scores').innerHTML=d.top_scores.map(x=>`<span class="score">${x.score} · ${x.probability}%</span>`).join('');
 document.getElementById('note').textContent=d.note;document.getElementById('result').style.display='block';
 }catch(e){err.textContent=e.message}
}
</script></body></html>'''
