/**
 * J.A.R.V.I.S. Control Center - Frontend JS
 */

const API = "";
let currentPage = "dashboard";
let audioCtx = null;
let analyser = null;
let micStream = null;
let serverOnline = true;

// ══════════════════════════════════════════
//  PARTICLES
// ══════════════════════════════════════════
function initParticles() {
    const canvas = document.getElementById("particles");
    const ctx = canvas.getContext("2d");
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const particles = [];
    for (let i = 0; i < 80; i++) {
        particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            vx: (Math.random() - 0.5) * 0.3,
            vy: (Math.random() - 0.5) * 0.3,
            r: Math.random() * 1.5 + 0.5,
            a: Math.random() * 0.3 + 0.1,
        });
    }

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];
            p.x += p.vx;
            p.y += p.vy;

            if (p.x < 0) p.x = canvas.width;
            if (p.x > canvas.width) p.x = 0;
            if (p.y < 0) p.y = canvas.height;
            if (p.y > canvas.height) p.y = 0;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(0, 212, 255, ${p.a})`;
            ctx.fill();

            for (let j = i + 1; j < particles.length; j++) {
                const q = particles[j];
                const dx = p.x - q.x;
                const dy = p.y - q.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 120) {
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(q.x, q.y);
                    ctx.strokeStyle = `rgba(0, 212, 255, ${0.06 * (1 - dist / 120)})`;
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(draw);
    }
    draw();

    window.addEventListener("resize", () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });
}

// ══════════════════════════════════════════
//  CONNECTION STATUS
// ══════════════════════════════════════════
async function checkConnection() {
    try {
        const res = await fetch(`${API}/api/health`);
        if (res.ok) {
            serverOnline = true;
            document.getElementById("sidebar-status").querySelector(".status-dot").className = "status-dot online";
            document.getElementById("sidebar-status").querySelector("span:last-child").textContent = "Online";
        } else {
            throw new Error("offline");
        }
    } catch (e) {
        serverOnline = false;
        document.getElementById("sidebar-status").querySelector(".status-dot").className = "status-dot";
        document.getElementById("sidebar-status").querySelector("span:last-child").textContent = "Offline";
    }
}

// ══════════════════════════════════════════
//  NAVIGATION
// ══════════════════════════════════════════
function initNav() {
    document.querySelectorAll(".nav-item").forEach(item => {
        item.addEventListener("click", () => {
            const page = item.dataset.page;
            switchPage(page);
        });
    });
    document.getElementById("sidebar-toggle").addEventListener("click", () => {
        const sidebar = document.getElementById("sidebar");
        const overlay = document.getElementById("sidebar-overlay");
        sidebar.classList.toggle("open");
        overlay.classList.toggle("open");
    });
    document.getElementById("sidebar-overlay").addEventListener("click", () => {
    document.getElementById("sidebar").classList.remove("open");
    document.getElementById("sidebar-overlay").classList.remove("open");
        document.getElementById("sidebar-overlay").classList.remove("open");
    });
}

function updatePageTitle(page) {
    const names = {
        dashboard: "Dashboard",
        chat: "Chat",
        voice: "Voz",
        control: "Controle PC",
        vision: "Visao",
        memory: "Memoria",
        files: "Arquivos",
        smarthome: "Casa Inteligente",
        robots: "Robos",
        map: "Mapa",
        stats: "Estatisticas",
        security: "Seguranca",
        plugins: "Plugins",
        logs: "Logs",
        modules: "Modulos",
        config: "Config",
    };
    document.title = `JARVIS - ${names[page] || page}`;
}

function switchPage(page) {
    currentPage = page;
    updatePageTitle(page);
    document.querySelectorAll(".nav-item").forEach(i => i.classList.remove("active"));
    document.querySelector(`.nav-item[data-page="${page}"]`).classList.add("active");
    document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
    document.getElementById(`page-${page}`).classList.add("active");
    document.getElementById("sidebar").classList.remove("open");

    if (page === "logs") loadLogs();
    if (page === "memory") loadMemory();
    if (page === "modules") loadModules();
    if (page === "files") loadFiles();
    if (page === "config") loadSettings();
}

// ══════════════════════════════════════════
//  DASHBOARD
// ══════════════════════════════════════════
async function refreshDashboard() {
    try {
        const res = await fetch(`${API}/api/dashboard`);
        if (!res.ok) throw new Error("HTTP " + res.status);
        const d = await res.json();

        document.getElementById("dash-time").textContent = d.time;
        document.getElementById("dash-date").textContent = d.date;
        document.getElementById("d-uptime").textContent = d.uptime;
        document.getElementById("d-modules").textContent = d.modules_count;
        document.getElementById("d-platform").textContent = d.jarvis.platform || sys.platform;
        document.getElementById("jarvis-state").textContent = d.jarvis.state || "Ativo";
        document.getElementById("jarvis-provider").textContent = d.jarvis.provider;

        setMetric("d-cpu", "d-cpu-bar", d.cpu.percent, `${d.cpu.cores} cores`);
        setMetric("d-ram", "d-ram-bar", d.ram.percent, `${d.ram.used} / ${d.ram.total} GB`);
        setMetric("d-disk", "d-disk-bar", d.disk.percent, `${d.disk.used} / ${d.disk.total} GB`);

        const pingEl = document.getElementById("d-ping");
        pingEl.textContent = `${d.network.ping}ms`;
        setBar("d-ping-bar", Math.min(d.network.ping / 2, 100));
        document.getElementById("d-net-sub").textContent = `↓ ${d.network.recv_mb} MB  ↑ ${d.network.sent_mb} MB`;

        const procsRes = await fetch(`${API}/api/processes`);
        const procs = await procsRes.json();
        const procsEl = document.getElementById("d-processes");
        if (procs.length === 0) {
            procsEl.innerHTML = '<div style="color:var(--text3)">Nenhum processo ativo</div>';
        } else {
            procsEl.innerHTML = procs.map(p => `
                <div class="proc-row">
                    <span class="proc-name">${esc(p.name)}</span>
                    <span class="proc-cpu">${p.cpu}%</span>
                    <span class="proc-ram">${p.ram_pct}%</span>
                </div>
            `).join("");
        }

        lastDashData = d;
        if (typeof updateStats === "function") updateStats(d);
        checkConnection();
    } catch (e) {
        console.error("Dashboard error:", e);
        checkConnection();
    }
}

function setMetric(valId, barId, pct, sub) {
    document.getElementById(valId).textContent = `${pct}%`;
    setBar(barId, pct);
    document.getElementById(valId).closest(".metric-card").querySelector(".metric-sub").textContent = sub;
}

function setBar(id, pct) {
    const bar = document.getElementById(id);
    if (!bar) return;
    bar.style.width = `${pct}%`;
    bar.classList.remove("warning", "critical");
    if (pct > 90) bar.classList.add("critical");
    else if (pct > 75) bar.classList.add("warning");
}

function esc(s) { const d = document.createElement("div"); d.textContent = s; return d.innerHTML; }

// Store dashData globally for stats
let lastDashData = null;

// ══════════════════════════════════════════
//  CHAT
// ══════════════════════════════════════════
function initChat() {
    const input = document.getElementById("chat-input");
    const btn = document.getElementById("btn-send");

    btn.addEventListener("click", sendChat);
    input.addEventListener("keydown", e => { if (e.key === "Enter") sendChat(); });
}

async function sendChat() {
    const input = document.getElementById("chat-input");
    const msg = input.value.trim();
    if (!msg) return;

    addChatMsg("user", msg);
    input.value = "";

    addChatMsg("jarvis", "Pensando...");

    try {
        const res = await fetch(`${API}/api/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: msg }),
        });
        const data = await res.json();

        const msgs = document.getElementById("chat-messages");
        msgs.removeChild(msgs.lastChild);

        if (data.response === "__CLEAR__") {
            msgs.innerHTML = "";
            addChatMsg("jarvis", "Tela limpa.");
        } else {
            addChatMsg("jarvis", data.response, data.time);
        }
    } catch (e) {
        const msgs = document.getElementById("chat-messages");
        msgs.removeChild(msgs.lastChild);
        addChatMsg("jarvis", "Erro de conexao com o servidor.");
    }
}

