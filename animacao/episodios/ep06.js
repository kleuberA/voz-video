/**
 * Episódio #6 — "Se arrependeu da Black Friday? Você tem 7 dias" (CDC, art. 49).
 *
 * Cenas (tempos em videos/short-ep06-black-friday/timing*.json, eventos ligados às palavras):
 *   pedido  gancho: manchete inteira no quadro 0 + card do pedido com o calendário de 7 dias.
 *           Algo muda a cada ~1 s desde o início (diagnóstico: nada de tela parada no gancho).
 *   regras  1/3 internet ou telefone, sem motivo · 2/3 conta da entrega · 3/3 devolve tudo, estorno.
 *   virada  loja física: carimbo NÃO VALE.
 *   cta     o art. 49 (texto literal da ficha) numa janela do Estuda Leges + oferta + link no perfil.
 *
 * DADOS DE DEMONSTRAÇÃO: pedido, datas, valores e cartão são exemplos ilustrativos (marcados
 * "exemplo" na tela). Texto de lei: só o que está em ficha.fontes[].texto_literal.
 */
import { EASE, clamp, count, life, mix, pop, prog, rise, shake, spring, stamp, track } from "../motor.js";
import { ICONE, compor, destacar, esc, legenda, selo } from "../pecas.js";

const css = `
.e6-topo { left: 20px; position: absolute; right: 20px; text-align: center; }
.e6-l1 { font-size: 44px; }
.e6-l2 { font-size: 92px; line-height: 0.9; margin-top: 2px; }
.e6-l2b { font-size: 50px; margin-top: 6px; }
.e6-dias { display: flex; gap: 7px; justify-content: center; padding: 10px 16px 14px; }
.e6-dia { align-items: center; border: 1.5px solid rgba(31,36,33,0.22); border-radius: 7px; color: var(--paper-ink-2);
  display: flex; font-size: 12px; font-weight: 700; height: 34px; justify-content: center; width: 34px; }
.e6-dia.on { background: #1f8f4e; border-color: #1f8f4e; color: #fff; }
.e6-dia.esc { background: rgba(141,219,166,0.14); border-color: rgba(141,219,166,0.35); color: var(--cap-3); }
.e6-dia.esc.on { background: var(--hi); border-color: var(--hi); color: #0b1f14; }
.e6-status { align-items: center; background: rgba(31,143,78,0.12); border-radius: 99px; color: #187a43; display: inline-flex;
  font-family: var(--sans); font-size: 11.5px; font-weight: 700; gap: 5px; padding: 3px 9px; }
.e6-status svg { height: 13px; width: 13px; }
.e6-rot { color: var(--paper-ink-2); font-size: 9.5px; letter-spacing: 0.12em; padding: 0 16px; text-align: center; text-transform: uppercase; }
.e6-tit { font-size: 38px; }
.e6-nao { color: var(--red); }
.e6-linha-tempo { height: 4px; left: 64px; position: absolute; right: 92px; top: 312px; background: var(--chip-line); border-radius: 2px; }
.e6-marco { position: absolute; text-align: center; top: 292px; width: 120px; }
.e6-marco i { border-radius: 50%; display: block; height: 22px; margin: 0 auto 8px; width: 22px; }
.e6-marco b { display: block; font-size: 16px; }
.e6-marco small { color: var(--cap-3); font-size: 11.5px; }
.e6-x { color: var(--red); font-size: 12px; font-weight: 800; letter-spacing: 0.08em; margin-top: 4px; text-transform: uppercase; }
.e6-risco { background: var(--red); height: 2px; left: 12px; position: absolute; top: 50%; }
.e6-janela { background: #121512; border: 1px solid rgba(255,255,255,0.14); border-radius: 12px; left: 22px; overflow: hidden;
  position: absolute; right: 22px; box-shadow: 0 0 90px -20px rgba(92,196,127,0.22), 0 30px 60px -18px rgba(0,0,0,0.6); }
.e6-barra { align-items: center; background: #1b201c; display: flex; gap: 6px; padding: 8px 10px; }
.e6-barra i { background: #343a35; border-radius: 50%; height: 7px; width: 7px; }
.e6-url { background: #0c0f0c; border-radius: 6px; color: #8f8f87; flex: 1; font-size: 9.5px; margin-left: 6px; overflow: hidden;
  padding: 4px 8px; white-space: nowrap; }
.e6-lei { color: #e9e6df; font-family: var(--serif); font-size: 14.5px; line-height: 1.55; padding: 14px 16px 16px; }
.e6-lei b { font-weight: 700; }
.e6-mark { background-image: linear-gradient(rgba(242,183,102,0.42), rgba(242,183,102,0.42)); background-repeat: no-repeat; border-radius: 2px; }
.e6-seta { align-items: center; color: var(--hi); display: flex; font-size: 13px; font-weight: 700; gap: 8px; left: 24px; position: absolute; }
`;

