/**
 * Episódio #10 — teste de oferta: pegadinha da CF, art. 5º, XI (plano do usuário de 26/11/2026).
 * O vídeo não vende a assinatura: leva a criar a conta grátis de 7 dias. Narrado com a voz padrão.
 *
 * Cenas (eventos ligados às palavras, ver config.json):
 *   gancho    texto grande e inteiro no quadro 0 (A, B ou C)
 *   julgue    selo "Questão adaptada · Certo ou errado?" + "Julgue o item:"
 *   item      o item em fonte de prova
 *   contagem  ✅ CERTO / ❌ ERRADO + anel 3-2-1 + "Comenta antes de ver 👇"
 *   errado    "ERRADO." carimbado, "a qualquer hora" riscado
 *   lei       texto literal do XI com "durante o dia" grifado
 *   regra     sem consentimento, a qualquer hora: flagrante, desastre, socorro
 *   app       treino de literalidade do app com a troca que ele realmente gera (inviolável → violável)
 *   cta       logo, endereço e a oferta
 * Textos de tela: ficha.letreiros e ficha.item. Texto de lei: ficha.fontes[0].texto_literal.
 */
import { EASE, clamp, mix, pop, prog, rise, shake, spring, stamp } from "../motor.js";
import { ICONE, compor, destacar, esc, legenda, selo } from "../pecas.js";

const css = `
.e10-meio { left: 22px; position: absolute; right: 58px; text-align: center; }
.e10-grande { font-family: var(--display); font-size: 52px; line-height: 1.02; }
.e10-selo { border: 1.5px solid rgba(242,183,102,0.6); border-radius: 99px; color: var(--amber); display: inline-block; font-family: var(--mono);
  font-size: 12px; font-weight: 700; letter-spacing: 0.14em; padding: 7px 14px; text-transform: uppercase; }
.e10-prova { background: #f6f2e8; border-radius: 6px; color: #1d1d1b; font-family: "Times New Roman", var(--serif), serif; font-size: 21px; left: 22px;
  line-height: 1.45; padding: 18px 18px 20px; position: absolute; right: 58px; text-align: left; box-shadow: 0 2px 6px rgba(0,0,0,0.3), 0 26px 60px -20px rgba(0,0,0,0.7); }
.e10-prova small { color: #6b665b; display: block; font-family: var(--mono); font-size: 10px; letter-spacing: 0.12em; margin-bottom: 8px; text-transform: uppercase; }
.e10-risco { background: var(--red); height: 3px; left: 0; position: absolute; top: 55%; border-radius: 2px; }
.e10-bts { display: flex; gap: 12px; justify-content: center; left: 22px; position: absolute; right: 58px; }
.e10-bt { align-items: center; background: var(--chip); border: 1.5px solid var(--chip-line); border-radius: 14px; display: flex; font-size: 20px; font-weight: 800;
  gap: 8px; justify-content: center; padding: 13px 0; width: 160px; }
.e10-bt.certo { border-color: rgba(141,219,166,0.5); }
.e10-bt.errado { border-color: rgba(239,90,76,0.6); }
.e10-bt.vence { background: rgba(239,90,76,0.22); border-color: var(--red); color: #ffb4ab; box-shadow: 0 0 40px rgba(239,90,76,0.35); }
.e10-bt.apaga { opacity: 0.35; }
.e10-anel { left: 50%; position: absolute; transform: translateX(-50%); }
.e10-anel b { font-family: var(--display); font-size: 32px; font-weight: 400; left: 0; line-height: 60px; position: absolute; right: 0; text-align: center; }
.e10-lei { background: #121512; border: 1px solid rgba(255,255,255,0.14); border-radius: 14px; color: #e9e6df; font-family: var(--serif); font-size: 18px;
  left: 22px; line-height: 1.55; padding: 16px 18px; position: absolute; right: 58px; text-align: left; }
.e10-lei small { color: var(--cap-3); display: block; font-family: var(--mono); font-size: 10px; letter-spacing: 0.14em; margin-bottom: 8px; text-transform: uppercase; }
.e10-grifo { background-image: linear-gradient(rgba(250,204,21,0.38), rgba(250,204,21,0.38)); background-repeat: no-repeat; border-radius: 3px; }
.e10-chips { display: flex; flex-direction: column; gap: 10px; left: 40px; position: absolute; right: 76px; }
.e10-chips span { align-items: center; background: var(--chip); border: 1px solid rgba(141,219,166,0.45); border-radius: 12px; color: var(--hi); display: flex;
  font-size: 19px; font-weight: 700; gap: 10px; padding: 12px 14px; }
.e10-chips svg { height: 20px; width: 20px; }
.e10-janela { background: #161a17; border: 1px solid rgba(255,255,255,0.16); border-radius: 14px; left: 18px; overflow: hidden; position: absolute; right: 54px; text-align: left;
  box-shadow: 0 0 90px -20px rgba(92,196,127,0.22), 0 30px 60px -18px rgba(0,0,0,0.6); }
.e10-janela h5 { border-bottom: 1px solid rgba(255,255,255,0.08); font-size: 13px; padding: 11px 14px; }
.e10-trein { padding: 12px 14px 14px; }
.e10-prog { align-items: center; color: var(--cap-3); display: flex; font-size: 11px; justify-content: space-between; margin-bottom: 8px; }
.e10-prog span.chip { border-radius: 99px; color: var(--amber); font-size: 10.5px; padding: 3px 8px; border-color: rgba(242,183,102,0.45); }
.e10-kick { color: var(--cap-2); font-size: 12px; margin-bottom: 6px; }
.e10-stmt { color: #e9e6df; font-family: var(--serif); font-size: 15.5px; line-height: 1.5; margin-bottom: 10px; }
.e10-op { display: grid; gap: 8px; grid-template-columns: 1fr 1fr; }
.e10-op span { background: #1f2421; border: 1px solid rgba(255,255,255,0.14); border-radius: 9px; font-size: 13px; font-weight: 700; padding: 9px; text-align: center; }
.e10-op span.ok { background: rgba(34,160,85,0.22); border-color: var(--hi); color: var(--hi); }
.e10-fb { background: rgba(34,160,85,0.12); border: 1px solid rgba(141,219,166,0.4); border-radius: 9px; color: var(--hi); font-size: 12.5px; font-weight: 600; margin-top: 10px; padding: 9px 10px; }
.e10-letreiro { font-family: var(--display); font-size: 36px; line-height: 1.05; }
.e10-cta-bt { align-items: center; background: #22a055; border-radius: 12px; color: #fff; display: inline-flex; font-size: 19px; font-weight: 800; gap: 8px; padding: 12px 20px;
  box-shadow: 0 10px 30px -8px rgba(34,160,85,0.6); }
`;

