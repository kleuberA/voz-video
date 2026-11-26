/**
 * Episódio #9 — "Estude comigo: 30 s de lei seca" (formato B de producao/ESTRATEGIA_CONVERSAO.md).
 * Sem voz: tela do app + letreiros + trilha (montar_sem_voz.py). Uma sessão de estudo real:
 * ler o inciso → grifar → virar flashcard (Ocultar trecho) → testar (Errei/Difícil/Bom/Fácil).
 *
 * Fidelidade (ficha.fidelidade_app): rótulos e intervalos de um card novo como no app
 * (lib/flashcards/srs.ts: Errei = agora, Difícil e Bom = 1 dia, Fácil = 4 dias). É uma recriação
 * da interface: o app não roda neste ambiente.
 * Texto de lei: só ficha.fontes[].texto_literal (CF, art. 5º, LXVIII e LXIX).
 */
import { EASE, clamp, count, mix, pop, prog, rise, shake, spring, track } from "../motor.js";
import { ICONE, compor, destacar, esc, selo } from "../pecas.js";

const css = `
.e9-topo { left: 20px; position: absolute; right: 20px; text-align: center; }
.e9-gancho { font-size: 40px; }
.e9-passo { align-items: center; background: rgba(8,18,13,0.85); border: 1px solid rgba(242,183,102,0.45); border-radius: 99px; color: var(--amber);
  display: inline-flex; font-size: 15px; font-weight: 700; gap: 8px; padding: 7px 14px; }
.e9-passo b { background: var(--amber); border-radius: 50%; color: #1b1407; display: inline-flex; font-size: 12px; height: 20px; justify-content: center; line-height: 20px; width: 20px; }
.e9-janela { background: #111411; border: 1px solid rgba(255,255,255,0.14); border-radius: 14px; left: 16px; overflow: hidden; position: absolute; right: 52px;
  box-shadow: 0 0 90px -20px rgba(92,196,127,0.22), 0 30px 60px -18px rgba(0,0,0,0.6); }
.e9-barra { align-items: center; background: #1b201c; display: flex; gap: 5px; padding: 7px 9px; }
.e9-barra i { background: #343a35; border-radius: 50%; height: 6px; width: 6px; }
.e9-url { background: #0c0f0c; border-radius: 6px; color: #8f8f87; flex: 1; font-size: 9px; margin-left: 5px; overflow: hidden; padding: 3px 7px; white-space: nowrap; }
.e9-app { align-items: center; border-bottom: 1px solid rgba(255,255,255,0.08); display: flex; font-size: 11px; gap: 7px; justify-content: space-between; padding: 8px 12px; }
.e9-app span { align-items: center; display: flex; font-weight: 700; gap: 6px; letter-spacing: 0.12em; }
.e9-app img { height: 14px; width: 14px; }
.e9-cron { background: rgba(141,219,166,0.12); border-radius: 99px; color: var(--hi); font-family: var(--mono); font-size: 10.5px; padding: 3px 8px; }
.e9-leitor { color: #e9e6df; font-family: var(--serif); font-size: 15.5px; line-height: 1.6; padding: 12px 14px 16px; position: relative; }
.e9-leitor h4 { color: var(--cap-3); font-family: var(--mono); font-size: 10px; font-weight: 600; letter-spacing: 0.14em; margin-bottom: 6px; text-transform: uppercase; }
.e9-leitor p { margin-bottom: 10px; }
.e9-sel { border-radius: 2px; }
.e9-ferr { align-items: center; background: #1f2421; border: 1px solid rgba(255,255,255,0.16); border-radius: 10px; display: flex; gap: 7px; padding: 6px 8px; position: absolute;
  box-shadow: 0 12px 30px -8px rgba(0,0,0,0.7); }
.e9-ferr i { border-radius: 50%; display: block; height: 15px; width: 15px; }
.e9-ferr span { color: #e9e6df; font-size: 11px; font-weight: 600; padding: 0 3px; }
.e9-dialogo { background: #161a17; border: 1px solid rgba(255,255,255,0.16); border-radius: 14px; left: 26px; padding: 14px; position: absolute; right: 62px;
  box-shadow: 0 30px 70px -10px rgba(0,0,0,0.8); }
.e9-dialogo h5 { font-size: 15px; margin-bottom: 4px; }
.e9-dialogo small { color: var(--cap-3); display: block; font-size: 10.5px; margin-bottom: 10px; }
.e9-abas { background: #0f120f; border-radius: 9px; display: flex; gap: 3px; margin-bottom: 10px; padding: 3px; }
.e9-abas span { border-radius: 7px; color: var(--cap-3); flex: 1; font-size: 10.5px; font-weight: 600; padding: 6px 2px; text-align: center; }
.e9-abas span.on { background: #2a302b; color: #fff; }
.e9-texto { background: #0f120f; border: 1px solid rgba(255,255,255,0.1); border-radius: 9px; color: #e9e6df; font-family: var(--serif); font-size: 13.5px; line-height: 1.5; padding: 10px; }
.e9-oculto { background: rgba(141,219,166,0.16); border: 1px dashed rgba(141,219,166,0.6); border-radius: 4px; color: var(--hi); font-family: var(--sans); font-size: 11.5px; font-weight: 700; padding: 0 6px; }
.e9-bt { align-items: center; background: #22a055; border-radius: 9px; color: #fff; display: inline-flex; font-size: 13px; font-weight: 700; justify-content: center; padding: 9px 14px; }
.e9-bt.cinza { background: #2a302b; }
.e9-notas { display: grid; gap: 6px; grid-template-columns: repeat(4, 1fr); }
.e9-notas span { background: #1f2421; border: 1px solid rgba(255,255,255,0.12); border-radius: 9px; font-size: 12px; font-weight: 700; padding: 7px 2px; text-align: center; }
.e9-notas small { color: var(--cap-3); display: block; font-size: 10px; font-weight: 500; }
.e9-notas .errei { color: #ff9a8f; } .e9-notas .bom { border-color: var(--hi); color: var(--hi); }
.e9-aviso { align-items: center; background: #1f2421; border: 1px solid rgba(141,219,166,0.45); border-radius: 10px; color: var(--hi); display: inline-flex; font-size: 12.5px; font-weight: 700; gap: 7px; padding: 8px 12px; }
.e9-aviso svg { height: 15px; width: 15px; }
.e9-cursor { height: 22px; left: 0; position: absolute; top: 0; width: 22px; z-index: 50; }
.e9-resumo { background: var(--chip); border: 1px solid var(--chip-line); border-radius: 16px; left: 30px; padding: 18px; position: absolute; right: 66px; }
.e9-resumo div { display: flex; justify-content: space-between; padding: 7px 0; font-size: 15px; }
.e9-resumo b { color: var(--amber); }
.e9-origem { align-items: center; color: var(--cap-3); display: flex; font-size: 11.5px; gap: 7px; justify-content: center; left: 20px; position: absolute; right: 60px; }
.e9-origem img { height: 14px; width: 14px; }
`;