/** Divide a frase do gancho em duas: "Se arrependeu da Black Friday? 7 dias." → [..., "7 dias."] */
function partes(tela) {
    const m = tela.match(/^(.+?[?.!])\s+(.+)$/) || tela.match(/^(.+?:)\s+(.+)$/);
    return m ? [m[1], m[2]] : [tela, ""];
}

function dias(t, inicio, passo, classe = "") {
    return Array.from({ length: 7 }, (_, i) => {
        const on = t >= inicio + i * passo;
        const k = on ? spring(t, inicio + i * passo, { dur: 0.4, bounce: 0.3 }) : 0;
        return `<span class="e6-dia ${classe} ${on ? "on" : ""}" style="transform:scale(${on ? mix(0.7, 1, k).toFixed(3) : 1})">${i + 1}</span>`;
    }).join("");
}

// ── Cena 1: o gancho ───────────────────────────────────────────────────────────────────────────
function pedido(tl, ctx) {
    const t = ctx.t;
    const [l1, l2] = partes(ctx.gancho.tela);
    const B = ctx.variante === "B";
    const pulso = 1 + 0.07 * Math.sin(Math.PI * clamp((t - 2.5) / 0.5)) * (t > 2.5 && t < 3 ? 1 : 0);
    const flutua = Math.sin(t * 1.3) * 2.5;
    const topo = B
        ? `<p class="kicker" style="${rise(t, 0)}">Código de Defesa do Consumidor · art. 49</p>
           <h1 class="titulo e6-l1" style="margin-top:12px">${destacar(l1.replace("NÃO", "*NÃO*"), "e6-nao")}</h1>
           <h1 class="titulo e6-l2b verde" style="transform:scale(${pulso.toFixed(4)})">${esc(l2)}</h1>`
        : `<p class="kicker">Código de Defesa do Consumidor · art. 49</p>
           <h1 class="titulo e6-l1" style="margin-top:12px">${esc(l1)}</h1>
           <h1 class="titulo e6-l2 ambar" style="transform:scale(${pulso.toFixed(4)});text-shadow:0 0 ${(40 * (pulso - 1) / 0.07).toFixed(1)}px rgba(242,183,102,0.5)">${esc(l2)}</h1>`;
    return `<style>${css}</style>
    <div class="e6-topo" style="top:${B ? 110 : 96}px">${topo}</div>
    <div class="papel" style="left:44px;right:62px;top:${B ? 288 : 296}px;transform:translate3d(0,${flutua.toFixed(2)}px,0)">
      <div class="cab">PEDIDO #48213 · BLACK FRIDAY<small>LOJA ON-LINE · EXEMPLO</small></div>
      <div class="linha"><span>1x Fone sem fio</span><span>R$ 279,90</span></div>
      <div class="linha"><span>Compra 27/11</span><span class="e6-status" style="${pop(t, 0.9, { from: 0.8 })}">${ICONE.ok}Entregue 02/12</span></div>
      <div class="e6-dias">${dias(t, 0.3, 0.13)}</div>
      <div class="e6-rot" style="padding-bottom:12px">dias para desistir, contados da entrega</div>
      <div class="carimbo claro" style="background:rgba(8,18,13,0.92);top:40px;font-size:18px;right:-18px;${stamp(t, 1.6, { rot: -5 })}">Pode desistir</div>
    </div>`;
}

