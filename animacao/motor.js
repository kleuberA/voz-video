/**
 * Motor de tempo dos Shorts. Tudo no vídeo é função pura do instante `t` (segundos): nenhuma
 * transição CSS, nenhum timer, nenhum número aleatório. O mesmo `t` sempre desenha o mesmo quadro,
 * e é isso que permite renderizar quadro a quadro.
 */

export const FPS = 30;

export const clamp = (v, min = 0, max = 1) => Math.min(max, Math.max(min, v));
export const mix = (a, b, k) => a + (b - a) * k;

/** Curva cúbica de Bézier igual à do CSS. */
export function bezier(x1, y1, x2, y2) {
    const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx;
    const cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
    const sx = (s) => ((ax * s + bx) * s + cx) * s;
    const sy = (s) => ((ay * s + by) * s + cy) * s;
    const dx = (s) => (3 * ax * s + 2 * bx) * s + cx;
    return (x) => {
        if (x <= 0) return 0;
        if (x >= 1) return 1;
        let s = x;
        for (let i = 0; i < 8; i++) {
            const e = sx(s) - x;
            if (Math.abs(e) < 1e-6) return sy(s);
            const d = dx(s);
            if (Math.abs(d) < 1e-6) break;
            s -= e / d;
        }
        let lo = 0, hi = 1;
        s = x;
        for (let i = 0; i < 24; i++) {
            const v = sx(s);
            if (Math.abs(v - x) < 1e-6) break;
            if (v < x) lo = s; else hi = s;
            s = (lo + hi) / 2;
        }
        return sy(s);
    };
}

export const EASE = {
    out: bezier(0.16, 1, 0.3, 1),     // entradas
    inOut: bezier(0.65, 0, 0.35, 1),  // câmera e movimentos
    soft: bezier(0.45, 0, 0.2, 1),    // trocas de cena
    in: bezier(0.55, 0, 0.75, 0.2),   // saídas
    linear: (x) => x,
};

/** Progresso 0→1 de uma animação que começa em `at` e dura `dur`. */
export function prog(t, at, dur, ease = EASE.out) {
    if (dur <= 0) return t >= at ? 1 : 0;
    return ease(clamp((t - at) / dur));
}

/** Mola com pouco overshoot (`bounce` ~0,2 no máximo), 0→1 a partir de `at`. */
export function spring(t, at, { dur = 0.8, bounce = 0.15 } = {}) {
    const x = t - at;
    if (x <= 0) return 0;
    const w = (2 * Math.PI) / dur, z = 1 - bounce;
    if (z >= 1) return 1 - (1 + w * x) * Math.exp(-w * x);
    const wd = w * Math.sqrt(1 - z * z);
    return 1 - Math.exp(-z * w * x) * (Math.cos(wd * x) + ((z * w) / wd) * Math.sin(wd * x));
}

/** Valor ao longo de quadros-chave [[t, v], ...]. */
export function track(t, keys, ease = EASE.inOut) {
    if (t <= keys[0][0]) return keys[0][1];
    for (let i = 1; i < keys.length; i++) {
        if (t <= keys[i][0]) {
            const [t0, v0] = keys[i - 1], [t1, v1] = keys[i];
            return mix(v0, v1, ease(clamp((t - t0) / (t1 - t0))));
        }
    }
    return keys[keys.length - 1][1];
}

/**
 * Entrada padrão (sobe, ganha opacidade e foco) como texto de `style`. Com `at <= 0` o elemento já
 * está inteiro no quadro 0: é assim que o gancho aparece completo desde o primeiro quadro.
 */
export function rise(t, at, { y = 22, x = 0, scale = 1, blur = 5, dur = 0.6 } = {}) {
    if (at <= 0 && t >= 0) return "";
    const k = prog(t, at, dur);
    const o = prog(t, at, dur * 0.6);
    const f = blur && k < 1 ? `filter:blur(${((1 - k) * blur).toFixed(2)}px);` : "";
    return `opacity:${o.toFixed(3)};transform:translate3d(${((1 - k) * x).toFixed(2)}px,${((1 - k) * y).toFixed(2)}px,0) scale(${mix(scale, 1, k).toFixed(4)});${f}`;
}

/** Saída (inverso de rise) a partir de `at`. */
export function leave(t, at, { y = -14, dur = 0.35 } = {}) {
    const k = prog(t, at, dur, EASE.in);
    return `opacity:${(1 - k).toFixed(3)};transform:translate3d(0,${(k * y).toFixed(2)}px,0);`;
}

/** Entra em `inAt` e sai em `outAt`. */
export function life(t, inAt, outAt, opts = {}) {
    return t < outAt ? rise(t, inAt, opts) : leave(t, outAt);
}

/** Pop com mola (selos, carimbos, chips). */
export function pop(t, at, { from = 0.6, bounce = 0.25, dur = 0.6, rot = 0 } = {}) {
    if (t < at) return "opacity:0;transform:scale(" + from + ");";
    const k = spring(t, at, { dur, bounce });
    return `opacity:${prog(t, at, 0.18).toFixed(3)};transform:rotate(${rot}deg) scale(${mix(from, 1, k).toFixed(4)});`;
}

/** Carimbo: entra grande e bate (escala 1,8 → 1) com tranco. */
export function stamp(t, at, { rot = -6 } = {}) {
    if (t < at) return "opacity:0;";
    const k = spring(t, at, { dur: 0.45, bounce: 0.18 });
    return `opacity:${prog(t, at, 0.08).toFixed(3)};transform:rotate(${rot}deg) scale(${mix(1.8, 1, k).toFixed(4)});`;
}

/** Tranco de câmera (deslocamento em px) que decai depois de `at`. */
export function shake(t, at, amp = 6) {
    const x = t - at;
    if (x < 0 || x > 0.45) return 0;
    return Math.sin(x * 70) * amp * Math.exp(-x * 9);
}

/** Número que conta de `from` a `to`. */
export function count(t, at, dur, from, to) {
    return Math.round(mix(from, to, prog(t, at, dur)));
}