const L = (ctx, i) => ctx.ficha.letreiros[i];
const QH = "a qualquer hora";

/** O item da prova; com `risco` (0–1), "a qualquer hora" ganha a linha vermelha. */
function prova(ctx, top, risco = 0, escala = 1, estilo = "") {
    const item = esc(ctx.ficha.item).replace(QH, `<span style="position:relative">${QH}<i class="e10-risco" style="width:${(risco * 100).toFixed(1)}%"></i></span>`);
    return `<div class="e10-prova" style="top:${top}px;transform:scale(${escala});transform-origin:50% 0;${estilo}"><small>Questão adaptada · CF, art. 5º, XI</small>${item}</div>`;
}

function anel(t, ini, fim, top) {
    if (t < ini - 0.1 || t >= fim) return "";
    const k = clamp((t - ini) / (fim - ini));
    const n = Math.max(1, 3 - Math.floor(k * 3));
    const r = 26, perim = 2 * Math.PI * r;
    return `<div class="e10-anel" style="top:${top}px;width:60px;height:60px;${pop(t, ini - 0.1, { from: 0.7 })}">
      <svg viewBox="0 0 60 60" width="60" height="60"><circle cx="30" cy="30" r="${r}" fill="none" stroke="rgba(255,255,255,0.12)" stroke-width="4"/>
      <circle cx="30" cy="30" r="${r}" fill="none" stroke="var(--amber)" stroke-width="4" stroke-linecap="round" stroke-dasharray="${perim.toFixed(1)}"
        stroke-dashoffset="${(perim * k).toFixed(1)}" transform="rotate(-90 30 30)"/></svg><b>${n}</b></div>`;
}

function gancho(tl, ctx) {
    const t = ctx.t;
    const zoom = mix(1, 1.05, prog(t, 0, ctx.cena.end, EASE.linear));
    return `<style>${css}</style>
    <div class="e10-meio" style="top:230px;transform:scale(${zoom.toFixed(4)})">
      <p class="kicker ambar" style="margin-bottom:16px">CF · art. 5º, XI</p>
      <h1 class="e10-grande">${destacar(ctx.gancho.tela)}</h1>
    </div>`;
}