// ── Cena 2: as três regras ─────────────────────────────────────────────────────────────────────
function regras(tl, ctx) {
    const t = ctx.t, c = ctx.timing.cues;
    const item = t < c.dois - 0.25 ? 1 : t < c.tres - 0.25 ? 2 : 3;
    const inicioItem = item === 1 ? ctx.cena.start : item === 2 ? c.dois - 0.25 : c.tres - 0.25;
    const fimItem = item === 1 ? c.dois - 0.25 : item === 2 ? c.tres - 0.25 : Infinity;
    const sai = (x) => (t >= fimItem - 0.3 ? `opacity:${(1 - prog(t, fimItem - 0.3, 0.3)).toFixed(3)};` : "");
    const fontes = ["CDC, art. 49", "CDC, art. 49", "CDC, art. 49, par. único · Decreto 7.962/2013, art. 5º, § 3º"];
    const titulos = ["Comprou *on-line*? *7 dias* pra desistir.", "Conta da *entrega*, não da compra.", "Devolvem *tudo*. No cartão, *estorno*."];
    let corpo = "";
    if (item === 1) {
        corpo = `
        <div style="display:flex;gap:12px;justify-content:center;left:20px;position:absolute;right:60px;top:262px">
          <span class="chip" style="font-size:17px;padding:12px 16px;${pop(t, c.internet - 0.15)}">${ICONE.web}Internet</span>
          <span class="chip" style="font-size:17px;padding:12px 16px;${pop(t, c.telefone - 0.15)}">${ICONE.fone}Telefone</span>
        </div>
        <div style="left:20px;position:absolute;right:60px;text-align:center;top:338px">
          <span class="chip ok" style="font-size:17px;padding:12px 16px;${pop(t, c.motivo - 0.45)}">${ICONE.ok}Sem explicar o motivo</span>
        </div>
        <div class="e6-dias" style="left:0;position:absolute;right:44px;top:410px">${dias(t, inicioItem + 0.5, 0.18, "esc")}</div>`;
    } else if (item === 2) {
        const xEntrega = prog(t, c.entrega - 0.1, 0.4);
        const xCompra = t >= c.compra - 0.1;
        corpo = `
        <div class="e6-linha-tempo"></div>
        <div class="e6-linha-tempo" style="background:var(--hi);right:auto;width:${(276 * prog(t, inicioItem + 0.2, c.entrega - inicioItem, EASE.inOut)).toFixed(1)}px"></div>
        <div class="e6-marco" style="left:4px;${rise(t, inicioItem + 0.15)}">
          <i style="background:${xCompra ? "var(--red)" : "var(--cap-3)"}"></i><b>Compra</b><small>27/11 · exemplo</small>
          <div class="e6-x" style="${pop(t, c.compra - 0.1, { from: 0.7 })}">não conta</div>
        </div>
        <div class="e6-marco" style="left:252px;${pop(t, c.entrega - 0.1, { from: 0.5 })}">
          <i style="background:var(--hi);box-shadow:0 0 ${(24 * xEntrega).toFixed(1)}px rgba(141,219,166,0.7)"></i><b class="verde">Entrega</b><small>02/12 · exemplo</small>
          <div class="e6-x" style="color:var(--hi)">dia 1</div>
        </div>
        <div class="e6-dias" style="left:0;position:absolute;right:44px;top:420px">${dias(t, c.entrega + 0.25, 0.14, "esc")}</div>`;
    } else {
        const estorno = prog(t, c.estornar - 0.1, 0.35, EASE.inOut);
        const total = t < c.estornar ? "366,30" : count(t, c.estornar, 0.6, 36630, 8640).toString().replace(/(\d+)(\d{2})$/, "$1,$2");
        corpo = `
        <div class="papel" style="left:40px;right:64px;top:236px;${rise(t, inicioItem + 0.1, { y: 30 })}">
          <div class="cab">FATURA · CARTÃO •••• 4821<small>DEZEMBRO/2026 · EXEMPLO</small></div>
          <div class="linha"><span>27/11 Loja on-line</span><span>R$ 279,90</span>
            <i class="e6-risco" style="width:${(296 * estorno).toFixed(1)}px"></i></div>
          <div class="linha"><span>29/11 Mercado</span><span>R$ 86,40</span></div>
          <div class="linha" style="border-top:1px dashed rgba(31,36,33,0.25);font-weight:700;padding:9px 16px 13px"><span>TOTAL</span><span style="color:${t >= c.estornar ? "#18864a" : "inherit"}">R$ ${total}</span></div>
          <div class="carimbo verde" style="font-size:20px;left:118px;top:52px;${stamp(t, c.estornar, { rot: -7 })}">Estornado</div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:center;gap:8px;left:20px;position:absolute;right:60px;top:410px">
          <span class="chip ok" style="font-size:16px;${pop(t, c.tudo - 0.1)}">${ICONE.ok}Devolução: R$ 279,90</span>
          <span style="color:var(--cap-2);font-size:13px;${rise(t, c.corrigido - 0.35, { y: 10 })}">na hora e corrigida</span>
        </div>`;
    }
    const k = spring(t, inicioItem, { dur: 0.5, bounce: 0.3 });
    return `<style>${css}</style>
    ${selo(t, ctx.cena.start + 0.2)}
    <div class="contador ambar" style="transform:scale(${mix(0.6, 1, k).toFixed(3)})">${item}<small>/3</small></div>
    <div class="e6-topo" style="top:112px;right:60px;${sai()}">
      <p class="kicker ambar" style="${rise(t, inicioItem + 0.05, { y: 8 })}">${esc(fontes[item - 1])}</p>
      <h2 class="titulo e6-tit" style="margin-top:12px;${rise(t, inicioItem + 0.12)}">${destacar(titulos[item - 1])}</h2>
    </div>
    <div style="${sai()}">${corpo}</div>`;
}

