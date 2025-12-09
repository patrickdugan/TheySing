// ============================================================================
// THEY SING - UI Manager
// Phase-based strategy game interface
// ============================================================================

import { TheySingEngine } from '../engine/TheySingEngine';
import { FACTIONS, UNIT_STATS, THRESHOLDS } from '../engine/gameData';
import { 
  GameState, GamePhase, FactionId, Unit, GameNode, Order, OrderType,
  UnitType, Vector, GameEvent
} from '../engine/types';
import { FlatMapScene } from '../three/FlatMapScene';
import { TechTreeScene } from '../three/TechTreeScene';

// ============================================================================
// UI MANAGER CLASS
// ============================================================================

export class TheySingUI {
  private container: HTMLElement;
  private engine: TheySingEngine;
  private scene: FlatMapScene;
  private techTree: TechTreeScene | null = null;
  private currentFaction: FactionId = 'HEGEMON';
  
  // UI Elements
  private hudPanel!: HTMLElement;
  private phasePanel!: HTMLElement;
  private detailsPanel!: HTMLElement;
  private ordersPanel!: HTMLElement;
  private logPanel!: HTMLElement;
  private modalOverlay!: HTMLElement;
  
  // Order building state
  private pendingOrders: Order[] = [];
  private orderMode: OrderType | null = null;

  constructor(container: HTMLElement, engine: TheySingEngine, scene: FlatMapScene) {
    this.container = container;
    this.engine = engine;
    this.scene = scene;
    
    this.injectStyles();
    this.createUI();
    this.bindEvents();
    this.updateAll();
  }

  // ==========================================================================
  // STYLES
  // ==========================================================================