function julgue(tl, ctx) {
    const t = ctx.t, ini = ctx.cena.start;
    return `<style>${css}</style>
    ${selo(t, ini)}
    <div class="e10-meio" style="top:250px">
      <span class="e10-selo" style="${pop(t, ini + 0.05, { from: 0.8 })}">Questão adaptada · Certo ou errado?</span>
      <h2 class="e10-grande" style="margin-top:22px;${rise(t, ini + 0.25)}">${esc(L(ctx, 0))}</h2>
    </div>`;
}

function item(tl, ctx) {
    const t = ctx.t, ini = ctx.cena.start;
    return `<style>${css}</style>
    ${selo(t, -1)}
    <div class="e10-meio" style="top:150px"><span class="e10-selo">Certo ou errado?</span></div>
    ${prova(ctx, 206, 0, 1, rise(t, ini + 0.05, { y: 30, scale: 0.96 }))}`;
}

function contagem(tl, ctx) {
    const t = ctx.t, c = ctx.timing.cues, ini = ctx.cena.start;
    return `<style>${css}</style>
    ${selo(t, -1)}
    ${prova(ctx, 120, 0, 0.88)}
    <div class="e10-bts" style="top:330px;${rise(t, ini + 0.05, { y: 16 })}">
      <span class="e10-bt certo">✅ CERTO</span><span class="e10-bt errado">❌ ERRADO</span>
    </div>
    ${anel(t, c.q, c.carimbo, 398)}
    <div class="e10-meio" style="top:470px;${rise(t, c.comenta, { y: 8 })}"><span style="font-size:20px;font-weight:800">${esc(L(ctx, 1))}</span></div>`;
}

function errado(tl, ctx) {
    const t = ctx.t, c = ctx.timing.cues;
    const dx = shake(t, c.carimbo, 7);
    return `<style>${css}</style>
    ${selo(t, -1)}
    <div style="inset:0;position:absolute;transform:translate3d(${dx.toFixed(2)}px,0,0)">
      ${prova(ctx, 120, prog(t, c.carimbo + 0.15, 0.35, EASE.inOut), 0.88)}
      <div class="e10-bts" style="top:330px">
        <span class="e10-bt certo apaga">✅ CERTO</span><span class="e10-bt errado vence" style="transform:scale(${mix(1, 1.08, spring(t, c.carimbo, { dur: 0.5, bounce: 0.3 }) * (1 - prog(t, c.carimbo + 0.6, 0.4))).toFixed(3)})">❌ ERRADO</span>
      </div>
      <div class="carimbo vermelho" style="font-size:46px;left:110px;top:400px;${stamp(t, c.carimbo, { rot: -8 })}">${esc(L(ctx, 2))}</div>
    </div>`;
}

function lei(tl, ctx) {
    const t = ctx.t, c = ctx.timing.cues, ini = ctx.cena.start;
    const k = prog(t, c.grifo - 0.1, 0.6, EASE.inOut);
    const alvo = "durante o dia, por determinação judicial";
    const texto = esc(ctx.ficha.fontes[0].texto_literal.replace(/^XI - /, "")).replace(alvo,
        `<span class="e10-grifo" style="background-size:${(k * 100).toFixed(1)}% 100%">${alvo}</span>`);
    return `<style>${css}</style>
    ${selo(t, -1)}
    <div class="e10-meio" style="top:126px"><h2 class="e10-letreiro" style="${rise(t, ini + 0.05)}">${destacar(L(ctx, 3).replace("DURANTE O DIA", "*DURANTE O DIA*"))}</h2></div>
    <div class="e10-lei" style="top:234px;${rise(t, ini + 0.2, { y: 24 })}"><small>CF, art. 5º, XI · texto oficial</small>${texto}</div>
    <div class="e10-meio" style="top:452px;${rise(t, c.grifo + 0.5, { y: 8 })}">
      <span class="chip" style="color:#ffb4ab;border-color:rgba(239,90,76,0.5)"><span style="position:relative">${QH}<i class="e10-risco" style="width:${(prog(t, c.grifo + 0.7, 0.35) * 100).toFixed(1)}%"></i></span> ✗</span></div>`;
}

function regra(tl, ctx) {
    const t = ctx.t, c = ctx.timing.cues, ini = ctx.cena.start;
    const itens = [["Flagrante", c.flagrante - 0.1], ["Desastre", c.flagrante + 0.45], ["Prestar socorro", c.flagrante + 1.0]];
    return `<style>${css}</style>
    ${selo(t, -1)}
    <div class="e10-meio" style="top:130px"><h2 class="e10-letreiro" style="${rise(t, ini + 0.05)}">${esc(L(ctx, 4))}</h2>
      <p style="color:var(--cap-2);font-size:19px;font-weight:700;margin-top:10px;${rise(t, ini + 0.3, { y: 8 })}">${esc(L(ctx, 5))}</p></div>
    <div class="e10-chips" style="top:270px">${itens.map(([n, at]) => `<span style="${pop(t, at, { from: 0.8 })}">${ICONE.ok}${n}</span>`).join("")}</div>`;
}