function addChatMsg(role, content, time) {
    const container = document.getElementById("chat-messages");
    const avatar = role === "jarvis" ? "🤖" : "👤";
    const now = time || new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });

    const div = document.createElement("div");
    div.className = `chat-msg ${role}`;
    div.innerHTML = `
        <div class="chat-avatar">${avatar}</div>
        <div class="chat-bubble">${esc(content)}</div>
        <div class="chat-time">${now}</div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

// ══════════════════════════════════════════
//  VOICE
// ══════════════════════════════════════════
function initVoice() {
    const btn = document.getElementById("voice-btn");
    btn.addEventListener("click", toggleVoice);

    const speakBtn = document.getElementById("btn-speak");
    speakBtn.addEventListener("click", speakText);

    document.getElementById("voice-text-input").addEventListener("keydown", e => {
        if (e.key === "Enter") speakText();
    });
}

async function toggleVoice() {
    const btn = document.getElementById("voice-btn");
    const status = document.getElementById("voice-status");

    if (btn.classList.contains("listening")) {
        btn.classList.remove("listening");
        status.textContent = "Pronto";
        if (micStream) {
            micStream.getTracks().forEach(t => t.stop());
            micStream = null;
        }
        return;
    }

    try {
        micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        btn.classList.add("listening");
        status.textContent = "Ouvindo...";

        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioCtx.createAnalyser();
        const source = audioCtx.createMediaStreamSource(micStream);
        source.connect(analyser);
        analyser.fftSize = 256;

        drawWaveform();
    } catch (e) {
        status.textContent = "Microfone nao permitido";
    }
}

function drawWaveform() {
    const canvas = document.getElementById("voice-wave");
    const ctx = canvas.getContext("2d");
    const bufLen = analyser.frequencyBinCount;
    const data = new Uint8Array(bufLen);

    function draw() {
        if (!document.getElementById("voice-btn").classList.contains("listening")) return;

        requestAnimationFrame(draw);
        analyser.getByteFrequencyData(data);

        ctx.fillStyle = "rgba(6, 10, 19, 0.3)";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        const barW = (canvas.width / bufLen) * 2;
        let x = 0;

        for (let i = 0; i < bufLen; i++) {
            const barH = (data[i] / 255) * canvas.height * 0.8;
            const hue = 180 + (data[i] / 255) * 40;
            ctx.fillStyle = `hsl(${hue}, 100%, 50%)`;
            ctx.fillRect(x, canvas.height - barH, barW - 1, barH);
            x += barW;
        }
    }
    draw();
}

async function speakText() {
    const input = document.getElementById("voice-text-input");
    const text = input.value.trim();
    if (!text) return;

    const status = document.getElementById("voice-status");
    const transcript = document.getElementById("voice-transcript");
    const response = document.getElementById("voice-response");

    status.textContent = "Falando...";
    transcript.textContent = text;

    try {
        await fetch(`${API}/api/voice/speak`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text }),
        });
        response.textContent = "Reproduzindo audio...";
        status.textContent = "Pronto";
    } catch (e) {
        status.textContent = "Erro ao falar";
    }
}

// ══════════════════════════════════════════
//  PC CONTROL
// ══════════════════════════════════════════
function initControl() {
    document.querySelectorAll(".control-btn").forEach(btn => {
        btn.addEventListener("click", async () => {
            const action = btn.dataset.action;
            if (!confirm(`Executar: ${action}?`)) return;

            try {
                await fetch(`${API}/api/control/${action}`, { method: "POST" });
                btn.style.borderColor = "var(--green)";
                setTimeout(() => btn.style.borderColor = "", 1500);
            } catch (e) {
                btn.style.borderColor = "var(--red)";
                setTimeout(() => btn.style.borderColor = "", 1500);
            }
        });
    });
}

// ══════════════════════════════════════════
//  MEMORY
// ══════════════════════════════════════════
async function loadMemory() {
    try {
        const res = await fetch(`${API}/api/memory`);
        const data = await res.json();

        const infoEl = document.getElementById("memory-info");
        infoEl.innerHTML = Object.entries(data.info).map(([k, v]) => `
            <div class="mem-info-card">
                <div class="mem-label">${k.replace(/_/g, " ")}</div>
                <div class="mem-value">${esc(String(v))}</div>
            </div>
        `).join("");

        const listEl = document.getElementById("memory-list");
        if (data.memories.length === 0) {
            listEl.innerHTML = '<div style="color:var(--text3);padding:20px">Nenhuma memoria salva ainda.</div>';
        } else {
            listEl.innerHTML = data.memories.map(m => `
                <div class="mem-item">
                    <div class="mem-key">${esc(m.key || "")}</div>
                    <div class="mem-val">${esc(m.value || m.content || "")}</div>
                </div>
            `).join("");
        }
    } catch (e) {
        document.getElementById("memory-info").innerHTML = '<div style="color:var(--red)">Erro ao carregar memoria</div>';
    }
}

// ══════════════════════════════════════════
//  FILES
// ══════════════════════════════════════════
async function loadFiles(path) {
    try {
        const url = path ? `/api/files?path=${encodeURIComponent(path)}` : `/api/files`;
        const res = await fetch(url);
        const data = await res.json();

        document.getElementById("files-path").value = data.current || path || "C:\\";

        const listEl = document.getElementById("files-list");
        listEl.innerHTML = data.items.map(f => `
            <div class="file-row" data-path="${esc(f.path)}" data-isdir="${f.is_dir}">
                <span class="file-icon">${f.is_dir ? "📁" : "📄"}</span>
                <span class="file-name">${esc(f.name)}</span>
                <span class="file-size">${f.is_dir ? "" : f.size}</span>
            </div>
        `).join("");

        listEl.querySelectorAll(".file-row").forEach(row => {
            row.addEventListener("click", () => {
                if (row.dataset.isdir === "true") {
                    loadFiles(row.dataset.path);
                }
            });
        });
    } catch (e) {
        document.getElementById("files-list").innerHTML = '<div style="color:var(--red);padding:20px">Erro ao carregar arquivos</div>';
    }
}

// ══════════════════════════════════════════
//  LOGS
// ══════════════════════════════════════════
async function loadLogs() {
    try {
        const res = await fetch(`${API}/api/logs`);
        const data = await res.json();

        const listEl = document.getElementById("logs-list");
        if (data.logs.length === 0) {
            listEl.innerHTML = '<div style="color:var(--text3);padding:20px">Nenhum log registrado.</div>';
            return;
        }

        listEl.innerHTML = data.logs.reverse().map(l => {
            const typeClass = l.type.includes("chat_user") ? "chat_user"
                : l.type.includes("chat_jarvis") ? "chat_jarvis"
                : l.type.includes("control") ? "control"
                : "voice";
            const msg = l.message || l.text || l.action || "";
            return `
                <div class="log-entry">
                    <span class="log-time">${l.time || "--:--"}</span>
                    <span class="log-type ${typeClass}">${l.type}</span>
                    <span class="log-msg">${esc(msg)}</span>
                </div>
            `;
        }).join("");
    } catch (e) {
        document.getElementById("logs-list").innerHTML = '<div style="color:var(--red)">Erro ao carregar logs</div>';
    }
}

// ══════════════════════════════════════════
//  MODULES
// ══════════════════════════════════════════
async function loadModules() {
    try {
        const res = await fetch(`${API}/api/modules`);
        const mods = await res.json();

        document.getElementById("modules-grid").innerHTML = mods.map(m => `
            <div class="mod-card glass">
                <div class="mod-name">${esc(m.name)}</div>
                <div class="mod-files">${m.files} arquivos</div>
                <div class="mod-status"></div>
            </div>
        `).join("");
    } catch (e) {
        document.getElementById("modules-grid").innerHTML = '<div style="color:var(--red)">Erro ao carregar modulos</div>';
    }
}

// ══════════════════════════════════════════
//  CONFIG
// ══════════════════════════════════════════
async function loadSettings() {
    try {
        const res = await fetch(`${API}/api/settings`);
        const s = await res.json();
        document.getElementById("cfg-theme").value = s.theme || "cyan";
        document.getElementById("cfg-language").value = s.language || "pt-BR";
        document.getElementById("cfg-wakeword").value = s.wake_word || "jarvis";
        document.getElementById("cfg-tts-voice").value = s.tts_voice || "pt-BR-AntonioNeural";
        document.getElementById("cfg-model").value = s.model || s.ai_model || "";
    } catch (e) {}
}

function initConfig() {
    document.getElementById("btn-save-config").addEventListener("click", async () => {
        const settings = {
            theme: document.getElementById("cfg-theme").value,
            language: document.getElementById("cfg-language").value,
            wake_word: document.getElementById("cfg-wakeword").value,
            tts_voice: document.getElementById("cfg-tts-voice").value,
            ai_model: document.getElementById("cfg-model").value,
        };

        try {
            await fetch(`${API}/api/settings`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(settings),
            });
            const btn = document.getElementById("btn-save-config");
            btn.textContent = "Salvo!";
            btn.style.borderColor = "var(--green)";
            btn.style.color = "var(--green)";
            setTimeout(() => {
                btn.textContent = "Salvar Configuracoes";
                btn.style.borderColor = "";
                btn.style.color = "";
            }, 2000);
        } catch (e) {
            alert("Erro ao salvar");
        }
    });
}

// ══════════════════════════════════════════
//  LOGS REFRESH
// ══════════════════════════════════════════
function initLogsRefresh() {
    document.getElementById("btn-refresh-logs").addEventListener("click", loadLogs);
}

// ══════════════════════════════════════════
//  VISION / CAMERA
// ══════════════════════════════════════════
function initVision() {
    const btnCamera = document.getElementById("btn-camera");
    const video = document.getElementById("camera-video");
    const placeholder = document.getElementById("camera-placeholder");

    btnCamera.addEventListener("click", async () => {
        if (video.style.display === "block") {
            video.style.display = "none";
            placeholder.style.display = "flex";
            btnCamera.textContent = "Ativar Camera";
            if (video.srcObject) {
                video.srcObject.getTracks().forEach(t => t.stop());
                video.srcObject = null;
            }
            return;
        }
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;
            video.style.display = "block";
            placeholder.style.display = "none";
            btnCamera.textContent = "Desativar Camera";
        } catch (e) {
            placeholder.querySelector("span:last-child").textContent = "Camera nao permitida";
        }
    });

    const btnCapture = document.getElementById("btn-capture");
    btnCapture.addEventListener("click", () => {
        alert("Captura de tela enviada ao Jarvis para analise!");
    });
}

// ══════════════════════════════════════════
//  SMART HOME
// ══════════════════════════════════════════
function initSmartHome() {
    document.querySelectorAll(".sh-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            btn.classList.toggle("active");
            const status = btn.querySelector(".sh-status");
            if (btn.classList.contains("active")) {
                status.textContent = "Ligada";
            } else {
                status.textContent = "Desligada";
            }
        });
    });
}

// ══════════════════════════════════════════
//  STATISTICS
// ══════════════════════════════════════════
let cpuHistory = [];
let ramHistory = [];

function initStats() {
    drawChart("stats-cpu-chart", cpuHistory, "#00d4ff");
    drawChart("stats-ram-chart", ramHistory, "#00ff88");
}

function updateStats(dashData) {
    if (dashData.cpu) cpuHistory.push(dashData.cpu.percent);
    if (dashData.ram) ramHistory.push(dashData.ram.percent);
    if (cpuHistory.length > 30) cpuHistory.shift();
    if (ramHistory.length > 30) ramHistory.shift();

    drawChart("stats-cpu-chart", cpuHistory, "#00d4ff");
    drawChart("stats-ram-chart", ramHistory, "#00ff88");
}

function drawChart(canvasId, data, color) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    canvas.width = canvas.parentElement.clientWidth - 40;
    canvas.height = 200;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (data.length < 2) return;

    const max = 100;
    const w = canvas.width;
    const h = canvas.height;
    const step = w / (data.length - 1);

    ctx.beginPath();
    ctx.moveTo(0, h - (data[0] / max) * h);
    for (let i = 1; i < data.length; i++) {
        ctx.lineTo(i * step, h - (data[i] / max) * h);
    }
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.lineTo((data.length - 1) * step, h);
    ctx.lineTo(0, h);
    ctx.closePath();
    ctx.fillStyle = color.replace(")", ", 0.1)").replace("rgb", "rgba").replace("#", "");
    const gradient = ctx.createLinearGradient(0, 0, 0, h);
    gradient.addColorStop(0, color + "33");
    gradient.addColorStop(1, "transparent");
    ctx.fillStyle = gradient;
    ctx.fill();
}

async function loadStats() {
    try {
        const res = await fetch(`${API}/api/stats`);
        if (!res.ok) throw new Error("HTTP " + res.status);
        const s = await res.json();
        document.getElementById("stat-commands").textContent = s.total_commands || 0;
        document.getElementById("stat-responses").textContent = s.chat_commands || 0;
        document.getElementById("stat-uptime").textContent = s.uptime || "--";
    } catch (e) {
        document.getElementById("stat-commands").textContent = "--";
        document.getElementById("stat-responses").textContent = "--";
        document.getElementById("stat-uptime").textContent = "Offline";
    }
}

// ══════════════════════════════════════════
//  WEATHER
// ══════════════════════════════════════════
async function loadWeather() {
    try {
        const res = await fetch(`${API}/api/weather`);
        if (!res.ok) throw new Error("HTTP " + res.status);
        const w = await res.json();
        if (w.temp !== undefined && w.temp !== "--") {
            document.getElementById("w-temp").textContent = `${w.temp}°`;
            document.getElementById("w-desc").textContent = w.description || "";
            document.getElementById("w-humidity").textContent = `💧 ${w.humidity}%`;
            document.getElementById("w-wind").textContent = `💨 ${w.wind} km/h`;
        } else {
            document.getElementById("w-desc").textContent = "Clima indisponivel";
        }
    } catch (e) {
        document.getElementById("w-desc").textContent = "Offline";
    }
}

// ══════════════════════════════════════════
//  INIT
// ══════════════════════════════════════════
document.addEventListener("DOMContentLoaded", () => {
    initParticles();
    initNav();
    initChat();
    initVoice();
    initControl();
    initConfig();
    initLogsRefresh();
    initVision();
    initSmartHome();
    initStats();

    checkConnection();
    refreshDashboard();
    setInterval(refreshDashboard, 3000);
    setInterval(checkConnection, 15000);
    loadWeather();
    setInterval(loadWeather, 300000);
    loadStats();
    setInterval(loadStats, 10000);
});