  private injectStyles(): void {
    if (document.getElementById('theysing-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'theysing-styles';
    style.textContent = `
      @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=JetBrains+Mono:wght@400;500&display=swap');
      
      .ts-ui {
        font-family: 'JetBrains Mono', monospace;
        color: #e0e0e0;
        font-size: 13px;
        pointer-events: none;
      }
      
      .ts-ui * {
        box-sizing: border-box;
      }
      
      .ts-panel {
        background: rgba(10, 15, 25, 0.92);
        border: 1px solid rgba(60, 120, 180, 0.4);
        border-radius: 4px;
        padding: 12px;
        pointer-events: auto;
        backdrop-filter: blur(8px);
      }
      
      .ts-header {
        font-family: 'Orbitron', sans-serif;
        font-size: 11px;
        color: #4488cc;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 10px;
        padding-bottom: 6px;
        border-bottom: 1px solid rgba(60, 120, 180, 0.3);
      }
      
      /* HUD Panel */
      .ts-hud {
        position: absolute;
        top: 10px;
        left: 10px;
        width: 280px;
      }
      
      .ts-faction-name {
        font-family: 'Orbitron', sans-serif;
        font-size: 16px;
        font-weight: 700;
        margin-bottom: 8px;
      }
      
      .ts-resources {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
        margin-bottom: 12px;
      }
      
      .ts-resource {
        background: rgba(0, 0, 0, 0.3);
        padding: 8px;
        border-radius: 3px;
      }
      
      .ts-resource-label {
        font-size: 10px;
        color: #888;
        text-transform: uppercase;
      }
      
      .ts-resource-value {
        font-size: 18px;
        font-weight: 700;
      }
      
      .ts-resource.flops .ts-resource-value { color: #44ff88; }
      .ts-resource.influence .ts-resource-value { color: #ff88ff; }
      
      /* Global Counters */
      .ts-counters {
        margin-top: 10px;
      }
      
      .ts-counter {
        margin-bottom: 8px;
      }
      
      .ts-counter-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 3px;
        font-size: 11px;
      }
      
      .ts-counter-bar {
        height: 6px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 3px;
        overflow: hidden;
      }
      
      .ts-counter-fill {
        height: 100%;
        transition: width 0.5s ease, background-color 0.3s ease;
      }
      
      .ts-counter.tas .ts-counter-fill {
        background: linear-gradient(90deg, #44ff88, #ffaa00, #ff4444);
      }
      
      .ts-counter.kessler .ts-counter-fill {
        background: linear-gradient(90deg, #4488ff, #ff4488, #ff0000);
      }
      
      /* Phase Panel */
      .ts-phase {
        position: absolute;
        top: 10px;
        left: 50%;
        transform: translateX(-50%);
        text-align: center;
        min-width: 300px;
      }
      
      .ts-turn {
        font-family: 'Orbitron', sans-serif;
        font-size: 12px;
        color: #888;
        margin-bottom: 4px;
      }
      
      .ts-phase-name {
        font-family: 'Orbitron', sans-serif;
        font-size: 20px;
        font-weight: 700;
        color: #4488ff;
        margin-bottom: 8px;
      }
      
      .ts-phase-steps {
        display: flex;
        justify-content: center;
        gap: 4px;
        margin-bottom: 10px;
      }
      
      .ts-phase-step {
        width: 50px;
        height: 4px;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 2px;
      }
      
      .ts-phase-step.active {
        background: #4488ff;
      }
      
      .ts-phase-step.complete {
        background: #44ff88;
      }
      
      .ts-advance-btn {
        background: linear-gradient(135deg, #2255aa, #3366cc);
        border: 1px solid #4488ff;
        color: white;
        padding: 8px 20px;
        font-family: 'Orbitron', sans-serif;
        font-size: 12px;
        cursor: pointer;
        border-radius: 4px;
        transition: all 0.2s ease;
      }
      
      .ts-advance-btn:hover {
        background: linear-gradient(135deg, #3366cc, #4488ff);
        transform: translateY(-1px);
      }
      
      .ts-advance-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }
      
      /* Details Panel */
      .ts-details {
        position: absolute;
        top: 10px;
        right: 10px;
        width: 260px;
      }
      
      .ts-detail-section {
        margin-bottom: 10px;
      }
      
      .ts-detail-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 14px;
        margin-bottom: 6px;
      }
      
      .ts-detail-row {
        display: flex;
        justify-content: space-between;
        padding: 4px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      }
      
      .ts-detail-label {
        color: #888;
      }
      
      .ts-unit-list {
        max-height: 150px;
        overflow-y: auto;
      }
      
      .ts-unit-item {
        display: flex;
        align-items: center;
        padding: 6px;
        margin-bottom: 4px;
        background: rgba(0, 0, 0, 0.3);
        border-radius: 3px;
        cursor: pointer;
        transition: background 0.2s ease;
      }
      
      .ts-unit-item:hover {
        background: rgba(60, 120, 180, 0.3);
      }
      
      .ts-unit-item.selected {
        border: 1px solid #4488ff;
      }
      
      .ts-unit-icon {
        width: 24px;
        height: 24px;
        border-radius: 3px;
        margin-right: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 10px;
      }
      
      .ts-unit-info {
        flex: 1;
      }
      
      .ts-unit-type {
        font-size: 12px;
        font-weight: 500;
      }
      
      .ts-unit-location {
        font-size: 10px;
        color: #888;
      }
      
      /* Orders Panel */
      .ts-orders {
        position: absolute;
        bottom: 10px;
        left: 10px;
        width: 400px;
      }
      
      .ts-order-buttons {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-bottom: 10px;
      }
      
      .ts-order-btn {
        padding: 6px 12px;
        background: rgba(40, 60, 80, 0.8);
        border: 1px solid rgba(60, 120, 180, 0.4);
        color: #ccc;
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        cursor: pointer;
        border-radius: 3px;
        transition: all 0.2s ease;
      }
      
      .ts-order-btn:hover {
        background: rgba(60, 100, 140, 0.8);
        border-color: #4488ff;
      }
      
      .ts-order-btn.active {
        background: #3366aa;
        border-color: #4488ff;
        color: white;
      }
      
      .ts-order-btn:disabled {
        opacity: 0.4;
        cursor: not-allowed;
      }
      
      .ts-pending-orders {
        max-height: 120px;
        overflow-y: auto;
      }
      
      .ts-pending-order {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 6px 8px;
        background: rgba(0, 50, 80, 0.5);
        border-radius: 3px;
        margin-bottom: 4px;
        font-size: 11px;
      }
      
      .ts-pending-order .remove {
        color: #ff6666;
        cursor: pointer;
        padding: 0 4px;
      }
      
      .ts-submit-orders {
        margin-top: 10px;
        width: 100%;
        padding: 10px;
        background: linear-gradient(135deg, #227744, #33aa66);
        border: 1px solid #44ff88;
        color: white;
        font-family: 'Orbitron', sans-serif;
        font-size: 12px;
        cursor: pointer;
        border-radius: 4px;
      }
      
      .ts-submit-orders:hover {
        background: linear-gradient(135deg, #33aa66, #44cc88);
      }
      
      .ts-submit-orders:disabled {
        opacity: 0.4;
        background: #444;
        border-color: #666;
        cursor: not-allowed;
      }
      
      /* Log Panel */
      .ts-log {
        position: absolute;
        bottom: 10px;
        right: 10px;
        width: 320px;
        max-height: 200px;
      }
      
      .ts-log-entries {
        max-height: 160px;
        overflow-y: auto;
        font-size: 11px;
      }
      
      .ts-log-entry {
        padding: 4px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      }
      
      .ts-log-entry.COMBAT { color: #ff6666; }
      .ts-log-entry.ALERT { color: #ffaa44; }
      .ts-log-entry.SYSTEM { color: #4488ff; }
      
      .ts-log-turn {
        color: #666;
        margin-right: 6px;
      }
      
      /* Modal */
      .ts-modal-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        pointer-events: auto;
        opacity: 0;
        visibility: hidden;
        transition: opacity 0.3s ease;
      }
      
      .ts-modal-overlay.visible {
        opacity: 1;
        visibility: visible;
      }
      
      .ts-modal {
        background: rgba(15, 25, 40, 0.98);
        border: 2px solid #4488ff;
        border-radius: 8px;
        padding: 24px;
        max-width: 500px;
        text-align: center;
      }
      
      .ts-modal-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 24px;
        margin-bottom: 16px;
      }
      
      .ts-modal-content {
        margin-bottom: 20px;
        line-height: 1.6;
      }
      
      .ts-modal-buttons {
        display: flex;
        gap: 10px;
        justify-content: center;
      }
      
      .ts-modal-btn {
        padding: 10px 24px;
        border-radius: 4px;
        font-family: 'Orbitron', sans-serif;
        font-size: 12px;
        cursor: pointer;
        transition: all 0.2s ease;
      }
      
      /* Tech display */
      .ts-tech-levels {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 4px;
        margin-top: 8px;
      }
      
      .ts-tech {
        text-align: center;
        padding: 4px;
        background: rgba(0, 0, 0, 0.3);
        border-radius: 3px;
        font-size: 10px;
      }
      
      .ts-tech-label { color: #888; }
      .ts-tech-level { 
        font-size: 14px; 
        font-weight: 700;
        margin-top: 2px;
      }
      
      .ts-tech.KINETIC .ts-tech-level { color: #ff6666; }
      .ts-tech.INFO .ts-tech-level { color: #66ff66; }
      .ts-tech.LOGIC .ts-tech-level { color: #6666ff; }
      .ts-tech.MEMETIC .ts-tech-level { color: #ff66ff; }
      
      /* Scrollbar */
      .ts-ui ::-webkit-scrollbar {
        width: 6px;
      }
      .ts-ui ::-webkit-scrollbar-track {
        background: rgba(0, 0, 0, 0.3);
      }
      .ts-ui ::-webkit-scrollbar-thumb {
        background: #4488ff;
        border-radius: 3px;
      }
    `;
    document.head.appendChild(style);
  }

  // ==========================================================================
  // UI CREATION
  // ==========================================================================

  private createUI(): void {
    const wrapper = document.createElement('div');
    wrapper.className = 'ts-ui';
    wrapper.style.cssText = 'position: absolute; top: 0; left: 0; right: 0; bottom: 0;';
    
    this.hudPanel = this.createHUDPanel();
    this.phasePanel = this.createPhasePanel();
    this.detailsPanel = this.createDetailsPanel();
    this.ordersPanel = this.createOrdersPanel();
    this.logPanel = this.createLogPanel();
    this.modalOverlay = this.createModalOverlay();
    
    wrapper.appendChild(this.hudPanel);
    wrapper.appendChild(this.phasePanel);
    wrapper.appendChild(this.detailsPanel);
    wrapper.appendChild(this.ordersPanel);
    wrapper.appendChild(this.logPanel);
    wrapper.appendChild(this.modalOverlay);
    
    this.container.appendChild(wrapper);
  }

  private createHUDPanel(): HTMLElement {
    const panel = document.createElement('div');
    panel.className = 'ts-panel ts-hud';
    panel.innerHTML = `
      <div class="ts-faction-name"></div>
      <div class="ts-resources">
        <div class="ts-resource flops">
          <div class="ts-resource-label">FLOPs</div>
          <div class="ts-resource-value">0</div>
        </div>
        <div class="ts-resource influence">
          <div class="ts-resource-label">Influence</div>
          <div class="ts-resource-value">0</div>
        </div>
      </div>
      <div class="ts-header">Tech Levels</div>
      <div class="ts-tech-levels">
        <div class="ts-tech KINETIC"><div class="ts-tech-label">KIN</div><div class="ts-tech-level">0</div></div>
        <div class="ts-tech INFO"><div class="ts-tech-label">INF</div><div class="ts-tech-level">0</div></div>
        <div class="ts-tech LOGIC"><div class="ts-tech-label">LOG</div><div class="ts-tech-level">0</div></div>
        <div class="ts-tech MEMETIC"><div class="ts-tech-label">MEM</div><div class="ts-tech-level">0</div></div>
      </div>
      <div class="ts-counters">
        <div class="ts-counter tas">
          <div class="ts-counter-header">
            <span>TAS (Thermal Anomaly)</span>
            <span class="ts-counter-value">0/100</span>
          </div>
          <div class="ts-counter-bar"><div class="ts-counter-fill" style="width: 0%"></div></div>
        </div>
        <div class="ts-counter kessler">
          <div class="ts-counter-header">
            <span>Kessler Risk</span>
            <span class="ts-counter-value">0/100</span>
          </div>
          <div class="ts-counter-bar"><div class="ts-counter-fill" style="width: 0%"></div></div>
        </div>
      </div>
    `;
    return panel;
  }

  private createPhasePanel(): HTMLElement {
    const panel = document.createElement('div');
    panel.className = 'ts-panel ts-phase';
    panel.innerHTML = `
      <div class="ts-turn">TURN 1</div>
      <div class="ts-phase-name">NEGOTIATION</div>
      <div class="ts-phase-steps">
        <div class="ts-phase-step active" data-phase="NEGOTIATION"></div>
        <div class="ts-phase-step" data-phase="ALLOCATION"></div>
        <div class="ts-phase-step" data-phase="ACTION_DECLARATION"></div>
        <div class="ts-phase-step" data-phase="RESOLUTION"></div>
        <div class="ts-phase-step" data-phase="TURN_END"></div>
      </div>
      <button class="ts-advance-btn">ADVANCE PHASE →</button>
    `;
    return panel;
  }

  private createDetailsPanel(): HTMLElement {
    const panel = document.createElement('div');
    panel.className = 'ts-panel ts-details';
    panel.innerHTML = `
      <div class="ts-header">Selection</div>
      <div class="ts-detail-content">
        <p style="color: #666; font-style: italic;">Click a node or unit to view details</p>
      </div>
      <div class="ts-header" style="margin-top: 16px;">Your Units</div>
      <div class="ts-unit-list"></div>
    `;
    return panel;
  }

  private createOrdersPanel(): HTMLElement {
    const panel = document.createElement('div');
    panel.className = 'ts-panel ts-orders';
    panel.innerHTML = `
      <div class="ts-header">Orders</div>
      <div class="ts-order-buttons"></div>
      <div class="ts-header" style="margin-top: 10px;">Pending Orders</div>
      <div class="ts-pending-orders"></div>
      <button class="ts-submit-orders" disabled>SUBMIT ORDERS (0)</button>
    `;
    return panel;
  }

  private createLogPanel(): HTMLElement {
    const panel = document.createElement('div');
    panel.className = 'ts-panel ts-log';
    panel.innerHTML = `
      <div class="ts-header">Event Log</div>
      <div class="ts-log-entries"></div>
    `;
    return panel;
  }

  private createModalOverlay(): HTMLElement {
    const overlay = document.createElement('div');
    overlay.className = 'ts-modal-overlay';
    overlay.innerHTML = `
      <div class="ts-modal">
        <div class="ts-modal-title"></div>
        <div class="ts-modal-content"></div>
        <div class="ts-modal-buttons"></div>
      </div>
    `;
    return overlay;
  }

  // ==========================================================================
  // EVENT BINDING
  // ==========================================================================

  private bindEvents(): void {
    // Phase advance button
    const advanceBtn = this.phasePanel.querySelector('.ts-advance-btn');
    advanceBtn?.addEventListener('click', () => this.onAdvancePhase());
    
    // Submit orders button
    const submitBtn = this.ordersPanel.querySelector('.ts-submit-orders');
    submitBtn?.addEventListener('click', () => this.onSubmitOrders());
    
    // Scene callbacks
    this.scene.onNodeClick = (nodeId) => this.showNodeDetails(nodeId);
    this.scene.onUnitClick = (unitId) => this.showUnitDetails(unitId);
    
    // Engine events
    this.engine.on('*', (event) => this.onEngineEvent(event));
  }

  private onEngineEvent(event: GameEvent): void {
    this.updateAll();
    
    // Special handling
    if (event.type === 'GAME_OVER') {
      this.showGameOverModal(event.payload);
    }
  }

  // ==========================================================================
  // UPDATE METHODS
  // ==========================================================================

  public updateAll(): void {
    const state = this.engine.getState();
    this.updateHUD(state);
    this.updatePhase(state);
    this.updateUnitList(state);
    this.updateOrderButtons(state);
    this.updatePendingOrders();
    this.updateLog(state);
  }

  private updateHUD(state: GameState): void {
    const faction = state.factions.get(this.currentFaction);
    if (!faction) return;
    
    // Faction name with color
    const nameEl = this.hudPanel.querySelector('.ts-faction-name') as HTMLElement;
    const factionDef = FACTIONS[this.currentFaction];
    nameEl.textContent = factionDef.name;
    nameEl.style.color = `#${factionDef.color.toString(16).padStart(6, '0')}`;
    
    // Resources
    this.hudPanel.querySelector('.flops .ts-resource-value')!.textContent = faction.flops.toString();
    this.hudPanel.querySelector('.influence .ts-resource-value')!.textContent = faction.influence.toString();
    
    // Tech levels
    const vectors: Vector[] = ['KINETIC', 'INFO', 'LOGIC', 'MEMETIC'];
    for (const v of vectors) {
      const el = this.hudPanel.querySelector(`.ts-tech.${v} .ts-tech-level`);
      if (el) el.textContent = faction.techLevel[v].toString();
    }
    
    // Global counters
    const tas = state.counters.tas;
    const kessler = state.counters.kessler;
    
    this.hudPanel.querySelector('.tas .ts-counter-value')!.textContent = `${tas}/100`;
    const tasFill = this.hudPanel.querySelector('.tas .ts-counter-fill') as HTMLElement;
    tasFill.style.width = `${tas}%`;
    
    this.hudPanel.querySelector('.kessler .ts-counter-value')!.textContent = `${kessler}/100`;
    const kessFill = this.hudPanel.querySelector('.kessler .ts-counter-fill') as HTMLElement;
    kessFill.style.width = `${kessler}%`;
  }

  private updatePhase(state: GameState): void {
    const phases: GamePhase[] = ['NEGOTIATION', 'ALLOCATION', 'ACTION_DECLARATION', 'RESOLUTION', 'TURN_END'];
    const currentIdx = phases.indexOf(state.phase);
    
    this.phasePanel.querySelector('.ts-turn')!.textContent = `TURN ${state.counters.turn}`;
    this.phasePanel.querySelector('.ts-phase-name')!.textContent = state.phase.replace('_', ' ');
    
    // Update step indicators
    const steps = this.phasePanel.querySelectorAll('.ts-phase-step');
    steps.forEach((step, i) => {
      step.classList.remove('active', 'complete');
      if (i < currentIdx) step.classList.add('complete');
      if (i === currentIdx) step.classList.add('active');
    });
  }

  private updateUnitList(state: GameState): void {
    const listEl = this.detailsPanel.querySelector('.ts-unit-list')!;
    const units = Array.from(state.units.values()).filter(u => u.owner === this.currentFaction);
    
    listEl.innerHTML = units.map(unit => {
      const node = state.nodes.get(unit.location);
      const stats = UNIT_STATS[unit.type];
      const color = FACTIONS[unit.owner].color.toString(16).padStart(6, '0');
      const selected = this.scene.getSelectedUnit() === unit.id;
      
      return `
        <div class="ts-unit-item ${selected ? 'selected' : ''}" data-unit-id="${unit.id}">
          <div class="ts-unit-icon" style="background: #${color}">
            ${unit.type.charAt(0)}
          </div>
          <div class="ts-unit-info">
            <div class="ts-unit-type">${unit.type}</div>
            <div class="ts-unit-location">${node?.name || unit.location}</div>
          </div>
          <div style="font-size: 10px; color: #888">${stats.vector}</div>
        </div>
      `;
    }).join('');
    
    // Bind click events
    listEl.querySelectorAll('.ts-unit-item').forEach(el => {
      el.addEventListener('click', () => {
        const unitId = el.getAttribute('data-unit-id');
        if (unitId) {
          this.scene.selectUnit(unitId);
          this.showUnitDetails(unitId);
        }
      });
    });
  }

  private updateOrderButtons(state: GameState): void {
    const buttonsEl = this.ordersPanel.querySelector('.ts-order-buttons')!;
    const phase = state.phase;
    
    let availableOrders: { type: OrderType; label: string; phaseReq: GamePhase[] }[] = [
      { type: 'HOLD', label: 'HOLD', phaseReq: ['ACTION_DECLARATION'] },
      { type: 'MOVE', label: 'MOVE', phaseReq: ['ACTION_DECLARATION'] },
      { type: 'ATTACK', label: 'ATTACK', phaseReq: ['ACTION_DECLARATION'] },
      { type: 'FILTER', label: 'FILTER', phaseReq: ['ACTION_DECLARATION'] },
      { type: 'AUDIT', label: 'AUDIT', phaseReq: ['ACTION_DECLARATION'] },
      { type: 'ANTI_SAT', label: 'ANTI-SAT', phaseReq: ['ACTION_DECLARATION'] },
      { type: 'SABOTAGE', label: 'SABOTAGE', phaseReq: ['ACTION_DECLARATION'] },
      { type: 'BUILD', label: 'BUILD', phaseReq: ['ALLOCATION'] },
      { type: 'RESEARCH', label: 'RESEARCH', phaseReq: ['ALLOCATION'] },
    ];
    
    buttonsEl.innerHTML = availableOrders.map(o => {
      const enabled = o.phaseReq.includes(phase);
      const active = this.orderMode === o.type;
      return `
        <button class="ts-order-btn ${active ? 'active' : ''}" 
                data-order-type="${o.type}"
                ${enabled ? '' : 'disabled'}>
          ${o.label}
        </button>
      `;
    }).join('');
    
    // Bind events
    buttonsEl.querySelectorAll('.ts-order-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const type = btn.getAttribute('data-order-type') as OrderType;
        this.setOrderMode(type);
      });
    });
  }

  private updatePendingOrders(): void {
    const listEl = this.ordersPanel.querySelector('.ts-pending-orders')!;
    
    listEl.innerHTML = this.pendingOrders.map((order, i) => `
      <div class="ts-pending-order">
        <span>${order.type} - ${order.unitId || 'FACTION'} → ${order.targetNodeId || order.targetEdgeId || ''}</span>
        <span class="remove" data-index="${i}">✕</span>
      </div>
    `).join('');
    
    // Remove buttons
    listEl.querySelectorAll('.remove').forEach(el => {
      el.addEventListener('click', () => {
        const idx = parseInt(el.getAttribute('data-index') || '0');
        this.pendingOrders.splice(idx, 1);
        this.updatePendingOrders();
      });
    });
    
    // Update submit button
    const submitBtn = this.ordersPanel.querySelector('.ts-submit-orders') as HTMLButtonElement;
    submitBtn.disabled = this.pendingOrders.length === 0;
    submitBtn.textContent = `SUBMIT ORDERS (${this.pendingOrders.length})`;
  }

  private updateLog(state: GameState): void {
    const logs = state.logs.slice(-20);
    const entriesEl = this.logPanel.querySelector('.ts-log-entries')!;
    
    entriesEl.innerHTML = logs.map(log => `
      <div class="ts-log-entry ${log.type}">
        <span class="ts-log-turn">[T${log.turn}]</span>
        ${log.message}
      </div>
    `).join('');
    
    entriesEl.scrollTop = entriesEl.scrollHeight;
  }

  // ==========================================================================
  // DETAILS DISPLAY
  // ==========================================================================

  private showNodeDetails(nodeId: string): void {
    const node = this.engine.getNode(nodeId);
    if (!node) return;
    
    const units = this.engine.getUnitsAtNode(nodeId);
    const adjacent = this.engine.getAdjacentNodes(nodeId);
    
    const contentEl = this.detailsPanel.querySelector('.ts-detail-content')!;
    contentEl.innerHTML = `
      <div class="ts-detail-section">
        <div class="ts-detail-title" style="color: #${(node.owner ? FACTIONS[node.owner].color : 0x666666).toString(16).padStart(6, '0')}">${node.name}</div>
        <div class="ts-detail-row"><span class="ts-detail-label">Type</span><span>${node.type}</span></div>
        <div class="ts-detail-row"><span class="ts-detail-label">Layer</span><span>${node.layer}</span></div>
        <div class="ts-detail-row"><span class="ts-detail-label">Owner</span><span>${node.owner || 'NEUTRAL'}</span></div>
        <div class="ts-detail-row"><span class="ts-detail-label">Infrastructure</span><span>${node.infrastructure}%</span></div>
        <div class="ts-detail-row"><span class="ts-detail-label">FLOPs/turn</span><span>+${node.resources.flops}</span></div>
        <div class="ts-detail-row"><span class="ts-detail-label">Influence/turn</span><span>+${node.resources.influence}</span></div>
        ${node.isZombie ? '<div style="color: #00ff00; margin-top: 8px;">⚠ ZOMBIE NODE</div>' : ''}
        ${node.isCultNode ? '<div style="color: #ff00ff; margin-top: 8px;">⚠ CULT NODE</div>' : ''}
      </div>
      <div class="ts-detail-section">
        <div style="color: #888; font-size: 11px;">Units Present: ${units.length}</div>
        <div style="color: #888; font-size: 11px;">Adjacent: ${adjacent.length} nodes</div>
      </div>
    `;
  }

  private showUnitDetails(unitId: string): void {
    const unit = this.engine.getUnit(unitId);
    if (!unit) return;
    
    const stats = UNIT_STATS[unit.type];
    const node = this.engine.getNode(unit.location);
    const factionColor = FACTIONS[unit.owner].color.toString(16).padStart(6, '0');
    
    const contentEl = this.detailsPanel.querySelector('.ts-detail-content')!;
    contentEl.innerHTML = `
      <div class="ts-detail-section">
        <div class="ts-detail-title" style="color: #${factionColor}">${unit.type}</div>
        <div class="ts-detail-row"><span class="ts-detail-label">Owner</span><span>${unit.owner}</span></div>
        <div class="ts-detail-row"><span class="ts-detail-label">Location</span><span>${node?.name || unit.location}</span></div>
        <div class="ts-detail-row"><span class="ts-detail-label">Vector</span><span>${stats.vector}</span></div>
        <div class="ts-detail-row"><span class="ts-detail-label">Stealth</span><span>${unit.stealthLevel}</span></div>
        <div class="ts-detail-row"><span class="ts-detail-label">Speed</span><span>${stats.speed}</span></div>
        <div style="margin-top: 8px; font-size: 11px; color: #888;">${stats.special}</div>
      </div>
    `;
    
    this.updateUnitList(this.engine.getState());
  }

  // ==========================================================================
  // ORDER HANDLING
  // ==========================================================================

  private setOrderMode(type: OrderType): void {
    if (this.orderMode === type) {
      this.orderMode = null;
    } else {
      this.orderMode = type;
    }
    this.updateOrderButtons(this.engine.getState());
    
    // If order needs target, wait for click
    // For now, create simple order if unit is selected
    if (this.orderMode) {
      this.createOrderForSelectedUnit();
    }
  }

  private createOrderForSelectedUnit(): void {
    const selectedUnit = this.scene.getSelectedUnit();
    const selectedNode = this.scene.getSelectedNode();
    
    if (!this.orderMode) return;
    
    // RESEARCH and BUILD don't need a unit
    if (this.orderMode === 'RESEARCH') {
      // Show tech selection modal
      this.showResearchModal();
      return;
    }
    
    if (this.orderMode === 'BUILD') {
      if (selectedNode) {
        this.showBuildModal(selectedNode);
      }
      return;
    }
    
    // Other orders need a unit
    if (!selectedUnit) {
      return;
    }
    
    const unit = this.engine.getUnit(selectedUnit);
    if (!unit || unit.owner !== this.currentFaction) return;
    
    // For MOVE/ATTACK, need target node
    if (this.orderMode === 'MOVE' || this.orderMode === 'ATTACK') {
      // Set up target selection mode
      // For now, pick first adjacent node as example
      const adjacent = this.engine.getAdjacentNodes(unit.location);
      if (adjacent.length > 0) {
        const order: Order = {
          id: `order_${Date.now()}`,
          faction: this.currentFaction,
          unitId: selectedUnit,
          type: this.orderMode,
          targetNodeId: adjacent[0],
          priority: this.pendingOrders.length
        };
        this.pendingOrders.push(order);
        this.updatePendingOrders();
      }
    } else if (this.orderMode === 'HOLD') {
      const order: Order = {
        id: `order_${Date.now()}`,
        faction: this.currentFaction,
        unitId: selectedUnit,
        type: 'HOLD',
        priority: this.pendingOrders.length
      };
      this.pendingOrders.push(order);
      this.updatePendingOrders();
    }
    
    this.orderMode = null;
    this.updateOrderButtons(this.engine.getState());
  }

  private showResearchModal(): void {
    // Open the tech tree constellation view
    this.openTechTree();
  }

  private openTechTree(): void {
    if (this.techTree) return; // Already open
    
    this.techTree = new TechTreeScene(this.container);
    
    this.techTree.onClose = () => {
      this.techTree?.dispose();
      this.techTree = null;
    };
    
    this.techTree.onResearch = (techId: string) => {
      // Map tech ID to domain for now
      let domain: Vector = 'KINETIC';
      if (techId.startsWith('i')) domain = 'INFO';
      else if (techId.startsWith('l')) domain = 'LOGIC';
      else if (techId.startsWith('m')) domain = 'MEMETIC';
      
      const order: Order = {
        id: `order_${Date.now()}`,
        faction: this.currentFaction,
        unitId: this.currentFaction,
        type: 'RESEARCH',
        techDomain: domain,
        priority: this.pendingOrders.length
      };
      this.pendingOrders.push(order);
      this.updatePendingOrders();
      
      // Close tech tree after selecting research
      this.techTree?.close();
    };
    
    this.techTree.open();
  }

  private showBuildModal(nodeId: string): void {
    const unitTypes: UnitType[] = ['DRONE', 'SWARM', 'CULT', 'AUDITOR', 'SAT_SWARM'];
    const faction = this.engine.getFaction(this.currentFaction);
    
    const buttons = unitTypes.map(type => {
      const stats = UNIT_STATS[type];
      const canAfford = stats.currency === 'F' 
        ? (faction?.flops || 0) >= stats.cost 
        : (faction?.influence || 0) >= stats.cost;
      
      return {
        label: `${type} (${stats.cost}${stats.currency})`,
        disabled: !canAfford,
        action: () => {
          const order: Order = {
            id: `order_${Date.now()}`,
            faction: this.currentFaction,
            unitId: this.currentFaction,
            type: 'BUILD',
            unitTypeToBuild: type,
            targetNodeId: nodeId,
            priority: this.pendingOrders.length
          };
          this.pendingOrders.push(order);
          this.updatePendingOrders();
          this.hideModal();
        }
      };
    });
    
    this.showModal('Build Unit', `Build at ${nodeId}:`, buttons);
  }

  // ==========================================================================
  // PHASE HANDLING
  // ==========================================================================

  private onAdvancePhase(): void {
    this.engine.advancePhase();
    this.updateAll();
  }

  private onSubmitOrders(): void {
    if (this.pendingOrders.length === 0) return;
    
    const result = this.engine.submitOrders(this.currentFaction, this.pendingOrders);
    
    if (result.success) {
      this.pendingOrders = [];
      this.updatePendingOrders();
    } else {
      console.error('Order submission failed:', result.message);
    }
  }

  // ==========================================================================
  // MODAL
  // ==========================================================================

  private showModal(
    title: string, 
    content: string, 
    buttons: { label: string; action: () => void; disabled?: boolean }[]
  ): void {
    const modal = this.modalOverlay.querySelector('.ts-modal')!;
    modal.querySelector('.ts-modal-title')!.textContent = title;
    modal.querySelector('.ts-modal-content')!.innerHTML = content;
    
    const buttonsEl = modal.querySelector('.ts-modal-buttons')!;
    buttonsEl.innerHTML = buttons.map((b, i) => `
      <button class="ts-modal-btn" data-index="${i}" ${b.disabled ? 'disabled' : ''}
              style="background: ${i === 0 ? '#3366aa' : '#444'}; border: 1px solid ${i === 0 ? '#4488ff' : '#666'};">
        ${b.label}
      </button>
    `).join('');
    
    buttonsEl.querySelectorAll('.ts-modal-btn').forEach((btn, i) => {
      btn.addEventListener('click', () => buttons[i].action());
    });
    
    this.modalOverlay.classList.add('visible');
  }

  private hideModal(): void {
    this.modalOverlay.classList.remove('visible');
  }

  private showGameOverModal(payload: Record<string, unknown>): void {
    const reason = payload.reason as string;
    let title = 'GAME OVER';
    let message = '';
    
    if (reason === 'PROTOCOL_FAILURE') {
      title = '🛑 PROTOCOL FAILURE';
      message = 'The Thermal Anomaly Score exceeded 100. All ASI systems have been shut down by global regulatory intervention.';
    }
    
    this.showModal(title, message, [
      { label: 'NEW GAME', action: () => location.reload() }
    ]);
  }

  // ==========================================================================
  // PUBLIC API
  // ==========================================================================

  public setFaction(faction: FactionId): void {
    this.currentFaction = faction;
    this.updateAll();
  }
}
