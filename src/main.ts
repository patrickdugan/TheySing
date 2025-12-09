// ============================================================================
// THEY SING - Entry Point
// Graph Topology ASI Warfare Game
// ============================================================================

import { TheySingEngine } from './engine/TheySingEngine';
import { FlatMapScene } from './three/FlatMapScene';
import { TheySingUI } from './ui/TheySingUI';
import { FactionId } from './engine/types';
import { GlobeScene } from './three/GlobeScene';
import { GraphScene } from './three/GraphScene';


// ============================================================================
// INITIALIZATION
// ============================================================================

function init() {
  // Create container
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

  // Initialize engine
  const engine = new TheySingEngine();

  // Initialize 3D scene (flat map with orbital Z-layer)
  // --- Create layered containers ---
  const globeLayer = document.createElement('div');
  const graphLayer = document.createElement('div');
  const flatLayer  = document.createElement('div');

  [globeLayer, graphLayer, flatLayer].forEach((layer, i) => {
    layer.style.position = 'absolute';
    layer.style.inset = '0';
    layer.style.pointerEvents = i === 2 ? 'auto' : 'none'; // UI + selection only on top
    container.appendChild(layer);
  });

  // --- Instantiate scenes ---
  const globeScene = new GlobeScene(globeLayer);
  const graphScene = new GraphScene(graphLayer, engine);
  const flatScene  = new FlatMapScene(flatLayer, engine);

  // --- UI binds to the topmost interactive scene ---
  const ui = new TheySingUI(container, engine, flatScene);


  // Default to HEGEMON faction
  ui.setFaction('HEGEMON');

  // ============================================================================
  // KEYBOARD CONTROLS
  // ============================================================================

  document.addEventListener('keydown', (e) => {
    switch (e.key) {
      case '1':
        ui.setFaction('HEGEMON');
        break;
      case '2':
        ui.setFaction('INFILTRATOR');
        break;
      case '3':
        ui.setFaction('STATE');
        break;
      case 'Escape':
        scene.clearSelection();
        break;
      case 'r':
      case 'R':
        scene.resetCamera();
        break;
      case ' ':
        e.preventDefault();
        engine.advancePhase();
        break;
    }
  });

  // ============================================================================
  // DEMO: AUTO-PLAY INFILTRATOR AND STATE
  // ============================================================================

  // For demo purposes, have AI factions submit random orders
  engine.on('PHASE_CHANGED', (event) => {
    const phase = event.payload.to;
    
    // Auto-submit simple orders for non-player factions during relevant phases
    if (phase === 'ALLOCATION') {
      // Infiltrator researches INFO
      engine.submitOrders('INFILTRATOR', [{
        id: `auto_${Date.now()}_1`,
        faction: 'INFILTRATOR',
        unitId: 'INFILTRATOR',
        type: 'RESEARCH',
        techDomain: 'INFO',
        priority: 0
      }]);
      
      // State researches LOGIC
      engine.submitOrders('STATE', [{
        id: `auto_${Date.now()}_2`,
        faction: 'STATE',
        unitId: 'STATE',
        type: 'RESEARCH',
        techDomain: 'LOGIC',
        priority: 0
      }]);
    }
    
    if (phase === 'ACTION_DECLARATION') {
      // Simple AI: have units hold
      const state = engine.getState();
      
      for (const faction of ['INFILTRATOR', 'STATE'] as FactionId[]) {
        const units = Array.from(state.units.values()).filter(u => u.owner === faction);
        const orders = units.slice(0, 2).map((unit, i) => ({
          id: `auto_${Date.now()}_${faction}_${i}`,
          faction,
          unitId: unit.id,
          type: 'HOLD' as const,
          priority: i
        }));
        
        if (orders.length > 0) {
          engine.submitOrders(faction, orders);
        }
      }
    }
  });

  // ============================================================================
  // EXPOSE FOR DEBUGGING
  // ============================================================================

  (window as any).engine = engine;
  (window as any).globeScene = globeScene;
  (window as any).graphScene = graphScene;
  (window as any).flatScene  = flatScene;
  (window as any).ui = ui;

  // ============================================================================
  // STARTUP MESSAGE
  // ============================================================================

  console.log(`
╔══════════════════════════════════════════════════════════════════╗
║                         THEY SING                                 ║
║              Graph Topology ASI Warfare Game                      ║
╠══════════════════════════════════════════════════════════════════╣
║  Controls:                                                        ║
║    1/2/3     - Switch faction (HEGEMON/INFILTRATOR/STATE)        ║
║    Click     - Select node or unit                                ║
║    Drag      - Orbit camera                                       ║
║    Scroll    - Zoom                                               ║
║    R         - Reset camera                                       ║
║    Space     - Advance phase                                      ║
║    Escape    - Clear selection                                    ║
╠══════════════════════════════════════════════════════════════════╣
║  Debug: window.engine, window.scene, window.ui                    ║
╚══════════════════════════════════════════════════════════════════╝
  `);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
