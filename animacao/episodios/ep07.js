/**
 * Episódio #7 — "Tortura é crime imprescritível?" (CF, art. 5º, XLII a XLIV). O primeiro feito para
 * CONVERSÃO: a chamada mostra o caminho real até o cadastro (link no perfil → art. 5º → botão
 * "Treinar literalidade" com cadeado → "Criar conta grátis"), que é o que a página pública faz
 * (app/leis/public-law-reader.tsx no juris-app).
 *
 * Cenas (tempos em timing*.json, eventos ligados às palavras):
 *   quiz       afirmação inteira no quadro 0, Certo/Errado, contagem, revelação "Errado", PRESCREVE.
 *   lista      imprescritíveis na CF: só 2 (racismo, XLII; grupos armados, XLIV).
 *   contraste  tortura, tráfico, terrorismo, hediondos (XLIII): inafiançáveis, sem graça nem anistia, PRESCREVEM.
 *   treino     exemplo de questão do treino de literalidade: o XLII com uma palavra trocada.
 *   cta        o caminho até a conta grátis + oferta.
 * Texto de lei: só ficha.fontes[].texto_literal.
 */
import { EASE, clamp, mix, pop, prog, rise, shake, spring, stamp, track } from "../motor.js";
import { ICONE, compor, destacar, esc, legenda, selo } from "../pecas.js";

const css = `
.e7-topo { left: 20px; position: absolute; right: 20px; text-align: center; }
.e7-afirma { font-size: 50px; }
.e7-mark { background-image: linear-gradient(rgba(242,183,102,0.35), rgba(242,183,102,0.35)); background-position: 0 88%;
  background-repeat: no-repeat; border-radius: 3px; }
.e7-botoes { display: flex; gap: 12px; justify-content: center; left: 28px; position: absolute; right: 28px; }
.e7-bt { align-items: center; background: var(--chip); border: 1.5px solid var(--chip-line); border-radius: 14px; display: flex;
  font-size: 20px; font-weight: 700; gap: 8px; justify-content: center; padding: 13px 0; width: 160px; }
.e7-bt svg { height: 20px; width: 20px; }
.e7-bt.certa { background: rgba(34,160,85,0.22); border-color: var(--hi); color: var(--hi); box-shadow: 0 0 40px rgba(141,219,166,0.3); }
.e7-bt.apagada { opacity: 0.35; }
.e7-anel { left: 50%; position: absolute; transform: translateX(-50%); }
.e7-anel b { font-family: var(--display); font-size: 34px; font-weight: 400; left: 0; line-height: 64px; position: absolute; right: 0; text-align: center; }
.e7-tit { font-size: 40px; }
.e7-card { background: var(--chip); border: 1px solid var(--chip-line); border-radius: 16px; left: 28px; padding: 16px 18px; position: absolute; right: 64px; }
.e7-card b { display: block; font-size: 22px; }
.e7-card small { color: var(--cap-3); font-family: var(--mono); font-size: 10.5px; letter-spacing: 0.14em; text-transform: uppercase; }
.e7-card.ok { border-color: rgba(141,219,166,0.5); box-shadow: 0 0 40px -10px rgba(141,219,166,0.35); }
.e7-grade { display: grid; gap: 10px; grid-template-columns: 1fr 1fr; left: 28px; position: absolute; right: 64px; }
.e7-grade span { background: var(--chip); border: 1px solid var(--chip-line); border-radius: 12px; font-size: 17px; font-weight: 700; padding: 13px 10px; text-align: center; }
.e7-check { align-items: center; color: var(--hi); display: flex; font-size: 15px; font-weight: 600; gap: 8px; }
.e7-check svg { height: 17px; width: 17px; }
.e7-lei { background: #121512; border: 1px solid rgba(255,255,255,0.14); border-radius: 14px; color: #e9e6df; font-family: var(--serif);
  font-size: 16.5px; left: 24px; line-height: 1.55; padding: 16px 18px; position: absolute; right: 60px; }
.e7-lei .rot { color: var(--cap-3); display: block; font-family: var(--mono); font-size: 10px; letter-spacing: 0.14em; margin-bottom: 8px; text-transform: uppercase; }
.e7-troca { border-radius: 3px; padding: 0 2px; }
.e7-passo { align-items: center; display: flex; gap: 12px; left: 28px; position: absolute; right: 64px; }
.e7-passo i { align-items: center; background: var(--amber); border-radius: 50%; color: #1b1407; display: flex; flex: none; font-size: 14px;
  font-style: normal; font-weight: 800; height: 28px; justify-content: center; width: 28px; }
.e7-passo span { font-size: 17px; font-weight: 600; }
.e7-botao-app { align-items: center; background: #1b201c; border: 1px solid rgba(255,255,255,0.16); border-radius: 9px; color: #e9e6df; display: inline-flex;
  font-size: 14px; font-weight: 600; gap: 7px; padding: 8px 12px; position: relative; }
.e7-botao-app svg { height: 15px; width: 15px; }
.e7-criar { align-items: center; background: #22a055; border-radius: 12px; color: #fff; display: inline-flex; font-size: 18px; font-weight: 800; gap: 8px;
  padding: 12px 20px; box-shadow: 0 10px 30px -8px rgba(34,160,85,0.6); }
.e7-toque { border: 2px solid var(--hi); border-radius: 50%; height: 40px; position: absolute; width: 40px; }
`;

