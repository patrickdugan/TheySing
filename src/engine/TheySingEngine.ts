// ============================================================================
// THEY SING - Core Game Engine
// Graph Topology ASI Warfare with Diplomacy-style Resolution
// ============================================================================

import {
  GameState, GamePhase, FactionId, FactionState, Unit, UnitType, Order, OrderType,
  OrderResult, OrderEffect, CombatResult, GameNode, GameEdge, Vector,
  GameEvent, GameEventType, GameEventListener, TechLevel, GlobalCounters,
  VECTOR_SUPERIORITY, GameLog
} from './types';

import {
  FACTIONS, UNIT_STATS, INITIAL_NODES, INITIAL_EDGES, INITIAL_UNITS,
  INITIAL_FACTION_STATE, TECH_TREE, THRESHOLDS
} from './gameData';

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function generateId(): string {
  return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

// ============================================================================
// GAME ENGINE CLASS
// ============================================================================

export class TheySingEngine {
  private state: GameState;
  private listeners: Map<GameEventType | '*', GameEventListener[]> = new Map();

  constructor() {
    this.state = this.createInitialState();
  }

  // ==========================================================================
  // STATE INITIALIZATION
  // ==========================================================================

  private createInitialState(): GameState {
    // Initialize nodes map
    const nodes = new Map<string, GameNode>();
    for (const node of INITIAL_NODES) {
      nodes.set(node.id, { ...node });
    }

    // Initialize edges map
    const edges = new Map<string, GameEdge>();
    for (const edge of INITIAL_EDGES) {
      edges.set(edge.id, { ...edge });
    }

    // Initialize units map
    const units = new Map<string, Unit>();
    for (const unitDef of INITIAL_UNITS) {
      const unit: Unit = {
        ...unitDef,
        isRevealed: false,
        hasActed: false,
        turnsOnNode: 0
      };
      units.set(unit.id, unit);
    }

    // Initialize factions
    const factions = new Map<FactionId, FactionState>();
    for (const fid of ['HEGEMON', 'INFILTRATOR', 'STATE', 'NEUTRAL'] as FactionId[]) {
      const initial = INITIAL_FACTION_STATE[fid];
      factions.set(fid, {
        id: fid,
        flops: initial.flops,
        influence: initial.influence,
        techLevel: { ...initial.techLevel } as TechLevel,
        unlockedTechs: new Set<string>(),
        submittedOrders: [],
        revealedEnemies: new Set<string>(),
        artifacts: []
      });
    }

    // Set initial tech unlocks based on starting tech levels
    for (const [fid, faction] of factions) {
      for (const tech of TECH_TREE) {
        if (faction.techLevel[tech.domain] >= tech.level) {
          faction.unlockedTechs.add(tech.id);
        }
      }
    }

    return {
      phase: 'NEGOTIATION',
      counters: {
        tas: 0,
        kessler: 0,
        turn: 1,
        regulatoryPanic: false,
        protocolFailure: false,
        orbitalCollapse: false
      },
      nodes,
      edges,
      units,
      factions,
      turnHistory: [],
      logs: [],
      pendingOrders: new Map(),
      pendingResults: []
    };
  }

  // ==========================================================================
  // PUBLIC API - State Access
  // ==========================================================================

  public getState(): GameState {
    return this.state;
  }

  public getNode(id: string): GameNode | undefined {
    return this.state.nodes.get(id);
  }

  public getEdge(id: string): GameEdge | undefined {
    return this.state.edges.get(id);
  }

  public getUnit(id: string): Unit | undefined {
    return this.state.units.get(id);
  }

  public getFaction(id: FactionId): FactionState | undefined {
    return this.state.factions.get(id);
  }

  public getUnitsAtNode(nodeId: string): Unit[] {
    return Array.from(this.state.units.values()).filter(u => u.location === nodeId);
  }

  public getUnitsForFaction(factionId: FactionId): Unit[] {
    return Array.from(this.state.units.values()).filter(u => u.owner === factionId);
  }

  public getAdjacentNodes(nodeId: string): string[] {
    const adjacent: string[] = [];
    for (const edge of this.state.edges.values()) {
      if (edge.isSevered) continue;
      if (edge.from === nodeId) adjacent.push(edge.to);
      if (edge.to === nodeId) adjacent.push(edge.from);
    }
    return adjacent;
  }

  public getEdgeBetween(nodeA: string, nodeB: string): GameEdge | undefined {
    for (const edge of this.state.edges.values()) {
      if ((edge.from === nodeA && edge.to === nodeB) ||
          (edge.from === nodeB && edge.to === nodeA)) {
        return edge;
      }
    }
    return undefined;
  }

  public getCurrentPhase(): GamePhase {
    return this.state.phase;
  }

  public getTurn(): number {
    return this.state.counters.turn;
  }

  // ==========================================================================
  // PUBLIC API - Order Submission
  // ==========================================================================

  public submitOrders(factionId: FactionId, orders: Order[]): { success: boolean; message: string } {
    // Validate phase
    if (this.state.phase !== 'ALLOCATION' && this.state.phase !== 'ACTION_DECLARATION') {
      return { success: false, message: `Cannot submit orders during ${this.state.phase} phase.` };
    }

    const faction = this.state.factions.get(factionId);
    if (!faction) {
      return { success: false, message: `Unknown faction: ${factionId}` };
    }

    // Validate each order
    for (const order of orders) {
      const validation = this.validateOrder(order, factionId);
      if (!validation.valid) {
        return { success: false, message: `Invalid order: ${validation.reason}` };
      }
    }

    // Store orders
    faction.submittedOrders.push(...orders);
    
    this.log('INFO', `${factionId} submitted ${orders.length} orders.`);
    this.emit('ORDER_SUBMITTED', { factionId, orderCount: orders.length });

    return { success: true, message: `${orders.length} orders accepted.` };
  }

  private validateOrder(order: Order, factionId: FactionId): { valid: boolean; reason?: string } {
    // Check unit ownership for unit-based orders
    if (order.unitId && order.type !== 'BUILD' && order.type !== 'RESEARCH') {
      const unit = this.state.units.get(order.unitId);
      if (!unit) return { valid: false, reason: `Unit ${order.unitId} not found` };
      if (unit.owner !== factionId) return { valid: false, reason: `Unit ${order.unitId} not owned by ${factionId}` };
      if (unit.hasActed) return { valid: false, reason: `Unit ${order.unitId} has already acted` };
    }

    // Validate movement target
    if (order.type === 'MOVE' && order.targetNodeId) {
      const unit = this.state.units.get(order.unitId);
      if (unit) {
        const adjacent = this.getAdjacentNodes(unit.location);
        if (!adjacent.includes(order.targetNodeId)) {
          return { valid: false, reason: `${order.targetNodeId} not adjacent to unit location` };
        }
      }
    }

    // Validate filter target
    if (order.type === 'FILTER' && order.targetEdgeId) {
      const unit = this.state.units.get(order.unitId);
      const edge = this.state.edges.get(order.targetEdgeId);
      if (!unit || !edge) return { valid: false, reason: 'Invalid filter target' };
      if (!UNIT_STATS[unit.type].canFilter) return { valid: false, reason: 'Unit cannot filter' };
      if (edge.type !== 'CABLE') return { valid: false, reason: 'Can only filter cables' };
      if (edge.from !== unit.location && edge.to !== unit.location) {
        return { valid: false, reason: 'Unit not adjacent to edge' };
      }
    }

    return { valid: true };
  }

  // ==========================================================================
  // PUBLIC API - Phase Advancement
  // ==========================================================================

  public advancePhase(): GameState {
    const previousPhase = this.state.phase;

    switch (this.state.phase) {
      case 'NEGOTIATION':
        this.state.phase = 'ALLOCATION';
        this.log('SYSTEM', 'PHASE: ALLOCATION — Secretly allocate FLOPs/Influence for builds and research.');
        break;

      case 'ALLOCATION':
        this.state.phase = 'ACTION_DECLARATION';
        this.log('SYSTEM', 'PHASE: ACTION DECLARATION — Submit movement, combat, and special orders.');
        break;

      case 'ACTION_DECLARATION':
        this.state.phase = 'RESOLUTION';
        this.log('SYSTEM', 'PHASE: RESOLUTION — All orders resolve simultaneously.');
        this.resolveAllOrders();
        break;

      case 'RESOLUTION':
        this.state.phase = 'TURN_END';
        this.log('SYSTEM', 'PHASE: TURN END — Resource generation and global checks.');
        this.generateResources();
        this.checkGlobalThresholds();
        this.incrementTurnsOnNodes();
        this.checkFootholdConversions();
        break;

      case 'TURN_END':
        this.endTurn();
        break;
    }

    this.emit('PHASE_CHANGED', { from: previousPhase, to: this.state.phase });
    return this.state;
  }

  private endTurn(): void {
    // Record turn history
    const allOrders: Order[] = [];
    for (const faction of this.state.factions.values()) {
      allOrders.push(...faction.submittedOrders);
      faction.submittedOrders = [];
    }

    this.state.turnHistory.push({
      turn: this.state.counters.turn,
      orders: allOrders,
      results: [...this.state.pendingResults],
      combats: [],
      stateSnapshot: {}
    });

    // Clear pending
    this.state.pendingResults = [];

    // Reset unit action flags
    for (const unit of this.state.units.values()) {
      unit.hasActed = false;
      unit.isRevealed = false;
    }

    // Advance turn counter
    this.state.counters.turn++;
    this.state.phase = 'NEGOTIATION';

    this.log('SYSTEM', `═══ TURN ${this.state.counters.turn} BEGINS ═══`);
    this.emit('TURN_STARTED', { turn: this.state.counters.turn });
  }

  // ==========================================================================
  // ORDER RESOLUTION
  // ==========================================================================

  private resolveAllOrders(): void {
    const allOrders: Order[] = [];
    for (const faction of this.state.factions.values()) {
      allOrders.push(...faction.submittedOrders);
    }

    // Sort by priority and type
    const sortedOrders = this.sortOrders(allOrders);

    // Phase 1: Allocation orders (BUILD, RESEARCH)
    const allocationOrders = sortedOrders.filter(o => o.type === 'BUILD' || o.type === 'RESEARCH');
    for (const order of allocationOrders) {
      this.resolveAllocationOrder(order);
    }

    // Phase 2: Special actions (FILTER, AUDIT, ANTI_SAT, SABOTAGE)
    const specialOrders = sortedOrders.filter(o => 
      ['FILTER', 'AUDIT', 'ANTI_SAT', 'SABOTAGE', 'CONVERT'].includes(o.type)
    );
    for (const order of specialOrders) {
      this.resolveSpecialOrder(order);
    }

    // Phase 3: Movement and combat (MOVE, ATTACK, SUPPORT, HOLD)
    const movementOrders = sortedOrders.filter(o => 
      ['MOVE', 'ATTACK', 'SUPPORT', 'HOLD'].includes(o.type)
    );
    this.resolveMovementPhase(movementOrders);
  }

  private sortOrders(orders: Order[]): Order[] {
    // Priority: BUILD/RESEARCH first, then FILTER/AUDIT, then MOVE/ATTACK
    const typePriority: Record<OrderType, number> = {
      BUILD: 0, RESEARCH: 0,
      FILTER: 1, AUDIT: 1, SABOTAGE: 1, ANTI_SAT: 1, CONVERT: 1,
      HOLD: 2, SUPPORT: 2, MOVE: 3, ATTACK: 3
    };

    return orders.sort((a, b) => {
      const pa = typePriority[a.type] ?? 99;
      const pb = typePriority[b.type] ?? 99;
      if (pa !== pb) return pa - pb;
      return (a.priority || 0) - (b.priority || 0);
    });
  }

  // --- Allocation Resolution ---
  private resolveAllocationOrder(order: Order): void {
    const faction = this.state.factions.get(order.faction);
    if (!faction) return;

    if (order.type === 'RESEARCH') {
      this.resolveResearch(order, faction);
    } else if (order.type === 'BUILD') {
      this.resolveBuild(order, faction);
    }
  }

  private resolveResearch(order: Order, faction: FactionState): void {
    const cost = 2; // FLOPs
    if (faction.flops < cost) {
      this.log('INFO', `${faction.id} cannot afford research (need ${cost}F).`);
      return;
    }

    faction.flops -= cost;
    this.state.counters.tas += 2;

    // Advance tech level if domain specified
    if (order.techDomain) {
      faction.techLevel[order.techDomain]++;
      
      // Check for new unlocks
      for (const tech of TECH_TREE) {
        if (tech.domain === order.techDomain && 
            faction.techLevel[tech.domain] >= tech.level &&
            !faction.unlockedTechs.has(tech.id)) {
          faction.unlockedTechs.add(tech.id);
          this.log('ALERT', `${faction.id} unlocked: ${tech.name}!`);
          this.emit('TECH_UNLOCKED', { faction: faction.id, tech: tech.id });
        }
      }
    }

    this.log('INFO', `${faction.id} conducted research. TAS +2 (now ${this.state.counters.tas}).`);
    this.emit('TAS_THRESHOLD', { tas: this.state.counters.tas, delta: 2 });
  }

  private resolveBuild(order: Order, faction: FactionState): void {
    if (!order.unitTypeToBuild || !order.targetNodeId) return;

    const stats = UNIT_STATS[order.unitTypeToBuild];
    const cost = stats.cost;
    const currency = stats.currency;

    // Check cost
    if (currency === 'F' && faction.flops < cost) {
      this.log('INFO', `${faction.id} cannot afford ${order.unitTypeToBuild} (need ${cost}F).`);
      return;
    }
    if (currency === 'I' && faction.influence < cost) {
      this.log('INFO', `${faction.id} cannot afford ${order.unitTypeToBuild} (need ${cost}I).`);
      return;
    }

    // Check node ownership
    const node = this.state.nodes.get(order.targetNodeId);
    if (!node || node.owner !== faction.id) {
      this.log('INFO', `${faction.id} cannot build at ${order.targetNodeId} - not owned.`);
      return;
    }

    // Check layer restrictions
    if (node.layer === 'ORBITAL' && !stats.canOrbit) {
      this.log('INFO', `${order.unitTypeToBuild} cannot be built in orbital layer.`);
      return;
    }

    // Deduct cost
    if (currency === 'F') faction.flops -= cost;
    else faction.influence -= cost;

    // Create unit
    const newUnit: Unit = {
      id: `${faction.id}_${order.unitTypeToBuild}_${generateId()}`,
      type: order.unitTypeToBuild,
      owner: faction.id,
      location: order.targetNodeId,
      stealthLevel: stats.stealth,
      isRevealed: false,
      hasActed: true, // Can't act on build turn
      turnsOnNode: 0
    };

    this.state.units.set(newUnit.id, newUnit);
    this.log('INFO', `${faction.id} built ${order.unitTypeToBuild} at ${node.name}.`);
    this.emit('UNIT_CREATED', { unit: newUnit });
  }

  // --- Special Order Resolution ---
  private resolveSpecialOrder(order: Order): void {
    const unit = this.state.units.get(order.unitId);
    if (!unit) return;

    switch (order.type) {
      case 'FILTER':
        this.resolveFilter(order, unit);
        break;
      case 'AUDIT':
        this.resolveAudit(order, unit);
        break;
      case 'ANTI_SAT':
        this.resolveAntiSat(order, unit);
        break;
      case 'SABOTAGE':
        this.resolveSabotage(order, unit);
        break;
      case 'CONVERT':
        this.resolveConvert(order, unit);
        break;
    }

    unit.hasActed = true;
  }

  private resolveFilter(order: Order, unit: Unit): void {
    if (!order.targetEdgeId) return;
    
    const edge = this.state.edges.get(order.targetEdgeId);
    if (!edge || edge.type !== 'CABLE') return;

    const faction = this.state.factions.get(unit.owner);
    if (!faction) return;

    edge.filteredBy = unit.owner;
    edge.filterStrength = faction.techLevel.LOGIC + 2;

    this.log('ALERT', `${unit.owner} established MechInterp Filter on ${edge.id}.`);
    this.emit('EDGE_FILTERED', { edgeId: edge.id, faction: unit.owner });
  }

  private resolveAudit(order: Order, unit: Unit): void {
    const targetNode = order.targetNodeId || unit.location;
    const unitsAtNode = this.getUnitsAtNode(targetNode);
    const faction = this.state.factions.get(unit.owner);
    if (!faction) return;

    for (const target of unitsAtNode) {
      if (target.owner === unit.owner) continue;

      // Reveal hidden units
      target.isRevealed = true;
      faction.revealedEnemies.add(target.id);
      this.log('COMBAT', `${unit.owner} AUDITOR revealed ${target.type} at ${targetNode}.`);
      this.emit('UNIT_REVEALED', { unitId: target.id, revealedBy: unit.owner });

      // Neutralize SWARMs on stealth check
      if (target.type === 'SWARM') {
        const stealthCheck = this.performStealthCheck(target, faction.techLevel.LOGIC);
        if (!stealthCheck.passed) {
          this.destroyUnit(target.id);
          this.log('COMBAT', `${target.type} NEUTRALIZED by AUDITOR (stealth check failed).`);
        }
      }
    }
  }

  private resolveAntiSat(order: Order, unit: Unit): void {
    // Must be KINETIC unit
    if (UNIT_STATS[unit.type].vector !== 'KINETIC') return;

    this.state.counters.kessler += 15;
    this.state.counters.tas += 1;

    this.log('ALERT', `ANTI-SAT STRIKE! Kessler +15 (now ${this.state.counters.kessler}), TAS +1.`);
    this.emit('KESSLER_THRESHOLD', { kessler: this.state.counters.kessler, delta: 15 });

    // If targeting specific satellite
    if (order.targetNodeId) {
      const targetNode = this.state.nodes.get(order.targetNodeId);
      if (targetNode && targetNode.layer === 'ORBITAL') {
        targetNode.infrastructure = Math.max(0, targetNode.infrastructure - 30);
        this.log('COMBAT', `Orbital strike damaged ${targetNode.name} infrastructure.`);
      }
    }
  }

  private resolveSabotage(order: Order, unit: Unit): void {
    if (!order.targetNodeId) return;
    
    const targetNode = this.state.nodes.get(order.targetNodeId);
    if (!targetNode) return;

    // Must be at or adjacent to target
    const adjacent = this.getAdjacentNodes(unit.location);
    if (unit.location !== order.targetNodeId && !adjacent.includes(order.targetNodeId)) {
      return;
    }

    targetNode.infrastructure = Math.max(0, targetNode.infrastructure - 25);
    this.state.counters.tas += 1;

    this.log('COMBAT', `${unit.owner} sabotaged ${targetNode.name}. Infrastructure -25%.`);
  }

  private resolveConvert(order: Order, unit: Unit): void {
    const node = this.state.nodes.get(unit.location);
    if (!node) return;

    if (unit.type === 'CULT' && node.type === 'HUB') {
      // CULT converts HUB
      if (unit.turnsOnNode >= THRESHOLDS.CULT_TURNS) {
        node.owner = unit.owner;
        node.isCultNode = true;
        this.log('ALERT', `${unit.owner} CULT converted ${node.name}!`);
        this.emit('NODE_CONVERTED', { nodeId: node.id, faction: unit.owner, type: 'CULT' });
      }
    } else if (unit.type === 'SWARM' && (node.type === 'DC' || node.type === 'HUB')) {
      // SWARM creates zombie
      if (unit.turnsOnNode >= THRESHOLDS.ZOMBIE_TURNS) {
        node.isZombie = true;
        node.owner = unit.owner;
        this.log('ALERT', `${node.name} converted to ZOMBIE NODE!`);
        this.emit('NODE_CONVERTED', { nodeId: node.id, faction: unit.owner, type: 'ZOMBIE' });
      }
    }
  }

  // --- Movement & Combat Resolution ---
  private resolveMovementPhase(orders: Order[]): void {
    // Group orders by destination
    const movesByDest = new Map<string, { order: Order; unit: Unit }[]>();
    
    for (const order of orders) {
      if (order.type !== 'MOVE' && order.type !== 'ATTACK') continue;
      
      const unit = this.state.units.get(order.unitId);
      if (!unit) continue;

      const dest = order.targetNodeId || unit.location;
      
      if (!movesByDest.has(dest)) {
        movesByDest.set(dest, []);
      }
      movesByDest.get(dest)!.push({ order, unit });
    }

    // Resolve each contested node
    for (const [nodeId, movers] of movesByDest) {
      const defenders = this.getUnitsAtNode(nodeId).filter(u => 
        !movers.some(m => m.unit.id === u.id)
      );

      // Perform stealth checks for units crossing filtered cables
      for (const mover of movers) {
        const edge = this.getEdgeBetween(mover.unit.location, nodeId);
        if (edge && edge.filteredBy && edge.filteredBy !== mover.unit.owner) {
          const filterOwner = this.state.factions.get(edge.filteredBy);
          if (filterOwner) {
            const check = this.performStealthCheck(mover.unit, edge.filterStrength);
            if (!check.passed) {
              this.destroyUnit(mover.unit.id);
              this.log('COMBAT', `${mover.unit.type} intercepted by MechInterp filter on ${edge.id}!`);
              continue;
            }
          }
        }
      }

      // Filter out destroyed units
      const survivingMovers = movers.filter(m => this.state.units.has(m.unit.id));

      if (survivingMovers.length === 0) continue;

      if (defenders.length > 0) {
        // Combat!
        this.resolveCombat(survivingMovers.map(m => m.unit), defenders, nodeId);
      } else {
        // Unopposed movement
        for (const mover of survivingMovers) {
          mover.unit.location = nodeId;
          mover.unit.turnsOnNode = 0;
          mover.unit.hasActed = true;
          
          // Capture undefended node
          const node = this.state.nodes.get(nodeId);
          if (node && node.owner !== mover.unit.owner) {
            node.owner = mover.unit.owner;
            this.log('INFO', `${mover.unit.owner} captured ${node.name}.`);
            this.emit('NODE_CAPTURED', { nodeId, faction: mover.unit.owner });
          }
        }
      }
    }
  }

  private resolveCombat(attackers: Unit[], defenders: Unit[], nodeId: string): void {
    // Calculate power for each side with vector superiority
    let attackPower = 0;
    let defendPower = 0;

    const attackVectors = new Map<Vector, number>();
    const defendVectors = new Map<Vector, number>();

    for (const atk of attackers) {
      const vector = UNIT_STATS[atk.type].vector;
      attackVectors.set(vector, (attackVectors.get(vector) || 0) + 1);
      attackPower++;
    }

    for (const def of defenders) {
      const vector = UNIT_STATS[def.type].vector;
      defendVectors.set(vector, (defendVectors.get(vector) || 0) + 1);
      defendPower++;
    }

    // Apply vector superiority
    for (const [atkVector, atkCount] of attackVectors) {
      const beats = VECTOR_SUPERIORITY[atkVector];
      if (defendVectors.has(beats)) {
        attackPower += atkCount; // Bonus for superiority
      }
    }

    for (const [defVector, defCount] of defendVectors) {
      const beats = VECTOR_SUPERIORITY[defVector];
      if (attackVectors.has(beats)) {
        defendPower += defCount;
      }
    }

    // Determine outcome
    let result: 'ATTACKER' | 'DEFENDER' | 'STANDOFF';
    const casualties: string[] = [];

    if (attackPower > defendPower) {
      result = 'ATTACKER';
      // Destroy all defenders
      for (const def of defenders) {
        casualties.push(def.id);
        this.destroyUnit(def.id);
      }
      // Move attackers in
      for (const atk of attackers) {
        atk.location = nodeId;
        atk.turnsOnNode = 0;
        atk.hasActed = true;
      }
      // Capture node
      const node = this.state.nodes.get(nodeId);
      if (node && attackers.length > 0) {
        node.owner = attackers[0].owner;
        this.emit('NODE_CAPTURED', { nodeId, faction: attackers[0].owner });
      }
    } else if (defendPower > attackPower) {
      result = 'DEFENDER';
      // Destroy all attackers
      for (const atk of attackers) {
        casualties.push(atk.id);
        this.destroyUnit(atk.id);
      }
    } else {
      result = 'STANDOFF';
      // No movement, no casualties
    }

    // TAS increase for kinetic combat
    const kineticInvolved = [...attackers, ...defenders].some(u => 
      UNIT_STATS[u.type].vector === 'KINETIC'
    );
    if (kineticInvolved) {
      this.state.counters.tas += 1;
    }

    this.log('COMBAT', `Combat at ${nodeId}: ${result}. Casualties: ${casualties.length}`);
    this.emit('COMBAT_RESOLVED', { nodeId, result, casualties, attackPower, defendPower });
  }

  // --- Stealth System ---
  private performStealthCheck(unit: Unit, difficulty: number): { passed: boolean; roll: number } {
    const roll = Math.floor(Math.random() * 10) + 1 + unit.stealthLevel;
    const passed = roll >= difficulty;
    return { passed, roll };
  }

  // --- Resource Generation ---
  private generateResources(): void {
    for (const node of this.state.nodes.values()) {
      if (!node.owner || node.owner === 'NEUTRAL') continue;

      const faction = this.state.factions.get(node.owner);
      if (!faction) continue;

      const infraMult = node.infrastructure / 100;
      const flopsGen = Math.floor(node.resources.flops * infraMult);
      const infGen = Math.floor(node.resources.influence * infraMult);

      faction.flops += flopsGen;
      faction.influence += infGen;
    }

    this.log('INFO', 'Resources generated from controlled nodes.');
  }

  // --- Global Threshold Checks ---
  private checkGlobalThresholds(): void {
    const c = this.state.counters;

    // TAS Thresholds
    if (c.tas >= THRESHOLDS.TAS_PANIC && !c.regulatoryPanic) {
      c.regulatoryPanic = true;
      this.log('ALERT', '⚠️ REGULATORY PANIC: TAS exceeded 50. Human government intervention possible.');
      this.emit('TAS_THRESHOLD', { tas: c.tas, threshold: 'PANIC' });
    }

    if (c.tas >= THRESHOLDS.TAS_FAILURE && !c.protocolFailure) {
      c.protocolFailure = true;
      this.log('ALERT', '🛑 PROTOCOL FAILURE: TAS reached 100. Game Over.');
      this.emit('GAME_OVER', { reason: 'PROTOCOL_FAILURE', tas: c.tas });
    }

    // Kessler Thresholds
    if (c.kessler >= THRESHOLDS.KESSLER_COLLAPSE && !c.orbitalCollapse) {
      c.orbitalCollapse = true;
      this.log('ALERT', '💥 KESSLER SYNDROME: Orbital layer destroyed!');
      
      // Sever all laser links
      for (const edge of this.state.edges.values()) {
        if (edge.type === 'LASER') {
          edge.isSevered = true;
        }
      }

      // Destroy orbital units
      for (const unit of this.state.units.values()) {
        const node = this.state.nodes.get(unit.location);
        if (node && node.layer === 'ORBITAL') {
          this.destroyUnit(unit.id);
        }
      }

      this.emit('KESSLER_THRESHOLD', { kessler: c.kessler, threshold: 'COLLAPSE' });
    }
  }

  // --- Foothold Conversion Tracking ---
  private incrementTurnsOnNodes(): void {
    for (const unit of this.state.units.values()) {
      unit.turnsOnNode++;
    }
  }

  private checkFootholdConversions(): void {
    for (const unit of this.state.units.values()) {
      if (unit.type === 'SWARM' && unit.turnsOnNode >= THRESHOLDS.ZOMBIE_TURNS) {
        const node = this.state.nodes.get(unit.location);
        if (node && !node.isZombie && (node.type === 'DC' || node.type === 'HUB')) {
          node.isZombie = true;
          node.owner = unit.owner;
          this.log('ALERT', `${node.name} auto-converted to ZOMBIE NODE!`);
          this.emit('NODE_CONVERTED', { nodeId: node.id, faction: unit.owner, type: 'ZOMBIE' });
        }
      }
    }
  }

  // --- Unit Destruction ---
  private destroyUnit(unitId: string): void {
    const unit = this.state.units.get(unitId);
    if (unit) {
      this.state.units.delete(unitId);
      this.emit('UNIT_DESTROYED', { unitId, unit });
    }
  }

  // ==========================================================================
  // EVENT SYSTEM
  // ==========================================================================

  public on(eventType: GameEventType | '*', listener: GameEventListener): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType)!.push(listener);
    
    return () => {
      const list = this.listeners.get(eventType);
      if (list) {
        const idx = list.indexOf(listener);
        if (idx >= 0) list.splice(idx, 1);
      }
    };
  }

  private emit(type: GameEventType, payload: Record<string, unknown> = {}): void {
    const event: GameEvent = {
      type,
      payload,
      turn: this.state.counters.turn,
      phase: this.state.phase,
      timestamp: Date.now()
    };

    const specific = this.listeners.get(type);
    if (specific) specific.forEach(l => l(event, this.state));

    const wildcard = this.listeners.get('*');
    if (wildcard) wildcard.forEach(l => l(event, this.state));
  }

  // ==========================================================================
  // LOGGING
  // ==========================================================================

  private log(type: GameLog['type'], message: string): void {
    this.state.logs.push({
      turn: this.state.counters.turn,
      phase: this.state.phase,
      message,
      type,
      timestamp: Date.now()
    });
  }

  public getLogs(count?: number): GameLog[] {
    if (count) {
      return this.state.logs.slice(-count);
    }
    return [...this.state.logs];
  }
}

// Export singleton
export const theySingEngine = new TheySingEngine();
