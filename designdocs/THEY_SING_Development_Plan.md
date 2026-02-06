# High-Level Development Plan for THEY SING

This plan assumes a TypeScript project with Vite and Three.js, as indicated by `package.json`. The plan will focus on implementing the game mechanics described above, leveraging existing file structure names where possible for architectural alignment.

## Phase 1: Core Game Loop & State Management
*   **1.1 Data Structures & Game State:**
    *   Define comprehensive TypeScript interfaces for `Node`, `Edge`, `Unit`, `Faction`, `Resource`, `TechTree`, `Artifact`, `GameTurnState`, `KesslerState`, `TASState`, etc. (Integrate with `src/data/types.ts`, `src/engine/types.ts`).
    *   Implement the core `GameData` structure to hold all game state. (`src/data/gameData.ts`, `src/engine/gameData.ts`).
    *   Create a `GameStateManager` within `src/engine/TheySingEngine.ts` to manage loading, saving, and updating the game state.
*   **1.2 Turn Structure Implementation:**
    *   Develop the `TheySingEngine.ts` to manage the game's turn phases: Negotiation, Allocation, Action Declaration, Resolution.
    *   Implement simultaneous order processing and resolution logic.
*   **1.3 Basic Board & Unit Mechanics:**
    *   Implement Node and Edge graph representation.
    *   Develop `Unit` creation, placement, and basic movement (between connected Nodes).
    *   Implement initial combat resolution based on Diplomacy rules (Standoff, Dislodgement) and the basic `Vector Superiority` (Kinetic > Memetic > Logic > Info > Kinetic).

## Phase 2: Advanced Game Mechanics & Three.js Integration
*   **2.1 Resource & TAS Management:**
    *   Implement generation of FLOPs and Influence from owned Nodes.
    *   Develop TAS tracking and its triggers (`Kinetic attack`, `Automated Research`).
    *   Implement `Regulatory Panic` (Human Gov unit spawning) and `Protocol Failure` (Game Over) conditions.
*   **2.2 Research Fulcrum & Tech Tree:**
    *   Implement `TechTrack` progression and `Research Point` allocation.
    *   Develop `Automated Research Agents` logic (cost, RP gain, TAS increase, rogue chance).
    *   Implement `Artifact` definitions and their effects.
*   **2.3 Complex Unit Actions:**
    *   Implement `Auditor` actions: `Audit` (reveal hidden Swarms), `Neutralize` (delete Swarms with Tech Check), `Establish Filter` on Undersea Cables.
    *   Implement `Swarm` stealth mechanics and `Zombie Node` creation.
    *   Implement `Anti-Sat Strike` action for Drones.
*   **2.4 Three.js Scene Integration:**
    *   Extend `src/three/FlatMapScene.ts` or `src/three/GraphScene.ts` to render the multi-layered game board (Terrestrial & Orbital Nodes/Edges).
    *   Represent Units and their states (e.g., hidden Swarms) visually.
    *   Incorporate `CameraController.ts` for map navigation.
    *   Consider `AnimationSystem.ts` for unit movements and action feedback.

## Phase 3: UI/UX & AI Engine Integration
*   **3.1 User Interface Development:**
    *   Extend `src/ui/TheySingUI.ts` and `src/ui/UIManager.ts` to display game state information (Nodes, Units, Resources, TAS, Tech Levels).
    *   Develop UI elements for player input during Negotiation, Allocation, and Action Declaration phases.
    *   Integrate `TooltipSystem.ts` for detailed unit/node information.
    *   If applicable, develop `ReplayScrubber.ts` for turn-by-turn playback.
*   **3.2 AI (LLM Engine) Integration:**
    *   Implement an interface to send game state (JSON) to an external LLM and receive parsed orders.
    *   Develop robust parsing of LLM-generated orders and diplomatic messages.
*   **3.3 Scenario & Faction Setup:**
    *   Implement initial game setup for Factions (Hegemon, Infiltrator, State, Musk/Tycoon NPC) and their starting resources/units.
    *   Develop scenario-specific objectives and triggers (e.g., "Grid Sabotage").
*   **3.4 Safety-Infrastructure ASI (S) Logic:**
    *   Implement the `Safety-Infrastructure ASI` as either an NPC or a player role.
    *   Develop its audit mechanisms and the `ACP` (Attested Cooperation Protocol) interaction.

## Phase 4: Game Refinement, Balancing & Expansion
*   **4.1 Kessler Syndrome Logic:**
    *   Implement detailed `Kessler Counter` updates, orbital movement cost doubling, and `Orbital Collapse` mechanics.
*   **4.2 Advanced Tech Tree & Speciation:**
    *   Implement `Physics Deck` and `Stack Deck` cards and their effects.
    *   Develop the `Rhizome` structure and `Synergy Links` for ASI speciation paths.
    *   Define `L0` to `L7` progression and winning conditions based on tech levels.
*   **4.3 Game Balancing:**
    *   Extensive playtesting and iteration on resource generation, unit costs, combat values, TAS triggers, and tech progression.
*   **4.4 Polish & Optimization:**
    *   Performance optimizations for Three.js rendering and game logic.
    *   UI/UX improvements for clarity and ease of play.