const CORES = ["#facc15", "#4ade80", "#60a5fa", "#f472b6"];
const AMARELO = "rgba(250,204,21,0.34)", VERDE = "rgba(74,222,128,0.30)", SELECAO = "rgba(96,165,250,0.40)";
const T1 = "liberdade de locomoção", T2 = "direito líquido e certo";

/** Pulso no tempo da música (1 na batida, decai em ~0,1 s). */
function pulso(t, ctx) {
    const bt = 60 / (ctx.config.bpm || 120);
    return Math.exp(-((t % bt) / 0.09));
}

/** Aleatório determinístico (mesmo quadro, mesmo resultado). */
const rnd = (i, k) => {
    const x = Math.sin(i * 12.9898 + k * 78.233) * 43758.5453;
    return x - Math.floor(x);
};

/** Explosão de confete a partir de (x, y) no instante `at`. */
function confete(t, at, x0, y0, n = 46, forca = 1) {
    const dt = t - at;
    if (dt < 0 || dt > 1.7) return "";
    const cores = ["#f2b766", "#8ddba6", "#60a5fa", "#f472b6", "#facc15"];
    let html = "";
    for (let i = 0; i < n; i++) {
        const vx = (rnd(i, 1) - 0.5) * 560 * forca, vy = -(220 + rnd(i, 2) * 460) * forca;
        const x = x0 + vx * dt, y = y0 + vy * dt + 0.5 * 950 * dt * dt;
        const tam = 5 + rnd(i, 3) * 6, giro = (rnd(i, 4) - 0.5) * 1400 * dt;
        const o = 1 - clamp((dt - 1.1) / 0.6);
        html += `<i style="background:${cores[i % cores.length]};border-radius:${rnd(i, 5) > 0.6 ? "50%" : "2px"};height:${(tam * 0.6).toFixed(1)}px;left:${x.toFixed(1)}px;opacity:${o.toFixed(2)};position:absolute;top:${y.toFixed(1)}px;transform:rotate(${giro.toFixed(0)}deg);width:${tam.toFixed(1)}px"></i>`;
    }
    return `<div style="inset:0;pointer-events:none;position:absolute;z-index:60">${html}</div>`;
}