// ── Cena 3: a virada (loja física) ─────────────────────────────────────────────────────────────
function virada(tl, ctx) {
    const t = ctx.t, c = ctx.timing.cues, ini = ctx.cena.start;
    const dx = shake(t, c.naovale, 7);
    return `<style>${css}</style>
    ${selo(t, -1)}
    <div style="inset:0;position:absolute;transform:translate3d(${dx.toFixed(2)}px,${(dx * 0.4).toFixed(2)}px,0)">
      <div class="e6-topo" style="top:112px;right:60px">
        <p class="kicker ambar" style="${rise(t, ini + 0.1, { y: 8 })}">Atenção</p>
        <h2 class="titulo e6-tit" style="font-size:44px;margin-top:12px;${rise(t, ini + 0.15)}">E na <span class="ambar">loja física</span>?</h2>
      </div>
      <div class="papel" style="left:52px;right:72px;top:236px;transform:rotate(-2deg) ${t < ini + 0.2 ? "translate3d(0,40px,0)" : ""};${rise(t, ini + 0.2, { y: 40 })}">
        <div class="cab">LOJA DO SHOPPING<small>COMPRA NO BALCÃO · EXEMPLO</small></div>
        <div class="linha"><span>1x Tênis</span><span>R$ 349,90</span></div>
        <div class="linha" style="padding-bottom:16px"><span>Pagamento</span><span>cartão</span></div>
        <div class="carimbo vermelho" style="font-size:30px;left:58px;top:42px;${stamp(t, c.naovale, { rot: -9 })}">Não vale</div>
      </div>
      <div style="left:24px;position:absolute;right:64px;text-align:center;top:420px;${rise(t, c.naovale + 0.35, { y: 10 })}">
        <span class="chip" style="font-size:13.5px">${ICONE.loja}O art. 49 é para compra <b class="ambar" style="margin-left:-4px">fora</b> da loja</span>
      </div>
    </div>`;
}

// ── Cena 4: chamada ────────────────────────────────────────────────────────────────────────────
function marcar(texto, trechos, t) {
    let html = esc(texto);
    for (const { frase, at } of trechos) {
        const k = prog(t, at, 0.5, EASE.inOut);
        html = html.replace(esc(frase), `<span class="e6-mark" style="background-size:${(k * 100).toFixed(1)}% 100%">${esc(frase)}</span>`);
    }
    return html.replace(/^Art\. 49\./, "<b>Art. 49.</b>");
}

function cta(tl, ctx) {
    const t = ctx.t, c = ctx.timing.cues, ini = ctx.cena.start;
    const caput = ctx.ficha.fontes.find((f) => f.dispositivo === "art. 49, caput").texto_literal;
    const url = `estudaleges.com.br/leis/${ctx.ficha.link.lei}/${ctx.ficha.link.artigo}`;
    return `<style>${css}</style>
    <div class="e6-topo" style="top:84px">
      <p style="align-items:center;display:inline-flex;font-size:12px;font-weight:700;gap:7px;letter-spacing:0.14em;${rise(t, ini + 0.05, { y: 8 })}"><img src="logo.png" style="height:18px;width:18px" alt="">ESTUDA LEGES</p>
      <h2 class="titulo" style="font-size:44px;margin-top:10px;${rise(t, ini + 0.1)}">A lei inteira, <span class="verde"><i>grátis</i></span>.</h2>
    </div>
    <div class="e6-janela" style="top:190px;${rise(t, ini + 0.2, { y: 30, scale: 0.96 })}">
      <div class="e6-barra"><i></i><i></i><i></i><span class="e6-url">${esc(url)}</span></div>
      <div class="e6-lei">${marcar(caput, [{ frase: "no prazo de 7 dias", at: ini + 0.7 }, { frase: "ato de recebimento do produto", at: c.gratis - 0.2 }], t)}</div>
    </div>
    <div style="left:20px;position:absolute;right:60px;text-align:center;top:438px;${pop(t, c.gratis, { from: 0.8 })}">
      <span class="chip" style="border-color:rgba(242,183,102,0.5);color:var(--amber);font-size:13px">${esc(ctx.oferta.teste.replace("7 dias de Premium grátis, sem cartão", "7 dias de Premium grátis · sem cartão"))}</span>
    </div>
    <div class="e6-seta" style="top:484px;${rise(t, c.perfil - 0.1, { y: 8 })}">
      <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" style="transform:rotate(${track(t, [[c.perfil, -10], [c.perfil + 0.6, 6], [c.perfil + 1.2, -6]]).toFixed(1)}deg)"><path d="M17 3c-6 2-10 7-11 15M6 18l-3-4M6 18l4-3"/></svg>
      Link no perfil: toque no nome do canal
    </div>`;
}

const DESENHAR = { pedido, regras, virada, cta };
const TRANSICOES = { regras: "push", virada: "zoom", cta: "fade" };

export function quadro(t, ctx) {
    const cenas = ctx.timing.scenes;
    // legenda some no fim (sobra só a chamada na tela)
    return compor(t, cenas, DESENHAR, TRANSICOES, ctx) + legenda(t, ctx.timing.chunks);
}
