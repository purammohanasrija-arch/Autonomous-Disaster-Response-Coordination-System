/**
 * Emergency Alert Sounds — Web Audio API
 * Mimics real emergency siren patterns from Pixabay emergency sounds.
 *
 * sosAlarm()        – realistic emergency siren (wail pattern)
 * broadcastChime()  – 3-tone notification chime
 * warningBeep()     – warning beep
 * stopAllSounds()   – stop any playing sound
 */

let _sosCtx = null;
let _sosNodes = [];

function stopAllSounds() {
  if (_sosCtx) {
    try { _sosCtx.close(); } catch(e) {}
    _sosCtx = null;
  }
  _sosNodes = [];
}

// ── Real emergency siren (wail pattern like ambulance/fire truck) ─────────────
function sosAlarm(duration = 6) {
  stopAllSounds();
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    _sosCtx = ctx;

    const masterGain = ctx.createGain();
    masterGain.gain.setValueAtTime(0.7, ctx.currentTime);
    masterGain.connect(ctx.destination);

    // Wail pattern: sweep from 600Hz to 1200Hz repeatedly
    const cycleTime = 0.8; // seconds per wail cycle
    const cycles    = Math.ceil(duration / cycleTime);

    for (let i = 0; i < cycles; i++) {
      const t     = ctx.currentTime + i * cycleTime;
      const osc   = ctx.createOscillator();
      const gain  = ctx.createGain();

      osc.type = 'sawtooth';
      osc.connect(gain);
      gain.connect(masterGain);

      // Sweep up then down (wail)
      osc.frequency.setValueAtTime(600, t);
      osc.frequency.linearRampToValueAtTime(1200, t + cycleTime * 0.5);
      osc.frequency.linearRampToValueAtTime(600,  t + cycleTime);

      // Volume envelope
      gain.gain.setValueAtTime(0, t);
      gain.gain.linearRampToValueAtTime(0.8, t + 0.05);
      gain.gain.setValueAtTime(0.8, t + cycleTime - 0.05);
      gain.gain.linearRampToValueAtTime(0, t + cycleTime);

      osc.start(t);
      osc.stop(t + cycleTime);
      _sosNodes.push(osc);
    }

    // Add a second oscillator for richer sound (harmony)
    for (let i = 0; i < cycles; i++) {
      const t    = ctx.currentTime + i * cycleTime;
      const osc2 = ctx.createOscillator();
      const g2   = ctx.createGain();

      osc2.type = 'square';
      osc2.connect(g2);
      g2.connect(masterGain);

      osc2.frequency.setValueAtTime(800, t);
      osc2.frequency.linearRampToValueAtTime(1600, t + cycleTime * 0.5);
      osc2.frequency.linearRampToValueAtTime(800,  t + cycleTime);

      g2.gain.setValueAtTime(0, t);
      g2.gain.linearRampToValueAtTime(0.15, t + 0.05);
      g2.gain.setValueAtTime(0.15, t + cycleTime - 0.05);
      g2.gain.linearRampToValueAtTime(0, t + cycleTime);

      osc2.start(t);
      osc2.stop(t + cycleTime);
      _sosNodes.push(osc2);
    }

    // Auto-close context after sound ends
    setTimeout(() => {
      try { ctx.close(); } catch(e) {}
      if (_sosCtx === ctx) _sosCtx = null;
    }, (duration + 0.5) * 1000);

  } catch(e) {
    console.warn('SOS sound error:', e);
  }
}

// ── Broadcast chime (3-tone ascending) ───────────────────────────────────────
function broadcastChime() {
  try {
    const ctx   = new (window.AudioContext || window.webkitAudioContext)();
    const notes = [523, 659, 784, 1047]; // C5, E5, G5, C6
    notes.forEach((freq, i) => {
      const t = ctx.currentTime + i * 0.2;
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.type = 'sine';
      o.connect(g); g.connect(ctx.destination);
      o.frequency.value = freq;
      g.gain.setValueAtTime(0.4, t);
      g.gain.exponentialRampToValueAtTime(0.001, t + 0.5);
      o.start(t); o.stop(t + 0.5);
    });
    setTimeout(() => { try { ctx.close(); } catch(e) {} }, 2000);
  } catch(e) {}
}

// ── Warning beep ──────────────────────────────────────────────────────────────
function warningBeep(count = 3) {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    for (let i = 0; i < count; i++) {
      const t = ctx.currentTime + i * 0.35;
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.connect(g); g.connect(ctx.destination);
      o.frequency.value = 1000;
      g.gain.setValueAtTime(0.5, t);
      g.gain.exponentialRampToValueAtTime(0.001, t + 0.25);
      o.start(t); o.stop(t + 0.25);
    }
    setTimeout(() => { try { ctx.close(); } catch(e) {} }, 2000);
  } catch(e) {}
}

// ── High-risk weather alert sound ────────────────────────────────────────────
function weatherAlert() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    [0, 0.4, 0.8].forEach(t => {
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.type = 'square';
      o.connect(g); g.connect(ctx.destination);
      o.frequency.setValueAtTime(880, ctx.currentTime + t);
      o.frequency.linearRampToValueAtTime(440, ctx.currentTime + t + 0.3);
      g.gain.setValueAtTime(0.4, ctx.currentTime + t);
      g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + t + 0.35);
      o.start(ctx.currentTime + t);
      o.stop(ctx.currentTime + t + 0.35);
    });
    setTimeout(() => { try { ctx.close(); } catch(e) {} }, 2000);
  } catch(e) {}
}
