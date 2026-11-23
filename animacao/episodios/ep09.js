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
import { EASE, clamp, mix, pop, prog, rise, spring, track } from "../motor.js";
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
    return `<div class="e9-topo" style="top:156px"><span class="e9-passo" style="${pop(t, at, { from: 0.85 })}"><b>${n}</b>${esc(texto)}</span></div>`;
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
    <div class="e9-topo" style="top:66px"><h1 class="titulo e9-gancho">${destacar(ctx.gancho.tela)}</h1></div>
    ${passo(t, 1, L[0], 0.9)}
    ${janela(t, "estudaleges.com.br/biblioteca/constituicao-federal", leitor(ctx, t, 0, null, 0, null) +
        `<div style="background:linear-gradient(90deg,transparent,rgba(141,219,166,0.5),transparent);height:2px;left:14px;position:absolute;right:14px;top:${(96 + leitura * 230).toFixed(1)}px"></div>`)}`;
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
    ${janela(t, "estudaleges.com.br/biblioteca/constituicao-federal", leitor(ctx, t, ks1, cor1, ks2, cor2))}
    ${barra1 ? ferr(262, c.barra1) : ""}${barra2 ? ferr(372, c.sel2 + 1.0) : ""}
    ${cursor(t, [[c.sel1 - 0.4, 300, 330], [c.sel1, 150, 304], [c.sel1 + 0.9, 260, 322], [c.cor1, 56, 270], [c.sel2, 120, 412], [c.sel2 + 0.9, 300, 412], [c.cor2, 75, 380], [c.cor2 + 0.8, 250, 440]], [c.cor1, c.cor2])}`;
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
    ${janela(t, "estudaleges.com.br/biblioteca/constituicao-federal", leitor(ctx, t, 0, AMARELO, 0, VERDE) +
        (!aberto ? `<div class="e9-ferr" style="left:24px;top:66px;${pop(t, ini + 0.2, { from: 0.8 })}">${CORES.map((cc) => `<i style="background:${cc}"></i>`).join("")}<span style="background:${t >= c.botaoFlash - 0.1 ? "#2f3a32" : "transparent"};border-radius:6px">Flashcard</span><span>Copiar</span></div>` : ""))}
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
    ${janela(t, "estudaleges.com.br/flashcards/revisar", corpo)}
    ${nota ? `<div class="e9-topo" style="top:474px;right:60px"><span class="e9-aviso" style="${pop(t, c.volta, { from: 0.8 })}">${ICONE.ok}${esc(ctx.ficha.letreiros[4])}</span></div>` : ""}
    ${cursor(t, [[ini + 0.3, 300, 470], [c.mostrar, 200, 400], [c.bom - 0.5, 240, 420], [c.bom, 226, 410], [c.bom + 0.8, 300, 480]], [c.mostrar, c.bom])}`;
}

// ── 5. Fim ─────────────────────────────────────────────────────────────────────────────────────
function fim(tl, ctx) {
    const t = ctx.t, ini = ctx.cena.start;
    const linhas = [["Incisos lidos", "2"], ["Grifos", "2"], ["Flashcards", "1"], ["Tempo", "30 s"]];
    return `<style>${css}</style>
    <div class="e9-topo" style="top:100px;right:60px">
      <p class="kicker ambar" style="${rise(t, ini + 0.05, { y: 8 })}">Sessão de hoje</p>
      <h2 class="titulo" style="font-size:40px;margin-top:12px;${rise(t, ini + 0.12)}">Amanhã ele <span class="ambar">volta</span>.</h2>
    </div>
    <div class="e9-resumo" style="top:236px;${rise(t, ini + 0.3, { y: 16 })}">
      ${linhas.map(([a, b], i) => `<div style="${rise(t, ini + 0.4 + i * 0.12, { y: 6 })}"><span>${a}</span><b>${b}</b></div>`).join("")}
    </div>
    <div class="e9-origem" style="top:470px;${rise(t, ini + 1.0, { y: 6 })}"><img src="logo.png" alt="">estudando no Estuda Leges</div>`;
}

const DESENHAR = { abre, grifa, flashcard, testa, fim };
const TRANSICOES = { grifa: "fade", flashcard: "fade", testa: "push", fim: "fade" };

export function quadro(t, ctx) {
    return compor(t, ctx.timing.scenes, DESENHAR, TRANSICOES, ctx);
}