function app(tl, ctx) {
    const t = ctx.t, c = ctx.timing.cues, ini = ctx.cena.start;
    const clique = c.troca + 0.3, respondeu = t >= clique;
    const stmt = esc(ctx.ficha.fontes[0].texto_literal.replace(/^XI - /, "").replace("inviolável", "violável").replace(/, ou, durante o dia.*$/, " …"));
    return `<style>${css}</style>
    ${selo(t, -1)}
    <div class="e10-meio" style="top:112px"><h2 class="e10-letreiro" style="font-size:32px;${rise(t, ini + 0.05)}">${esc(t >= c.treine - 0.1 ? L(ctx, 7) : L(ctx, 6))}</h2></div>
    <div class="e10-janela" style="top:180px;${rise(t, ini + 0.15, { y: 26, scale: 0.97 })}">
      <h5>Treino de literalidade · Art. 5º</h5>
      <div class="e10-trein">
        <div class="e10-prog"><span>Questão 1</span><span class="chip">Pegadinha de palavra</span></div>
        <p class="e10-kick">Certo ou errado, segundo a letra da lei?</p>
        <p class="e10-stmt">${stmt}</p>
        <div class="e10-op"><span>Certo</span><span class="${respondeu ? "ok" : ""}">Errado</span></div>
        ${respondeu ? `<div class="e10-fb" style="${pop(t, clique, { from: 0.9 })}">✓ Acertou. A lei diz “inviolável”, não “violável”.</div>` : ""}
      </div>
    </div>`;
}

function cta(tl, ctx) {
    const t = ctx.t, c = ctx.timing.cues, ini = ctx.cena.start;
    return `<style>${css}</style>
    <div class="e10-meio" style="top:118px">
      <p style="align-items:center;display:inline-flex;font-size:13px;font-weight:700;gap:8px;letter-spacing:0.14em;${rise(t, ini + 0.05, { y: 8 })}"><img src="logo.png" style="height:22px;width:22px" alt="">ESTUDA LEGES</p>
      <h2 class="e10-letreiro" style="font-size:40px;margin-top:16px;${rise(t, ini + 0.12)}">${esc(L(ctx, 8))}</h2>
      <p class="verde" style="font-family:var(--display);font-size:34px;margin-top:6px;${rise(t, c.gratis - 0.2)}"><i>${esc(L(ctx, 9))}</i></p>
      <div style="margin-top:26px;${pop(t, c.perfil, { from: 0.85 })}"><span class="e10-cta-bt">Criar conta grátis →</span></div>
      <p style="color:var(--amber);font-size:14px;font-weight:700;margin-top:14px;${rise(t, c.gratis, { y: 6 })}">${esc(ctx.oferta.teste.replace(" de Premium", "").replace(", sem cartão", " · sem cartão"))}</p>
      <p style="color:var(--cap-3);font-family:var(--mono);font-size:13px;margin-top:10px;${rise(t, ini + 0.4, { y: 6 })}">estudaleges.com.br</p>
    </div>`;
}

/** Capa (ficha: "CERTO OU ERRADO?" e "a qualquer hora" riscado em vermelho, fundo escuro). */
function capa() {
    return `<style>${css}</style><div class="fundo" style="--g1x:68%;--g1y:16%;--g2x:14%;--g2y:88%"></div>
    <div class="e10-meio" style="top:200px">
      <p class="kicker ambar">CF · art. 5º, XI</p>
      <h1 class="e10-grande" style="font-size:66px;margin-top:18px">CERTO OU <span class="ambar">ERRADO</span>?</h1>
      <p style="color:#ffb4ab;font-family:var(--display);font-size:46px;margin-top:30px"><span style="position:relative">${QH}<i class="e10-risco" style="width:100%;height:5px"></i></span></p>
    </div>`;
}

const DESENHAR = { gancho, julgue, item, contagem, errado, lei, regra, app, cta };
const TRANSICOES = { julgue: "fade", item: "push", contagem: "fade", errado: "fade", lei: "push", regra: "fade", app: "zoom", cta: "fade" };

export function quadro(t, ctx) {
    if (ctx.capa) return capa();
    return compor(t, ctx.timing.scenes, DESENHAR, TRANSICOES, ctx) + legenda(t, ctx.timing.chunks);
}
