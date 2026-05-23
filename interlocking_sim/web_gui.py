from __future__ import annotations

import json
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .interlocking import InterlockingController
from .model import SignalAspect, SwitchPosition, TrackState, build_station


STATE = build_station()
CTRL = InterlockingController(STATE)
LOCK = threading.Lock()


HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>计算机联锁模拟仿真系统</title>
  <style>
    body { margin: 0; background: #f4f6f8; color: #1f2937; font-family: Arial, "Microsoft YaHei", sans-serif; }
    header { padding: 14px 22px; background: #111827; color: #f8fafc; font-size: 22px; font-weight: 700; }
    main { display: grid; grid-template-columns: 1fr 420px; gap: 14px; padding: 14px; }
    canvas { width: 100%; height: 330px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; }
    .panel { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 12px; margin-bottom: 12px; box-shadow: 0 1px 2px #0001; }
    h2 { margin: 0 0 10px; font-size: 16px; color: #1d4ed8; }
    button { margin: 3px; padding: 7px 9px; border: 0; border-radius: 6px; background: #2563eb; color: white; cursor: pointer; }
    button:hover { background: #1d4ed8; }
    .danger { background: #dc2626; }
    .warn { background: #ca8a04; }
    .grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 4px; }
    pre { white-space: pre-wrap; line-height: 1.5; background: #f8fafc; padding: 10px; border-radius: 8px; min-height: 170px; border: 1px solid #e2e8f0; }
  </style>
</head>
<body>
  <header>计算机联锁模拟仿真系统 - 单机软件上位机</header>
  <main>
    <section>
      <canvas id="yard" width="1200" height="380"></canvas>
      <div class="panel"><h2>列车/调车进路按钮</h2><div id="routes"></div></div>
      <div class="panel"><h2>单道岔操作、单锁、封锁</h2><div id="switches"></div></div>
    </section>
    <aside>
      <div class="panel"><h2>信号故障仿真</h2><button onclick="post('/signal?name=X')">X断丝/恢复</button><button onclick="post('/signal?name=S')">S断丝/恢复</button></div>
      <div class="panel"><h2>动态提示/状态</h2><pre id="status"></pre></div>
    </aside>
  </main>
<script>
const trackLines = {JXG:[[50,170,120,170]],IIAG:[[120,170,250,170]],'3G':[[250,170,330,90],[330,90,780,90],[780,90,880,170]],IIG:[[250,170,880,170]],'1G':[[320,170,420,245],[420,245,880,245],[880,245,950,170]],IIBG:[[950,170,1060,170]],JSG:[[1060,170,1150,170]],'安全线':[[210,245,300,245]]};
const signals = {X:[120,150],D1:[180,150],S3:[430,110],SII:[430,190],S1:[430,265],PZA:[330,275],X3:[760,110],XII:[760,190],X1:[760,265],D2:[1010,190],S:[1070,190]};
const signalTrackY = {X:170,D1:170,S3:90,SII:170,S1:245,PZA:245,X3:90,XII:170,X1:245,D2:170,S:170};
const switchMarks = {'1':[250,170],'3':[320,170],'5':[360,245],'4':[880,170],'2':[950,170]};
let routeNames = [];
let switchNames = [];
let currentData = __INITIAL_STATE__;

async function post(path) { await fetch(path, {method:'POST'}); await load(); }
async function load() {
  try {
    currentData = await (await fetch('/state', {cache: 'no-store'})).json();
  } catch (err) {
    currentData.messages = ['状态接口暂不可用，已显示内置初始站场图。', String(err)];
  }
  draw(currentData); renderControls(currentData); renderStatus(currentData);
}
function renderControls(data) {
  if (!routeNames.length) {
    routeNames = Object.keys(data.routes);
    document.getElementById('routes').innerHTML = routeNames.map(n => `<div><b>${n}</b><button onclick="post('/route?name=${encodeURIComponent(n)}')">办理</button><button class="warn" onclick="post('/cancel?name=${encodeURIComponent(n)}')">取消</button><button class="danger" onclick="post('/manual?name=${encodeURIComponent(n)}')">人工解锁</button></div>`).join('');
  }
  if (!switchNames.length) {
    switchNames = Object.keys(data.switches);
    document.getElementById('switches').innerHTML = switchNames.map(n => `<div><b>${n}</b><button onclick="post('/switch?name=${encodeURIComponent(n)}&target=NORMAL')">定操</button><button onclick="post('/switch?name=${encodeURIComponent(n)}&target=REVERSE')">反操</button><button class="warn" onclick="post('/lock?name=${encodeURIComponent(n)}&value=1')">单锁</button><button onclick="post('/lock?name=${encodeURIComponent(n)}&value=0')">单解</button><button class="danger" onclick="post('/block?name=${encodeURIComponent(n)}&value=1')">封锁</button><button onclick="post('/block?name=${encodeURIComponent(n)}&value=0')">解封</button></div>`).join('');
  }
}
function renderStatus(data) {
  const routes = Object.entries(data.routes).map(([n,r]) => `${n}: ${r.locked ? '锁闭' : '未锁'}${r.cancel_countdown ? ', 解锁倒计时 '+r.cancel_countdown+'s' : ''}`);
  document.getElementById('status').textContent = `仿真秒: ${data.tick_no}\n\n进路状态:\n${routes.join('\n')}\n\n操作提示:\n${data.messages.join('\n')}`;
}
function draw(data) {
  const c = document.getElementById('yard'), ctx = c.getContext('2d');
  ctx.clearRect(0,0,c.width,c.height);
  ctx.fillStyle = '#111827'; ctx.font = 'bold 20px Arial'; ctx.fillText('计算机联锁模拟仿真系统站场图', 430, 32);
  ctx.fillStyle = '#94a3b8'; ctx.font = '13px Arial'; ctx.fillText('6‰', 1000, 80);
  const locked = new Set(); Object.values(data.routes).forEach(r => { if (r.locked) r.tracks.forEach(t => locked.add(t)); });
  for (const [n, segs] of Object.entries(trackLines)) {
    const state = data.tracks[n]; const color = state === '占压' ? '#ef4444' : locked.has(n) ? '#2563eb' : '#9a641f'; const width = state === '占压' ? 8 : locked.has(n) ? 7 : 4;
    for (const p of segs) { ctx.strokeStyle = color; ctx.lineWidth = width; ctx.beginPath(); ctx.moveTo(p[0],p[1]); ctx.lineTo(p[2],p[3]); ctx.stroke(); }
  }
  drawBufferStop(ctx, 210, 245); drawEndDevice(ctx, 43, 170); drawEndDevice(ctx, 1158, 170); drawButtonSquare(ctx, 95, 170); drawButtonSquare(ctx, 1120, 170);
  drawLabels(ctx);
  for (const [mark,p] of Object.entries(switchMarks)) {
    const sw = data.switches[mark]; ctx.fillStyle = sw.position === '定位' ? '#a855f7' : sw.position === '反位' ? '#ec4899' : '#facc15';
    ctx.fillRect(p[0]-5,p[1]-5,10,10); ctx.strokeStyle = '#111827'; ctx.strokeRect(p[0]-5,p[1]-5,10,10);
    ctx.fillStyle = '#111827'; ctx.font = '12px Arial'; ctx.fillText(mark, p[0]-4, p[1]+20);
  }
  for (const [n,p] of Object.entries(signals)) {
    drawSignal(ctx, n, p[0], p[1], data.signals[n]);
  }
  for (const train of Object.values(data.trains)) {
    if (!train.active || !trackLines[train.current_track]) continue;
    const p = trackLines[train.current_track][0], x=(p[0]+p[2])/2, y=(p[1]+p[3])/2;
    ctx.fillStyle = '#06b6d4'; ctx.fillRect(x-18,y-28,36,18); ctx.strokeStyle = '#083344'; ctx.strokeRect(x-18,y-28,36,18); ctx.fillStyle='#0f172a'; ctx.fillText(train.name,x-10,y-34);
  }
  drawLegend(ctx);
}
function drawSignal(ctx, name, x, y, aspect) {
  ctx.strokeStyle = '#4b5563'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x, signalTrackY[name]); ctx.lineTo(x, y < signalTrackY[name] ? y+9 : y-9); ctx.stroke(); ctx.lineWidth = 1;
  drawButtonSquare(ctx, x+26, y);
  const colors = aspect === '开放' ? ['#22c55e', '#22c55e'] : aspect === '断丝' ? ['#f97316', '#f97316'] : ['#bfc5cf', '#bfc5cf'];
  ctx.fillStyle = colors[0]; ctx.beginPath(); ctx.arc(x, y, 5, 0, Math.PI*2); ctx.fill(); ctx.strokeStyle='#111827'; ctx.stroke();
  ctx.fillStyle = colors[1]; ctx.beginPath(); ctx.arc(x+19, y, 5, 0, Math.PI*2); ctx.fill(); ctx.strokeStyle='#111827'; ctx.stroke();
  ctx.fillStyle = '#111827'; ctx.font = '12px Arial'; ctx.fillText(name, x-8, ['S1','X1','PZA'].includes(name) ? y+20 : y-15);
  if (aspect === '断丝') ctx.fillText('断丝', x+55, y+3);
}
function drawBufferStop(ctx, x, y) {
  ctx.strokeStyle = '#a56a20'; ctx.lineWidth = 3;
  ctx.beginPath(); ctx.moveTo(x, y-16); ctx.lineTo(x, y+16); ctx.moveTo(x-12, y-16); ctx.lineTo(x+12, y-16); ctx.moveTo(x-12, y+16); ctx.lineTo(x+12, y+16); ctx.stroke();
}
function drawButtonSquare(ctx, x, y) { ctx.fillStyle = '#d946ef'; ctx.fillRect(x-6, y-6, 12, 12); ctx.strokeStyle = '#111827'; ctx.strokeRect(x-6, y-6, 12, 12); }
function drawEndDevice(ctx, x, y) { ctx.fillStyle = '#d1d5db'; ctx.fillRect(x-7, y-9, 14, 18); ctx.strokeStyle = '#111827'; ctx.strokeRect(x-7, y-9, 14, 18); }
function drawHollowPoint(ctx, x, y, color) { ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(x, y, 5, 0, Math.PI*2); ctx.stroke(); ctx.lineWidth = 1; }
function drawLabels(ctx) { const labels = {JXG:[78,193],IIAG:[182,193],'3G':[540,72],IIG:[560,152],'1G':[560,228],IIBG:[1006,152],JSG:[1105,152],'安全线':[246,226]}; ctx.fillStyle='#111827'; ctx.font='13px Arial'; for (const [t,p] of Object.entries(labels)) ctx.fillText(t,p[0],p[1]); }
function drawLegend(ctx) {
  const items = [['#9a641f','轨道出清'], ['#2563eb','进路锁闭'], ['#ef4444','轨道占压'], ['#22c55e','信号开放'], ['#bfc5cf','信号关闭'], ['#f97316','信号断丝'], ['#a855f7','道岔定位'], ['#ec4899','道岔反位']];
  let x = 60, y = 335; ctx.font = '12px Arial';
  for (const [color, text] of items) { ctx.fillStyle = color; ctx.fillRect(x, y-10, 18, 10); ctx.fillStyle = '#111827'; ctx.fillText(text, x+24, y); x += 128; }
}
draw(currentData); renderControls(currentData); renderStatus(currentData);
setInterval(load, 1000); load();
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/state":
            self._json(snapshot())
            return
        self._html(render_html())

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        args = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        with LOCK:
            if parsed.path == "/route":
                CTRL.request_route(args["name"])
            elif parsed.path == "/cancel":
                CTRL.cancel_route(args["name"])
            elif parsed.path == "/manual":
                CTRL.cancel_route(args["name"], manual=True)
            elif parsed.path == "/switch":
                target = SwitchPosition.NORMAL if args["target"] == "NORMAL" else SwitchPosition.REVERSE
                CTRL.move_switch(args["name"], target)
            elif parsed.path == "/lock":
                CTRL.set_switch_lock(args["name"], args["value"] == "1")
            elif parsed.path == "/block":
                CTRL.set_switch_block(args["name"], args["value"] == "1")
            elif parsed.path == "/signal":
                sig = STATE.signals[args["name"]]
                CTRL.set_signal_broken(args["name"], not sig.broken)
        self._json({"ok": True})

    def log_message(self, fmt: str, *args: object) -> None:
        return

    def _html(self, body: str) -> None:
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _json(self, obj: object) -> None:
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def snapshot() -> dict:
    with LOCK:
        return {
            "tick_no": STATE.tick_no,
            "tracks": {k: v.state.value for k, v in STATE.tracks.items()},
            "signals": {k: v.aspect.value for k, v in STATE.signals.items()},
            "switches": {k: {"position": v.position.value, "locked": v.locked, "single_locked": v.single_locked, "blocked": v.blocked} for k, v in STATE.switches.items()},
            "routes": {k: {"locked": v.locked, "cancel_countdown": v.cancel_countdown, "tracks": v.tracks} for k, v in STATE.routes.items()},
            "trains": {k: {"name": v.name, "active": v.active, "current_track": v.current_track} for k, v in STATE.trains.items()},
            "messages": STATE.messages[-8:],
        }


def render_html() -> str:
    return HTML.replace("__INITIAL_STATE__", json.dumps(snapshot(), ensure_ascii=False))


def tick_loop() -> None:
    while True:
        time.sleep(1)
        with LOCK:
            CTRL.tick()


def main() -> None:
    threading.Thread(target=tick_loop, daemon=True).start()
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    url = "http://127.0.0.1:8765"
    print("当前 Python 缺少 Tkinter，已启动单机软件上位机（本机浏览器承载界面）。")
    print(f"访问地址: {url}")
    webbrowser.open(url)
    server.serve_forever()
