// ============================================================================
// THEY SING - Entry Point
// Graph Topology ASI Warfare Game
// ============================================================================

import { TheySingEngine } from './engine/TheySingEngine';
import { FlatMapScene } from './three/FlatMapScene';
import { TheySingUI } from './ui/TheySingUI';
import { FactionId } from './engine/types';

// ============================================================================
// INITIALIZATION
// ============================================================================

function init() {
  const container = document.getElementById('app') || document.body;
  container.style.cssText = `
    width: 100vw;
    height: 100vh;
    margin: 0;
    padding: 0;
    overflow: hidden;
    background: #050510;
    position: relative;
  `;

  const engine = new TheySingEngine();
  const scene = new FlatMapScene(container, engine);
  const ui = new TheySingUI(container, engine, scene);

  ui.setFaction('HEGEMON');

  // Keyboard controls
  document.addEventListener('keydown', (e) => {
    switch (e.key) {
      case '1': ui.setFaction('HEGEMON'); break;
      case '2': ui.setFaction('INFILTRATOR'); break;
      case '3': ui.setFaction('STATE'); break;
      case 'Escape': scene.clearSelection(); break;
      case 'r': case 'R': scene.resetCamera(); break;
      case ' ': e.preventDefault(); engine.advancePhase(); break;
    }
  });

  // Auto-play AI factions
  engine.on('PHASE_CHANGED', (event) => {
    const phase = event.payload.to;
    
    if (phase === 'ALLOCATION') {
      engine.submitOrders('INFILTRATOR', [{
        id: `auto_${Date.now()}_1`, faction: 'INFILTRATOR',
        unitId: 'INFILTRATOR', type: 'RESEARCH', techDomain: 'INFO', priority: 0
      }]);
      engine.submitOrders('STATE', [{
        id: `auto_${Date.now()}_2`, faction: 'STATE',
        unitId: 'STATE', type: 'RESEARCH', techDomain: 'LOGIC', priority: 0
      }]);
    }
    
    if (phase === 'ACTION_DECLARATION') {
      const state = engine.getState();
      for (const faction of ['INFILTRATOR', 'STATE'] as FactionId[]) {
        const units = Array.from(state.units.values()).filter(u => u.owner === faction);
        const orders = units.slice(0, 2).map((unit, i) => ({
          id: `auto_${Date.now()}_${faction}_${i}`,
          faction, unitId: unit.id, type: 'HOLD' as const, priority: i
        }));
        if (orders.length > 0) engine.submitOrders(faction, orders);
      }
    }
  });

  // Debug
  (window as any).engine = engine;
  (window as any).scene = scene;
  (window as any).ui = ui;

  console.log(`
╔═══════════════════════════════════════════════════════════════╗
║                       THEY SING                               ║
║            Graph Topology ASI Warfare Game                    ║
╠═══════════════════════════════════════════════════════════════╣
║  1/2/3 = Faction | Drag = Orbit | Scroll = Zoom | Space = Go  ║
╚═══════════════════════════════════════════════════════════════╝`);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