/** Câmera da cena: zoom por quadros-chave em direção a um ponto, com o pulso da batida. */
function camera(t, ctx, chaves, origem, html, tremor = 0) {
    const s = track(t, chaves) * (1 + 0.012 * pulso(t, ctx));
    return `<div style="inset:0;position:absolute;transform-origin:${origem};transform:translate3d(${tremor.toFixed(2)}px,0,0) scale(${s.toFixed(4)})">${html}</div>`;
}

function inciso(ctx, d) {
    return ctx.ficha.fontes.find((f) => f.dispositivo === d).texto_literal;
}

/** Destaca `alvo` dentro do texto: seleção azul correndo (k_sel) e depois o grifo (cor). */
function marcar(html, alvo, ksel, cor) {
    if (ksel <= 0 && !cor) return html;
    const fundo = cor
        ? `background:${cor}`
        : `background-image:linear-gradient(${SELECAO},${SELECAO});background-repeat:no-repeat;background-size:${(ksel * 100).toFixed(1)}% 100%`;
    return html.replace(esc(alvo), `<span class="e9-sel" style="${fundo}">${esc(alvo)}</span>`);
}

function cursor(t, chaves, cliques) {
    if (!chaves.length || t < chaves[0][0] - 0.5) return "";
    const x = track(t, chaves.map(([tt, xx]) => [tt, xx]));
    const y = track(t, chaves.map(([tt, , yy]) => [tt, yy]));
    let anel = "";
    for (const c of cliques) {
        if (t >= c && t < c + 0.5) {
            const k = (t - c) / 0.5;
            anel = `<span style="border:2px solid var(--hi);border-radius:50%;height:34px;left:-10px;opacity:${(1 - k).toFixed(2)};position:absolute;top:-10px;transform:scale(${mix(0.4, 1.4, k).toFixed(2)});width:34px"></span>`;
        }
    }
    const aperta = cliques.some((c) => t >= c - 0.06 && t < c + 0.12) ? 0.85 : 1;
    return `<div class="e9-cursor" style="transform:translate3d(${x.toFixed(1)}px,${y.toFixed(1)}px,0)">${anel}
      <svg viewBox="0 0 28 28" width="22" height="22" style="transform:scale(${aperta})"><path d="M6 3.5v19.2l5.1-4.6 3.2 7.2 3.3-1.5-3.2-7h6.9z" fill="#fff" stroke="#111" stroke-linejoin="round" stroke-width="1.6"/></svg></div>`;
}

function cronometro(t) {
    const s = Math.min(30, Math.floor(t));
    return `00:${String(s).padStart(2, "0")}`;
}

function janela(t, url, corpo, top = 196) {
    return `<div class="e9-janela" style="top:${top}px">
      <div class="e9-barra"><i></i><i></i><i></i><span class="e9-url">${esc(url)}</span></div>
      <div class="e9-app"><span><img src="logo.png" alt="">ESTUDA LEGES</span><span class="e9-cron">⏱ ${cronometro(t)}</span></div>
      ${corpo}</div>`;
}

function passo(t, n, texto, at) {
    return `<div class="e9-topo" style="top:156px;z-index:45"><span class="e9-passo" style="${pop(t, at, { from: 0.85 })}"><b>${n}</b>${esc(texto)}</span></div>`;
}

