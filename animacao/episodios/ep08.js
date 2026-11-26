/**
 * Episódio #8 — "Desafio de literalidade #1" (formato A de producao/ESTRATEGIA_CONVERSAO.md).
 *
 * Três rodadas: um trecho LITERAL da CF (ficha.fontes[].texto_literal) aparece com a palavra-chave
 * escondida, como no flashcard "Ocultar trecho" do app; a voz pergunta, o anel conta 3 s, a resposta
 * entra com grifo. Sem oferta falada: o app aparece só como origem dos cartões, no fim, discreto.
 *
 * Cenas: desafio (gancho + 3 rodadas) e fim (placar e "quantas você acertou?").
 * Eventos (timing): q1/q2/q3 = fim da pergunta (começa a contagem), r1/r2/r3 = resposta falada,
 * c2/c3 = troca de cartão.
 */
import { EASE, clamp, mix, pop, prog, rise, spring } from "../motor.js";
import { ICONE, compor, destacar, esc, legenda, selo } from "../pecas.js";

/** As rodadas: trecho do dispositivo (de … até) e o termo escondido. */
const RODADAS = [
    { dispositivo: "art. 60, § 2º", rotulo: "CF, art. 60, § 2º · emenda", de: "A proposta", ate: "membros.", alvo: "três quintos", mostra: "3/5" },
    { dispositivo: "art. 66, § 1º", rotulo: "CF, art. 66, § 1º · veto", de: "Se o Presidente", ate: "recebimento", alvo: "quinze dias úteis", mostra: "15 dias úteis" },
    { dispositivo: "art. 62, § 3º", rotulo: "CF, art. 62, § 3º · medida provisória", de: "As medidas provisórias", ate: "igual período", alvo: "sessenta dias", mostra: "60 dias" },
];

const css = `
.e8-topo { left: 20px; position: absolute; right: 20px; text-align: center; }
.e8-gancho { font-size: 46px; }
.e8-placar { display: flex; gap: 6px; position: absolute; right: 64px; top: 66px; }
.e8-placar i { background: rgba(255,255,255,0.12); border-radius: 50%; display: block; height: 12px; width: 12px; }
.e8-placar i.on { background: var(--hi); box-shadow: 0 0 12px rgba(141,219,166,0.7); }
.e8-cartao { background: #121512; border: 1px solid rgba(255,255,255,0.14); border-radius: 16px; left: 22px; padding: 16px 18px 18px;
  position: absolute; right: 56px; box-shadow: 0 0 80px -24px rgba(92,196,127,0.25), 0 26px 50px -20px rgba(0,0,0,0.7); }
.e8-rot { align-items: center; color: var(--cap-3); display: flex; font-family: var(--mono); font-size: 10px; gap: 6px; justify-content: space-between;
  letter-spacing: 0.12em; margin-bottom: 10px; text-transform: uppercase; }
.e8-rot b { color: var(--amber); font-weight: 600; }
.e8-lei { color: #e9e6df; font-family: var(--serif); font-size: 18px; line-height: 1.55; }
.e8-lacuna { border-bottom: 2px dashed var(--amber); border-radius: 3px; color: transparent; display: inline-block; min-width: 96px; padding: 0 4px;
  background: rgba(242,183,102,0.10); text-align: center; }
.e8-resposta { border-radius: 3px; color: var(--amber); font-weight: 700; padding: 0 3px;
  background-image: linear-gradient(rgba(242,183,102,0.28), rgba(242,183,102,0.28)); background-repeat: no-repeat; }
.e8-anel { left: 50%; position: absolute; transform: translateX(-50%); }
.e8-anel b { font-family: var(--display); font-size: 30px; font-weight: 400; left: 0; line-height: 56px; position: absolute; right: 0; text-align: center; }
.e8-lista { display: flex; flex-direction: column; gap: 10px; left: 26px; position: absolute; right: 60px; }
.e8-lista div { align-items: baseline; background: var(--chip); border: 1px solid var(--chip-line); border-radius: 12px; display: flex; justify-content: space-between; padding: 12px 14px; }
.e8-lista small { color: var(--cap-3); font-family: var(--mono); font-size: 10.5px; letter-spacing: 0.1em; text-transform: uppercase; }
.e8-lista b { color: var(--amber); font-size: 19px; }
.e8-origem { align-items: center; color: var(--cap-3); display: flex; font-size: 11.5px; gap: 7px; justify-content: center; left: 20px; position: absolute; right: 60px; }
.e8-origem img { height: 14px; width: 14px; opacity: 0.85; }
`;

/** Trecho literal do dispositivo, com reticências quando não começa/termina no próprio texto. */
function trecho(ficha, r) {
    const lit = ficha.fontes.find((f) => f.dispositivo === r.dispositivo).texto_literal.replace(/^§ \d+º\s*/, "");
    const i = lit.indexOf(r.de), j = lit.indexOf(r.ate, i) + r.ate.length;
    let t = lit.slice(i, j);
    if (j < lit.length && !/[.;]$/.test(t)) t += " …";
    return t;
}

function anel(t, ini, fim, top) {
    if (t < ini - 0.15 || t >= fim) return "";
    const k = clamp((t - ini) / (fim - ini));
    const n = Math.max(1, 3 - Math.floor(k * 3));
    const r = 24, perim = 2 * Math.PI * r;
    return `<div class="e8-anel" style="top:${top}px;width:56px;height:56px;${pop(t, ini - 0.15, { from: 0.7 })}">
      <svg viewBox="0 0 56 56" width="56" height="56"><circle cx="28" cy="28" r="${r}" fill="none" stroke="rgba(255,255,255,0.12)" stroke-width="4"/>
      <circle cx="28" cy="28" r="${r}" fill="none" stroke="var(--amber)" stroke-width="4" stroke-linecap="round" stroke-dasharray="${perim.toFixed(1)}"
        stroke-dashoffset="${(perim * k).toFixed(1)}" transform="rotate(-90 28 28)"/></svg><b>${n}</b></div>`;
}