const CADEADO = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>`;
const LISTA = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6h11M9 12h11M9 18h11M4 6l1 1 2-2M4 12l1 1 2-2M4 18l1 1 2-2"/></svg>`;

/** Marca-texto que corre sob os trechos *destacados* (k de 0 a 1). */
function marcar(html, k) {
    return html.replace(/<span class="ambar">([^<]+)<\/span>/g, `<span class="ambar e7-mark" style="background-size:${(k * 100).toFixed(1)}% 34%">$1</span>`);
}

// ── Cena 1: o quiz ─────────────────────────────────────────────────────────────────────────────
function quiz(tl, ctx) {
    const t = ctx.t, c = ctx.timing.cues;
    const revelou = c.reveal !== undefined && t >= c.reveal;
    const k = prog(t, 0.45, 0.6, EASE.inOut);
    let afirma = marcar(destacar(ctx.gancho.tela), k);
    // na revelação, o termo destacado é riscado
    const risco = revelou ? prog(t, c.reveal, 0.35, EASE.inOut) : 0;
    if (risco > 0) afirma = afirma.replace(/(<span class="ambar e7-mark"[^>]*>)/, `$1<span style="background:linear-gradient(var(--red),var(--red)) no-repeat 0 55%/${(risco * 100).toFixed(1)}% 3px">`).replace(/(e7-mark"[^>]*><span[^>]*>[^<]+)/, "$1</span>");
    const pulso = (at) => 1 + 0.05 * Math.sin(Math.PI * clamp((t - at) / 0.4)) * (t > at && t < at + 0.4 ? 1 : 0);
    // contagem: 3, 2, 1 no anel (timer → reveal)
    let anel = "";
    if (c.timer !== undefined && t >= c.timer - 0.2 && !revelou) {
        const k2 = clamp((t - c.timer) / (c.reveal - c.timer));
        const n = Math.max(1, 3 - Math.floor(k2 * 3));
        const r = 28, perim = 2 * Math.PI * r;
        anel = `<div class="e7-anel" style="top:384px;width:64px;height:64px;${pop(t, c.timer - 0.2, { from: 0.7 })}">
          <svg viewBox="0 0 64 64" width="64" height="64"><circle cx="32" cy="32" r="${r}" fill="none" stroke="rgba(255,255,255,0.12)" stroke-width="4"/>
          <circle cx="32" cy="32" r="${r}" fill="none" stroke="var(--amber)" stroke-width="4" stroke-linecap="round" stroke-dasharray="${perim.toFixed(1)}"
            stroke-dashoffset="${(perim * k2).toFixed(1)}" transform="rotate(-90 32 32)"/></svg><b>${n}</b></div>`;
    }
    const cls = (certa) => (revelou ? (certa ? "certa" : "apagada") : "");
    const sobe = revelou ? spring(t, c.reveal, { dur: 0.5, bounce: 0.3 }) : 0;
    return `<style>${css}</style>
    <div class="e7-topo" style="top:104px">
      <p class="kicker ambar">Pegadinha de prova · CF, art. 5º</p>
      <h1 class="titulo e7-afirma" style="margin-top:16px">${afirma}</h1>
    </div>
    <div class="e7-botoes" style="top:300px">
      <span class="e7-bt ${cls(false)}" style="${revelou ? "" : pop(t, 0.9, { from: 0.85 })};transform:scale(${pulso(2.2).toFixed(3)})">${revelou ? ICONE.nao : ""}Certo</span>
      <span class="e7-bt ${cls(true)}" style="${revelou ? `transform:scale(${mix(1, 1.08, sobe * (1 - prog(t, c.reveal + 0.5, 0.4))).toFixed(3)})` : pop(t, 1.15, { from: 0.85 }) + `;transform:scale(${pulso(2.4).toFixed(3)})`}">${revelou ? ICONE.ok : ""}Errado</span>
    </div>
    ${anel}
    <div class="carimbo claro" style="font-size:30px;left:118px;top:392px;${stamp(t, c.prescreve - 0.1, { rot: -6 })}">Prescreve</div>`;
}

// ── Cena 2: só dois imprescritíveis ────────────────────────────────────────────────────────────
function lista(tl, ctx) {
    const t = ctx.t, c = ctx.timing.cues, ini = ctx.cena.start;
    return `<style>${css}</style>
    ${selo(t, ini + 0.2)}
    <div class="e7-topo" style="top:112px;right:60px">
      <p class="kicker ambar" style="${rise(t, ini + 0.05, { y: 8 })}">CF, art. 5º, XLII e XLIV</p>
      <h2 class="titulo e7-tit" style="margin-top:12px;${rise(t, ini + 0.12)}">Imprescritíveis na CF: <span class="ambar">só 2</span>.</h2>
    </div>
    <div class="e7-card ok" style="top:236px;${pop(t, c.racismo - 0.1, { from: 0.85 })}"><small>Inciso XLII</small><b>Racismo</b></div>
    <div class="e7-card ok" style="top:326px;${pop(t, c.grupos - 0.1, { from: 0.85 })}"><small>Inciso XLIV</small><b>Ação de grupos armados contra a ordem constitucional</b></div>`;
}

// ── Cena 3: os que prescrevem ──────────────────────────────────────────────────────────────────
function contraste(tl, ctx) {
    const t = ctx.t, c = ctx.timing.cues, ini = ctx.cena.start;
    const dx = shake(t, c.prescrevem, 6);
    return `<style>${css}</style>
    ${selo(t, -1)}
    <div style="inset:0;position:absolute;transform:translate3d(${dx.toFixed(2)}px,0,0)">
      <div class="e7-topo" style="top:112px;right:60px">
        <p class="kicker ambar" style="${rise(t, ini + 0.05, { y: 8 })}">CF, art. 5º, XLIII</p>
        <h2 class="titulo e7-tit" style="margin-top:12px;${rise(t, ini + 0.12)}">E a <span class="ambar">tortura</span>?</h2>
      </div>
      <div class="e7-grade" style="top:220px">
        <span style="${pop(t, c.tortura - 0.1, { from: 0.8 })}">Tortura</span>
        <span style="${pop(t, c.trafico - 0.1, { from: 0.8 })}">Tráfico</span>
        <span style="${pop(t, c.terrorismo - 0.1, { from: 0.8 })}">Terrorismo</span>
        <span style="${pop(t, c.hediondos - 0.1, { from: 0.8 })}">Hediondos</span>
      </div>
      <div style="display:flex;flex-direction:column;gap:10px;left:40px;position:absolute;top:350px">
        <span class="e7-check" style="${rise(t, c.inafiancaveis - 0.2, { y: 8 })}">${ICONE.ok}Inafiançáveis</span>
        <span class="e7-check" style="${rise(t, c.anistia - 0.4, { y: 8 })}">${ICONE.ok}Sem graça nem anistia</span>
      </div>
      <div class="carimbo vermelho" style="font-size:34px;left:96px;top:246px;${stamp(t, c.prescrevem, { rot: -8 })}">Prescrevem</div>
    </div>`;
}

// ── Cena 4: o treino troca uma palavra ─────────────────────────────────────────────────────────
function treino(tl, ctx) {
    const t = ctx.t, c = ctx.timing.cues, ini = ctx.cena.start;
    const xlii = ctx.ficha.fontes.find((f) => f.dispositivo === "art. 5º, XLII").texto_literal.replace(/^XLII - /, "");
    const trocou = t >= c.troca;
    const k = prog(t, c.troca, 0.3);
    const palavra = trocou
        ? `<span class="e7-troca" style="background:rgba(239,90,76,${(0.28 * k).toFixed(3)});color:${k > 0.5 ? "#ffb4ab" : "inherit"}">afiançável</span>`
        : `<span class="e7-troca">inafiançável</span>`;
    const texto = esc(xlii).replace("inafiançável", "\u0000").replace("\u0000", palavra);
    return `<style>${css}</style>
    ${selo(t, -1)}
    <div class="e7-topo" style="top:112px;right:60px">
      <p class="kicker ambar" style="${rise(t, ini + 0.05, { y: 8 })}">Treino de literalidade · exemplo</p>
      <h2 class="titulo e7-tit" style="margin-top:12px;${rise(t, ini + 0.12)}">A banca troca <span class="ambar">uma palavra</span>.</h2>
    </div>
    <div class="e7-lei" style="top:226px;${rise(t, ini + 0.2, { y: 24 })}"><span class="rot">Certo ou errado? · art. 5º, XLII</span>${texto}</div>
    <div class="e7-botoes" style="top:400px;transform:scale(0.86)">
      <span class="e7-bt" style="${rise(t, c.leu - 0.2, { y: 10 })}">Certo</span>
      <span class="e7-bt ${t >= c.treinar ? "certa" : ""}" style="${rise(t, c.leu - 0.1, { y: 10 })}">${t >= c.treinar ? ICONE.ok : ""}Errado</span>
    </div>`;
}

// ── Cena 5: o caminho até a conta ──────────────────────────────────────────────────────────────
function cta(tl, ctx) {
    const t = ctx.t, c = ctx.timing.cues, ini = ctx.cena.start;
    const toque = t >= c.toca && t < c.toca + 0.6 ? (t - c.toca) / 0.6 : -1;
    return `<style>${css}</style>
    <div class="e7-topo" style="top:84px">
      <p style="align-items:center;display:inline-flex;font-size:12px;font-weight:700;gap:7px;letter-spacing:0.14em;${rise(t, ini + 0.05, { y: 8 })}"><img src="logo.png" style="height:18px;width:18px" alt="">ESTUDA LEGES</p>
      <h2 class="titulo" style="font-size:40px;margin-top:10px;${rise(t, ini + 0.1)}">Treine o art. 5º com uma conta <span class="verde"><i>grátis</i></span>.</h2>
    </div>
    <div class="e7-passo" style="top:222px;${rise(t, c.perfil - 0.15, { y: 10 })}"><i>1</i><span>Link no perfil</span></div>
    <div class="e7-passo" style="top:272px;${rise(t, c.toca - 0.25, { y: 10 })}"><i>2</i><span>Art. 5º →</span>
      <span class="e7-botao-app">${LISTA}Treinar literalidade${CADEADO}
        ${toque >= 0 ? `<span class="e7-toque" style="left:${50}%;top:50%;opacity:${(1 - toque).toFixed(3)};transform:translate(-50%,-50%) scale(${mix(0.4, 1.6, EASE.out(toque)).toFixed(3)})"></span>` : ""}</span></div>
    <div class="e7-passo" style="top:326px;${rise(t, c.cria - 0.15, { y: 10 })}"><i>3</i><span class="e7-criar" style="transform:scale(${(1 + 0.05 * Math.sin(Math.PI * clamp((t - c.cria - 0.3) / 0.5))).toFixed(3)})">Criar conta grátis →</span></div>
    <div style="left:20px;position:absolute;right:60px;text-align:center;top:410px;${pop(t, c.gratis, { from: 0.8 })}">
      <span class="chip" style="border-color:rgba(242,183,102,0.5);color:var(--amber);font-size:13px">${esc(ctx.oferta.teste.replace(", sem cartão", " · sem cartão"))}</span>
    </div>
    <div class="e6-seta" style="align-items:center;color:var(--hi);display:flex;font-size:13px;font-weight:700;gap:8px;left:24px;position:absolute;top:470px;${rise(t, c.perfil + 0.6, { y: 8 })}">
      <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" style="transform:rotate(${track(t, [[c.perfil + 0.6, -10], [c.perfil + 1.2, 6], [c.perfil + 1.8, -6]]).toFixed(1)}deg)"><path d="M17 3c-6 2-10 7-11 15M6 18l-3-4M6 18l4-3"/></svg>
      Link no perfil: toque no nome do canal
    </div>`;
}

const DESENHAR = { quiz, lista, contraste, treino, cta };
const TRANSICOES = { lista: "push", contraste: "push", treino: "zoom", cta: "fade" };

export function quadro(t, ctx) {
    return compor(t, ctx.timing.scenes, DESENHAR, TRANSICOES, ctx) + (ctx.capa ? "" : legenda(t, ctx.timing.chunks));
}