function leitor(ctx, t, ks1, cor1, ks2, cor2) {
    let a = esc(inciso(ctx, "art. 5º, LXVIII")), b = esc(inciso(ctx, "art. 5º, LXIX"));
    a = marcar(a, T1, ks1, cor1);
    b = marcar(b, T2, ks2, cor2);
    return `<div class="e9-leitor"><h4>Constituição Federal · Art. 5º</h4><p>${a}</p><p>${b}</p></div>`;
}

// ── 1. Ler o inciso (gancho) ───────────────────────────────────────────────────────────────────
function abre(tl, ctx) {
    const t = ctx.t;
    const L = ctx.ficha.letreiros;
    // leitura: uma linha clara corre pelo texto (o olho lendo), para a tela não ficar parada
    const leitura = clamp((t - 0.6) / 4.6);
    return `<style>${css}</style>
    <div class="e9-topo" style="top:66px"><h1 class="titulo e9-gancho" style="transform:scale(${(1 + 0.035 * pulso(t, ctx)).toFixed(4)})">${destacar(ctx.gancho.tela)}</h1></div>
    ${passo(t, 1, L[0], 0.9)}
    ${camera(t, ctx, [[0, 1], [6, 1.05]], "50% 55%", janela(t, "estudaleges.com.br/biblioteca/constituicao-federal", leitor(ctx, t, 0, null, 0, null) +
        `<div style="background:linear-gradient(90deg,transparent,rgba(141,219,166,0.5),transparent);height:2px;left:14px;position:absolute;right:14px;top:${(96 + leitura * 230).toFixed(1)}px"></div>`))}`;
}

// ── 2. Grifar o que a banca troca ──────────────────────────────────────────────────────────────
function grifa(tl, ctx) {
    const t = ctx.t, c = ctx.timing.cues;
    const ks1 = prog(t, c.sel1, 0.9, EASE.inOut), cor1 = t >= c.cor1 ? AMARELO : null;
    const ks2 = prog(t, c.sel2, 0.9, EASE.inOut), cor2 = t >= c.cor2 ? VERDE : null;
    const barra1 = t >= c.barra1 && t < c.cor1 + 0.25, barra2 = t >= c.sel2 + 1.0 && t < c.cor2 + 0.25;
    const ferr = (top, at) => `<div class="e9-ferr" style="left:40px;top:${top}px;${pop(t, at, { from: 0.8 })}">
        ${CORES.map((cc) => `<i style="background:${cc}"></i>`).join("")}<span>Flashcard</span><span>Copiar</span></div>`;
    return `<style>${css}</style>
    ${selo(t, -1)}
    ${passo(t, 2, ctx.ficha.letreiros[1], ctx.cena.start + 0.2)}
    ${camera(t, ctx, [[ctx.cena.start, 1], [c.sel1 - 0.3, 1], [c.sel1 + 0.25, 1.2], [c.cor2 + 0.3, 1.2], [ctx.cena.end - 0.2, 1.04]], "42% 46%",
        janela(t, "estudaleges.com.br/biblioteca/constituicao-federal", leitor(ctx, t, ks1, cor1, ks2, cor2)) +
        (barra1 ? ferr(262, c.barra1) : "") + (barra2 ? ferr(372, c.sel2 + 1.0) : "") +
        cursor(t, [[c.sel1 - 0.4, 300, 330], [c.sel1, 150, 304], [c.sel1 + 0.9, 260, 322], [c.cor1, 56, 270], [c.sel2, 120, 412], [c.sel2 + 0.9, 300, 412], [c.cor2, 75, 380], [c.cor2 + 0.8, 250, 440]], [c.cor1, c.cor2]))}`;
}

