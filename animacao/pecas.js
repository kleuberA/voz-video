/**
 * Peças comuns dos Shorts: fundo, selo da marca, legenda palavra por palavra, ícones e a troca
 * entre cenas. Cada função recebe `t` e devolve HTML (texto): a página troca o conteúdo do palco a
 * cada quadro, sem transições CSS.
 */
import { EASE, clamp, mix, prog } from "./motor.js";

export const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

/** Fundo com a luz que deriva devagar (contínua entre as cenas). */
export function fundo(t) {
    const v = `--g1x:${(68 + Math.sin(t * 0.21) * 8).toFixed(2)}%;--g1y:${(16 + Math.cos(t * 0.17) * 7).toFixed(2)}%;` +
        `--g2x:${(14 + Math.cos(t * 0.13) * 6).toFixed(2)}%;--g2y:${(88 + Math.sin(t * 0.19) * 5).toFixed(2)}%;`;
    return `<div class="fundo" style="${v}"></div>`;
}

export function selo(t, at) {
    const o = prog(t, at, 0.4);
    return `<div class="selo" style="opacity:${o.toFixed(3)}"><img src="logo.png" alt="">Estuda Leges</div>`;
}

/** Destaque: trechos entre *asteriscos* ganham a classe dada (padrão: âmbar). */
export function destacar(texto, classe = "ambar") {
    return esc(texto).replace(/\*([^*]+)\*/g, `<span class="${classe}">$1</span>`);
}

/**
 * Legenda: mostra o bloco (até 3 palavras) que está sendo dito; a palavra acende quando é falada e
 * as "quentes" ficam em âmbar. Cada bloco entra com um leve pop.
 */
export function legenda(t, chunks, { ate = Infinity } = {}) {
    if (t >= ate) return "";
    const c = chunks.find((ch, i) => t >= ch.s - 0.05 && t < (chunks[i + 1] ? Math.min(chunks[i + 1].s - 0.05, ch.e + 0.6) : ch.e + 0.6));
    if (!c) return "";
    const k = prog(t, c.s - 0.05, 0.18);
    const palavras = c.words.map((w) => {
        const dita = t >= w.s;
        const cls = w.hot && dita ? "quente" : dita ? "dita" : "";
        const pulo = dita ? 1 + 0.12 * (1 - prog(t, w.s, 0.22)) : 1;
        return `<span class="${cls}" style="transform:scale(${pulo.toFixed(3)})">${esc(w.w)}</span>`;
    }).join(" ");
    return `<div class="legenda"><div class="legenda-linha" style="opacity:${k.toFixed(3)};transform:scale(${mix(0.92, 1, k).toFixed(3)})">${palavras}</div></div>`;
}

export const ICONE = {
    web: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/></svg>`,
    fone: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.5c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/></svg>`,
    ok: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>`,
    nao: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>`,
    loja: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l1.5-5h15L21 9M3 9h18v11H3zM9 20v-6h6v6"/></svg>`,
    caixa: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8 12 3 3 8v8l9 5 9-5zM3 8l9 5 9-5M12 13v8"/></svg>`,
};

/**
 * Compõe as cenas: cada cena é uma camada opaca que entra por cima da anterior. `cenas` vem do
 * timing ({id: {start, end}}); `desenhar[id](tLocal, ctx)` devolve o HTML da cena.
 * Transições: "push" (sobe), "fade" ou "zoom".
 */
export function compor(t, cenas, desenhar, transicoes, ctx) {
    const ids = Object.keys(cenas);
    const DUR = 0.55;
    let html = "";
    ids.forEach((id, i) => {
        const c = cenas[id];
        const prox = ids[i + 1] ? cenas[ids[i + 1]] : null;
        const de = i === 0 ? -1 : c.start - DUR / 2;
        const ate = prox ? prox.start + DUR / 2 : Infinity;
        if (t < de || t >= ate) return;
        const tipo = transicoes[id] || "push";
        const e = i === 0 ? 1 : prog(t, de, DUR, EASE.soft);
        const x = prox ? prog(t, prox.start - DUR / 2, DUR, EASE.soft) : 0;
        let estilo = "";
        if (e < 1) {
            if (tipo === "push") estilo += `transform:translate3d(0,${((1 - e) * 768).toFixed(1)}px,0);`;
            else if (tipo === "zoom") estilo += `opacity:${Math.min(1, e * 2.5).toFixed(3)};transform:scale(${mix(1.06, 1, e).toFixed(4)});`;
            else estilo += `opacity:${e.toFixed(3)};`;
        } else if (x > 0) {
            estilo += `transform:translate3d(0,${(-x * 140).toFixed(1)}px,0) scale(${mix(1, 0.95, x).toFixed(4)});opacity:${(1 - x * 0.7).toFixed(3)};`;
        }
        html += `<div class="camada" style="${estilo}">${fundo(t)}${desenhar[id](t - c.start, { ...ctx, t, cena: c })}</div>`;
    });
    return html;
}

export { clamp };