function cartao(t, ctx, i, ini, sai) {
    const c = ctx.timing.cues, r = RODADAS[i];
    const q = c[`q${i + 1}`], resp = c[`r${i + 1}`];
    const revelou = t >= resp - 0.05;
    const texto = trecho(ctx.ficha, r);
    const k = prog(t, resp - 0.05, 0.45, EASE.inOut);
    const pulso = revelou ? 0 : 0.5 + 0.5 * Math.sin(t * 5);
    const lacuna = revelou
        ? `<span class="e8-resposta" style="background-size:${(k * 100).toFixed(1)}% 100%;${pop(t, resp - 0.05, { from: 0.8, bounce: 0.3 })};display:inline-block">${esc(r.alvo)}</span>`
        : `<span class="e8-lacuna" style="background:rgba(242,183,102,${(0.08 + 0.1 * pulso).toFixed(3)})">${esc(r.alvo)}</span>`;
    const html = esc(texto).replace(esc(r.alvo), lacuna);
    // entra da direita e sai para a esquerda
    const e = i === 0 ? 1 : prog(t, ini, 0.5, EASE.soft);
    const x = sai !== undefined ? prog(t, sai, 0.45, EASE.soft) : 0;
    if (x >= 1) return "";
    const dx = (1 - e) * 420 - x * 420;
    return `<div class="e8-cartao" style="top:236px;transform:translate3d(${dx.toFixed(1)}px,0,0) rotate(${((1 - e) * 4 - x * 4).toFixed(2)}deg);opacity:${(e * (1 - x)).toFixed(3)}">
      <div class="e8-rot"><span>${esc(r.rotulo)}</span><b>${i + 1}/3</b></div>
      <div class="e8-lei">${html}</div>
    </div>
    ${anel(t, q, resp - 0.05, 470)}
    ${revelou ? `<div style="left:20px;position:absolute;right:60px;text-align:center;top:478px;${pop(t, resp, { from: 0.7 })}"><span class="chip ok" style="font-size:15px">${ICONE.ok}${esc(r.mostra)}</span></div>` : ""}`;
}

function desafio(tl, ctx) {
    const t = ctx.t, c = ctx.timing.cues;
    const acertos = [c.r1, c.r2, c.r3].filter((x) => t >= x).length;
    // o gancho encolhe para o título da rodada quando a 1ª pergunta começa
    const enc = prog(t, c.q1 - 2.2, 0.6, EASE.inOut);
    const brilho = 0.5 + 0.5 * Math.sin(t * 4);
    const gancho = destacar(ctx.gancho.tela).replace('<span class="ambar">', `<span class="ambar" style="text-shadow:0 0 ${(18 * brilho).toFixed(1)}px rgba(242,183,102,0.45)">`);
    let cartoes = "";
    const ini = [0, c.c2, c.c3];
    for (let i = 0; i < 3; i++) {
        if (t < ini[i] - 0.05) continue;
        cartoes += cartao(t, ctx, i, ini[i], ini[i + 1]);
    }
    return `<style>${css}</style>
    ${selo(t, c.q1 - 1.6)}
    <div class="e8-placar">${[0, 1, 2].map((i) => `<i class="${i < acertos ? "on" : ""}" style="transform:scale(${i === acertos - 1 ? mix(1.6, 1, spring(t, [c.r1, c.r2, c.r3][i], { dur: 0.5 })) : 1})"></i>`).join("")}</div>
    <div class="e8-topo" style="top:${mix(92, 104, enc).toFixed(1)}px">
      <p class="kicker ambar">Desafio de literalidade #1</p>
      <h1 class="titulo e8-gancho" style="margin-top:12px;font-size:${mix(46, 30, enc).toFixed(1)}px">${gancho}</h1>
    </div>
    ${cartoes}`;
}

function fim(tl, ctx) {
    const t = ctx.t, c = ctx.timing.cues, ini = ctx.cena.start;
    return `<style>${css}</style>
    <div class="e8-topo" style="top:96px;right:60px">
      <p class="kicker ambar" style="${rise(t, ini + 0.05, { y: 8 })}">Desafio de literalidade #1</p>
      <h2 class="titulo" style="font-size:44px;margin-top:12px;${rise(t, c.acertou - 0.3)}">Quantas você <span class="ambar">acertou</span>?</h2>
    </div>
    <div class="e8-lista" style="top:236px">
      ${RODADAS.map((r, i) => `<div style="${rise(t, ini + 0.15 + i * 0.12, { y: 14 })}"><small>${esc(r.rotulo.split(" · ")[0])}</small><b>${esc(r.mostra)}</b></div>`).join("")}
    </div>
    <div class="e8-origem" style="top:470px;${rise(t, ini + 0.8, { y: 6 })}"><img src="logo.png" alt="">cartões do treino de literalidade · Estuda Leges</div>`;
}

const DESENHAR = { desafio, fim };
const TRANSICOES = { fim: "fade" };

export function quadro(t, ctx) {
    return compor(t, ctx.timing.scenes, DESENHAR, TRANSICOES, ctx) + (ctx.capa ? "" : legenda(t, ctx.timing.chunks));
}