// ── 3. Virar flashcard (Ocultar trecho) ────────────────────────────────────────────────────────
function flashcard(tl, ctx) {
    const t = ctx.t, c = ctx.timing.cues, ini = ctx.cena.start;
    const aberto = t >= c.botaoFlash + 0.15;
    const oculto = t >= c.ocultar;
    const texto = esc(inciso(ctx, "art. 5º, LXVIII").replace(/^LXVIII - /, "")).replace(esc(T1), oculto ? `<span class="e9-oculto">[ ... ]</span>` : `<span style="background:${AMARELO}">${esc(T1)}</span>`);
    const criado = t >= c.criar + 0.15;
    const dialogo = aberto && !criado ? `<div class="e9-dialogo" style="top:226px;${pop(t, c.botaoFlash + 0.15, { from: 0.92, bounce: 0.15 })}">
        <h5>Criar flashcard</h5><small>Deck · Direito Constitucional</small>
        <div class="e9-abas"><span>Frente/Verso</span><span>Verdadeiro ou Falso</span><span class="${oculto ? "on" : ""}">Ocultar trecho</span></div>
        <div class="e9-texto">${texto}</div>
        <div style="display:flex;justify-content:flex-end;margin-top:10px"><span class="e9-bt">Criar flashcard</span></div></div>` : "";
    return `<style>${css}</style>
    ${selo(t, -1)}
    ${passo(t, 3, ctx.ficha.letreiros[2], ini + 0.2)}
    ${camera(t, ctx, [[ini, 1], [c.botaoFlash + 0.1, 1], [c.botaoFlash + 0.5, 1.12], [c.criar, 1.12], [c.criar + 0.4, 1.0]], "45% 50%", janela(t, "estudaleges.com.br/biblioteca/constituicao-federal", leitor(ctx, t, 0, AMARELO, 0, VERDE) +
        (!aberto ? `<div class="e9-ferr" style="left:24px;top:66px;${pop(t, ini + 0.2, { from: 0.8 })}">${CORES.map((cc) => `<i style="background:${cc}"></i>`).join("")}<span style="background:${t >= c.botaoFlash - 0.1 ? "#2f3a32" : "transparent"};border-radius:6px">Flashcard</span><span>Copiar</span></div>` : "")))}
    <div style="background:rgba(0,0,0,${aberto && !criado ? 0.45 : 0});inset:0;position:absolute"></div>
    ${dialogo}
    ${criado ? `<div class="e9-topo" style="top:440px;right:60px"><span class="e9-aviso" style="${pop(t, c.criar + 0.15, { from: 0.8 })}">${ICONE.ok}Flashcard criado · Ocultar trecho</span></div>` : ""}
    ${cursor(t, [[ini + 0.2, 240, 420], [c.botaoFlash, 150, 278], [c.ocultar - 0.5, 200, 330], [c.ocultar, 300, 316], [c.criar - 0.4, 320, 470], [c.criar, 318, 452], [c.criar + 0.8, 330, 520]], [c.botaoFlash, c.ocultar, c.criar])}`;
}

// ── 4. Testar a memória ────────────────────────────────────────────────────────────────────────
function testa(tl, ctx) {
    const t = ctx.t, c = ctx.timing.cues, ini = ctx.cena.start;
    const revelou = t >= c.revela;
    const texto = esc(inciso(ctx, "art. 5º, LXVIII").replace(/^LXVIII - /, "")).replace(esc(T1), revelou
        ? `<span style="background:${AMARELO};border-radius:3px;padding:0 2px">${esc(T1)}</span>`
        : `<span class="e9-oculto">[ ... ]</span>`);
    const nota = t >= c.bom;
    const corpo = `<div style="padding:14px">
        <div class="e9-texto" style="font-size:15px">${texto}</div>
        <div style="color:var(--cap-3);font-size:10px;margin:8px 2px 12px">Art. 5º, LXVIII · Constituição Federal</div>
        ${revelou
            ? `<div class="e9-notas" style="${rise(t, c.revela + 0.1, { y: 8 })}">
                 <span class="errei">Errei<small>agora</small></span><span>Difícil<small>1d</small></span>
                 <span class="bom" style="${nota ? "background:rgba(34,160,85,0.25)" : ""}">Bom<small>1d</small></span><span>Fácil<small>4d</small></span></div>`
            : `<div style="text-align:center"><span class="e9-bt cinza" style="width:100%">Mostrar resposta</span></div>`}
      </div>`;
    return `<style>${css}</style>
    ${selo(t, -1)}
    ${passo(t, 4, ctx.ficha.letreiros[3], ini + 0.2)}
    ${camera(t, ctx, [[ini, 1], [c.revela - 0.2, 1], [c.revela + 0.3, 1.1], [c.bom - 0.1, 1.1], [c.bom + 0.5, 1.04]], "50% 42%",
        janela(t, "estudaleges.com.br/flashcards/revisar", corpo) +
        cursor(t, [[ini + 0.3, 300, 470], [c.mostrar, 200, 400], [c.bom - 0.5, 240, 420], [c.bom, 226, 410], [c.bom + 0.8, 300, 480]], [c.mostrar, c.bom]),
        shake(t, c.bom, 5))}
    ${nota ? `<div class="e9-topo" style="top:474px;right:60px"><span class="e9-aviso" style="${pop(t, c.volta, { from: 0.8 })}">${ICONE.ok}${esc(ctx.ficha.letreiros[4])}</span></div>` : ""}
    ${confete(t, c.bom, 226, 420)}`;
}

// ── 5. Fim ─────────────────────────────────────────────────────────────────────────────────────
function fim(tl, ctx) {
    const t = ctx.t, ini = ctx.cena.start;
    const valor = (v, i) => count(t, ini + 0.5 + i * 0.25, 0.5, 0, v);
    const linhas = [["Incisos lidos", valor(2, 0)], ["Grifos", valor(2, 1)], ["Flashcards", valor(1, 2)], ["Tempo", `${valor(30, 3)} s`]];
    return `<style>${css}</style>
    <div class="e9-topo" style="top:100px;right:60px">
      <p class="kicker ambar" style="${rise(t, ini + 0.05, { y: 8 })}">Sessão de hoje</p>
      <h2 class="titulo" style="font-size:40px;margin-top:12px;${rise(t, ini + 0.12)}">Amanhã ele <span class="ambar">volta</span>.</h2>
    </div>
    <div class="e9-resumo" style="top:236px;${rise(t, ini + 0.3, { y: 16 })}">
      ${linhas.map(([a, b], i) => `<div style="${rise(t, ini + 0.4 + i * 0.12, { y: 6 })}"><span>${a}</span><b>${b}</b></div>`).join("")}
    </div>
    <div class="e9-origem" style="top:470px;${rise(t, ini + 1.0, { y: 6 })}"><img src="logo.png" alt="">estudando no Estuda Leges</div>
    ${confete(t, ini + 0.3, 216, 200, 30, 0.8)}`;
}

const DESENHAR = { abre, grifa, flashcard, testa, fim };
const TRANSICOES = { grifa: "fade", flashcard: "fade", testa: "push", fim: "fade" };

/** Barra de progresso da sessão (passos 1–4) e clarão na entrada de cada cena, por cima de tudo. */
function sobreposicao(t, ctx) {
    const c = ctx.timing.scenes;
    const ordem = ["abre", "grifa", "flashcard", "testa"];
    let barra = "";
    if (t >= c.grifa.start - 0.2 && t < c.fim.start) {
        barra = ordem.map((id) => {
            const k = clamp((t - c[id].start) / (c[id].end - c[id].start));
            return `<i style="background:rgba(255,255,255,0.12);border-radius:3px;flex:1;height:5px;overflow:hidden;position:relative">
              <b style="background:var(--amber);inset:0;position:absolute;transform-origin:0 50%;transform:scaleX(${k.toFixed(3)});box-shadow:0 0 10px rgba(242,183,102,0.6)"></b></i>`;
        }).join("");
        barra = `<div style="display:flex;gap:5px;left:20px;position:absolute;right:60px;top:122px;z-index:45;${rise(t, c.grifa.start - 0.2, { y: -6 })}">${barra}</div>`;
    }
    let clarao = 0;
    for (const id of ["grifa", "flashcard", "testa", "fim"]) {
        const d = t - c[id].start;
        if (d >= 0 && d < 0.4) clarao = Math.max(clarao, 0.32 * Math.exp(-d / 0.09));
    }
    return barra + (clarao > 0.01 ? `<div style="background:#fff;inset:0;opacity:${clarao.toFixed(3)};position:absolute;z-index:80"></div>` : "");
}

export function quadro(t, ctx) {
    return compor(t, ctx.timing.scenes, DESENHAR, TRANSICOES, ctx) + (ctx.capa ? "" : sobreposicao(t, ctx));
}
