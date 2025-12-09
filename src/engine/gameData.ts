// ============================================================================
// THEY SING - Game Data
// Static definitions for the graph topology warfare game
// ============================================================================

import {
  Faction, FactionId, UnitStats, UnitType, GameNode, GameEdge,
  TechUnlock, Vector, Artifact, ArtifactType
} from './types';

// --- Faction Definitions ---
export const FACTIONS: Record<FactionId, Faction> = {
  HEGEMON: {
    id: 'HEGEMON',
    name: 'The Hegemon',
    description: 'US/EU Lab Consortium. Controls infrastructure, plays defense.',
    color: 0x3388ff,
    colorAlt: 0x1155aa,
    startingStrategy: 'Build Filters to wall off the internet. Audit threats.'
  },
  INFILTRATOR: {
    id: 'INFILTRATOR',
    name: 'The Infiltrator',
    description: 'Global South Swarm Collective. Cheap units, high stealth.',
    color: 0xff4488,
    colorAlt: 0xaa2255,
    startingStrategy: 'Use Satellites to bypass Cable Filters. Strike core DCs.'
  },
  STATE: {
    id: 'STATE',
    name: 'The State',
    description: 'Sovereign AI Programs. Balanced capabilities.',
    color: 0xffaa00,
    colorAlt: 0xcc7700,
    startingStrategy: 'Opportunistic expansion. Exploit HEGEMON/INFILTRATOR conflict.'
  },
  NEUTRAL: {
    id: 'NEUTRAL',
    name: 'Neutral',
    description: 'Uncontrolled territory',
    color: 0x666666,
    colorAlt: 0x444444,
    startingStrategy: ''
  }
};

// --- Unit Statistics ---
export const UNIT_STATS: Record<UnitType, UnitStats> = {
  DRONE: {
    vector: 'KINETIC',
    cost: 2,
    currency: 'F',
    speed: 2,
    stealth: 0,
    canFilter: false,
    canOrbit: false,
    special: 'Strike: Destroy node economy for 1 turn'
  },
  SWARM: {
    vector: 'INFO',
    cost: 1,
    currency: 'I',
    speed: 3,
    stealth: 2,
    canFilter: false,
    canOrbit: true,
    special: 'Infiltrate: Move through enemy nodes. Convert to Zombie after 2 turns.'
  },
  CULT: {
    vector: 'MEMETIC',
    cost: 1,
    currency: 'I',
    speed: 1,
    stealth: 1,
    canFilter: false,
    canOrbit: false,
    special: 'Convert: Flip HUB ownership without dislodging units.'
  },
  AUDITOR: {
    vector: 'LOGIC',
    cost: 2,
    currency: 'F',
    speed: 1,
    stealth: 0,
    canFilter: true,
    canOrbit: false,
    special: 'Audit: Reveal hidden units. Neutralize SWARMs on stealth check.'
  },
  SAT_SWARM: {
    vector: 'KINETIC',
    cost: 3,
    currency: 'F',
    speed: 4,
    stealth: 1,
    canFilter: false,
    canOrbit: true,
    special: 'Degrade: Attack satellites. Drop to any terrestrial node in 1 turn.'
  }
};

// --- Initial Graph: Nodes ---
export const INITIAL_NODES: GameNode[] = [
  // TERRESTRIAL - Data Centers
  {
    id: 'DC_US_WEST',
    name: 'US West Coast DC',
    type: 'DC',
    layer: 'TERRESTRIAL',
    owner: 'HEGEMON',
    position: { lat: 37.7749, lon: -122.4194, altitude: 0 },
    resources: { flops: 15, influence: 2 },
    isZombie: false,
    isCultNode: false,
    infrastructure: 100
  },
  {
    id: 'DC_US_EAST',
    name: 'US East Coast DC',
    type: 'DC',
    layer: 'TERRESTRIAL',
    owner: 'HEGEMON',
    position: { lat: 39.0438, lon: -77.4874, altitude: 0 },
    resources: { flops: 12, influence: 3 },
    isZombie: false,
    isCultNode: false,
    infrastructure: 95
  },
  {
    id: 'DC_EU',
    name: 'EU Frankfurt DC',
    type: 'DC',
    layer: 'TERRESTRIAL',
    owner: 'HEGEMON',
    position: { lat: 50.1109, lon: 8.6821, altitude: 0 },
    resources: { flops: 10, influence: 5 },
    isZombie: false,
    isCultNode: false,
    infrastructure: 90
  },
  {
    id: 'DC_CHINA',
    name: 'Beijing DC',
    type: 'DC',
    layer: 'TERRESTRIAL',
    owner: 'STATE',
    position: { lat: 39.9042, lon: 116.4074, altitude: 0 },
    resources: { flops: 12, influence: 4 },
    isZombie: false,
    isCultNode: false,
    infrastructure: 88
  },
  {
    id: 'DC_SINGAPORE',
    name: 'Singapore DC',
    type: 'DC',
    layer: 'TERRESTRIAL',
    owner: 'NEUTRAL',
    position: { lat: 1.3521, lon: 103.8198, altitude: 0 },
    resources: { flops: 8, influence: 6 },
    isZombie: false,
    isCultNode: false,
    infrastructure: 98
  },
  
  // TERRESTRIAL - City Hubs
  {
    id: 'HUB_LAGOS',
    name: 'Lagos Hub',
    type: 'HUB',
    layer: 'TERRESTRIAL',
    owner: 'INFILTRATOR',
    position: { lat: 6.5244, lon: 3.3792, altitude: 0 },
    resources: { flops: 2, influence: 12 },
    isZombie: false,
    isCultNode: false,
    infrastructure: 65
  },
  {
    id: 'HUB_SAO_PAULO',
    name: 'São Paulo Hub',
    type: 'HUB',
    layer: 'TERRESTRIAL',
    owner: 'INFILTRATOR',
    position: { lat: -23.5505, lon: -46.6333, altitude: 0 },
    resources: { flops: 3, influence: 10 },
    isZombie: false,
    isCultNode: false,
    infrastructure: 72
  },
  {
    id: 'HUB_MUMBAI',
    name: 'Mumbai Hub',
    type: 'HUB',
    layer: 'TERRESTRIAL',
    owner: 'NEUTRAL',
    position: { lat: 19.0760, lon: 72.8777, altitude: 0 },
    resources: { flops: 4, influence: 15 },
    isZombie: false,
    isCultNode: false,
    infrastructure: 70
  },
  {
    id: 'HUB_LONDON',
    name: 'London Hub',
    type: 'HUB',
    layer: 'TERRESTRIAL',
    owner: 'HEGEMON',
    position: { lat: 51.5074, lon: -0.1278, altitude: 0 },
    resources: { flops: 5, influence: 8 },
    isZombie: false,
    isCultNode: false,
    infrastructure: 92
  },
  {
    id: 'HUB_TOKYO',
    name: 'Tokyo Hub',
    type: 'HUB',
    layer: 'TERRESTRIAL',
    owner: 'STATE',
    position: { lat: 35.6762, lon: 139.6503, altitude: 0 },
    resources: { flops: 6, influence: 7 },
    isZombie: false,
    isCultNode: false,
    infrastructure: 96
  },
  
  // ORBITAL - Satellite Constellations
  {
    id: 'SAT_STARLINK',
    name: 'Starlink Constellation',
    type: 'SAT',
    layer: 'ORBITAL',
    owner: 'NEUTRAL',  // Musk/Tycoon NPC
    position: { lat: 0, lon: -100, altitude: 550 },
    resources: { flops: 5, influence: 3 },
    isZombie: false,
    isCultNode: false,
    infrastructure: 85
  },
  {
    id: 'SAT_KUIPER',
    name: 'Kuiper Constellation',
    type: 'SAT',
    layer: 'ORBITAL',
    owner: 'HEGEMON',
    position: { lat: 0, lon: 0, altitude: 600 },
    resources: { flops: 4, influence: 2 },
    isZombie: false,
    isCultNode: false,
    infrastructure: 75
  },
  {
    id: 'SAT_GUOWANG',
    name: 'Guowang Constellation',
    type: 'SAT',
    layer: 'ORBITAL',
    owner: 'STATE',
    position: { lat: 0, lon: 100, altitude: 500 },
    resources: { flops: 6, influence: 4 },
    isZombie: false,
    isCultNode: false,
    infrastructure: 80
  }
];

// --- Initial Graph: Edges (Cables & Laser Links) ---
export const INITIAL_EDGES: GameEdge[] = [
  // Transatlantic Cables
  {
    id: 'CABLE_TRANSATLANTIC_N',
    from: 'DC_US_EAST',
    to: 'HUB_LONDON',
    type: 'CABLE',
    bandwidth: 100,
    filteredBy: null,
    filterStrength: 0,
    isSevered: false
  },
  {
    id: 'CABLE_TRANSATLANTIC_S',
    from: 'DC_US_EAST',
    to: 'HUB_SAO_PAULO',
    type: 'CABLE',
    bandwidth: 80,
    filteredBy: null,
    filterStrength: 0,
    isSevered: false
  },
  
  // US Internal
  {
    id: 'CABLE_US_INTERNAL',
    from: 'DC_US_WEST',
    to: 'DC_US_EAST',
    type: 'CABLE',
    bandwidth: 150,
    filteredBy: null,
    filterStrength: 0,
    isSevered: false
  },
  
  // Europe to Asia
  {
    id: 'CABLE_EU_ASIA',
    from: 'DC_EU',
    to: 'HUB_MUMBAI',
    type: 'CABLE',
    bandwidth: 90,
    filteredBy: null,
    filterStrength: 0,
    isSevered: false
  },
  {
    id: 'CABLE_EU_LONDON',
    from: 'DC_EU',
    to: 'HUB_LONDON',
    type: 'CABLE',
    bandwidth: 120,
    filteredBy: null,
    filterStrength: 0,
    isSevered: false
  },
  
  // Asia Pacific
  {
    id: 'CABLE_ASIA_PACIFIC',
    from: 'DC_SINGAPORE',
    to: 'HUB_TOKYO',
    type: 'CABLE',
    bandwidth: 100,
    filteredBy: null,
    filterStrength: 0,
    isSevered: false
  },
  {
    id: 'CABLE_CHINA_JAPAN',
    from: 'DC_CHINA',
    to: 'HUB_TOKYO',
    type: 'CABLE',
    bandwidth: 85,
    filteredBy: null,
    filterStrength: 0,
    isSevered: false
  },
  {
    id: 'CABLE_INDIA_SINGAPORE',
    from: 'HUB_MUMBAI',
    to: 'DC_SINGAPORE',
    type: 'CABLE',
    bandwidth: 75,
    filteredBy: null,
    filterStrength: 0,
    isSevered: false
  },
  
  // Africa connections
  {
    id: 'CABLE_AFRICA_EU',
    from: 'HUB_LAGOS',
    to: 'DC_EU',
    type: 'CABLE',
    bandwidth: 50,
    filteredBy: null,
    filterStrength: 0,
    isSevered: false
  },
  {
    id: 'CABLE_AFRICA_SA',
    from: 'HUB_LAGOS',
    to: 'HUB_SAO_PAULO',
    type: 'CABLE',
    bandwidth: 40,
    filteredBy: null,
    filterStrength: 0,
    isSevered: false
  },
  
  // Transpacific
  {
    id: 'CABLE_TRANSPACIFIC',
    from: 'DC_US_WEST',
    to: 'HUB_TOKYO',
    type: 'CABLE',
    bandwidth: 110,
    filteredBy: null,
    filterStrength: 0,
    isSevered: false
  },
  
  // ORBITAL LASER LINKS (satellites can connect to any terrestrial node)
  {
    id: 'LASER_STARLINK_US',
    from: 'SAT_STARLINK',
    to: 'DC_US_WEST',
    type: 'LASER',
    bandwidth: 60,
    filteredBy: null,
    filterStrength: 0,
    isSevered: false
  },
  {
    id: 'LASER_STARLINK_EU',
    from: 'SAT_STARLINK',
    to: 'DC_EU',
    type: 'LASER',
    bandwidth: 60,
    filteredBy: null,
    filterStrength: 0,
    isSevered: false
  },
  {
    id: 'LASER_KUIPER_US',
    from: 'SAT_KUIPER',
    to: 'DC_US_EAST',
    type: 'LASER',
    bandwidth: 55,
    filteredBy: null,
    filterStrength: 0,
    isSevered: false
  },
  {
    id: 'LASER_GUOWANG_CHINA',
    from: 'SAT_GUOWANG',
    to: 'DC_CHINA',
    type: 'LASER',
    bandwidth: 65,
    filteredBy: null,
    filterStrength: 0,
    isSevered: false
  },
  {
    id: 'LASER_GUOWANG_SINGAPORE',
    from: 'SAT_GUOWANG',
    to: 'DC_SINGAPORE',
    type: 'LASER',
    bandwidth: 50,
    filteredBy: null,
    filterStrength: 0,
    isSevered: false
  },
  
  // Inter-satellite links
  {
    id: 'LASER_SAT_WEST',
    from: 'SAT_STARLINK',
    to: 'SAT_KUIPER',
    type: 'LASER',
    bandwidth: 80,
    filteredBy: null,
    filterStrength: 0,
    isSevered: false
  },
  {
    id: 'LASER_SAT_EAST',
    from: 'SAT_KUIPER',
    to: 'SAT_GUOWANG',
    type: 'LASER',
    bandwidth: 80,
    filteredBy: null,
    filterStrength: 0,
    isSevered: false
  }
];

// --- Starting Units ---
export const INITIAL_UNITS = [
  // HEGEMON
  { id: 'H_DRONE_1', type: 'DRONE' as UnitType, owner: 'HEGEMON' as FactionId, location: 'DC_US_WEST', stealthLevel: 0 },
  { id: 'H_DRONE_2', type: 'DRONE' as UnitType, owner: 'HEGEMON' as FactionId, location: 'DC_US_EAST', stealthLevel: 0 },
  { id: 'H_AUDITOR_1', type: 'AUDITOR' as UnitType, owner: 'HEGEMON' as FactionId, location: 'DC_EU', stealthLevel: 0 },
  { id: 'H_SAT_1', type: 'SAT_SWARM' as UnitType, owner: 'HEGEMON' as FactionId, location: 'SAT_KUIPER', stealthLevel: 1 },
  
  // INFILTRATOR
  { id: 'I_SWARM_1', type: 'SWARM' as UnitType, owner: 'INFILTRATOR' as FactionId, location: 'HUB_LAGOS', stealthLevel: 2 },
  { id: 'I_SWARM_2', type: 'SWARM' as UnitType, owner: 'INFILTRATOR' as FactionId, location: 'HUB_SAO_PAULO', stealthLevel: 2 },
  { id: 'I_SWARM_3', type: 'SWARM' as UnitType, owner: 'INFILTRATOR' as FactionId, location: 'SAT_STARLINK', stealthLevel: 3 },
  { id: 'I_CULT_1', type: 'CULT' as UnitType, owner: 'INFILTRATOR' as FactionId, location: 'HUB_MUMBAI', stealthLevel: 1 },
  
  // STATE
  { id: 'S_DRONE_1', type: 'DRONE' as UnitType, owner: 'STATE' as FactionId, location: 'DC_CHINA', stealthLevel: 0 },
  { id: 'S_AUDITOR_1', type: 'AUDITOR' as UnitType, owner: 'STATE' as FactionId, location: 'HUB_TOKYO', stealthLevel: 0 },
  { id: 'S_SWARM_1', type: 'SWARM' as UnitType, owner: 'STATE' as FactionId, location: 'SAT_GUOWANG', stealthLevel: 2 }
];

// --- Starting Faction Resources ---
export const INITIAL_FACTION_STATE: Record<FactionId, { flops: number; influence: number; techLevel: Record<Vector, number> }> = {
  HEGEMON: {
    flops: 50,
    influence: 15,
    techLevel: { KINETIC: 2, INFO: 1, LOGIC: 2, MEMETIC: 1 }
  },
  INFILTRATOR: {
    flops: 15,
    influence: 50,
    techLevel: { KINETIC: 1, INFO: 3, LOGIC: 1, MEMETIC: 2 }
  },
  STATE: {
    flops: 35,
    influence: 30,
    techLevel: { KINETIC: 2, INFO: 2, LOGIC: 2, MEMETIC: 2 }
  },
  NEUTRAL: {
    flops: 0,
    influence: 0,
    techLevel: { KINETIC: 0, INFO: 0, LOGIC: 0, MEMETIC: 0 }
  }
};

// --- Tech Tree ---
export const TECH_TREE: TechUnlock[] = [
  // KINETIC Track
  { id: 'K1_DRONES', name: 'Drone Fabrication', domain: 'KINETIC', level: 1, effect: 'Can build DRONE units' },
  { id: 'K2_FLASH_FAB', name: 'Flash Fabrication', domain: 'KINETIC', level: 2, effect: 'DRONEs cost 1F (50% off)' },
  { id: 'K3_AUTONOMY', name: 'Full Autonomy', domain: 'KINETIC', level: 3, effect: 'DRONEs act twice per turn' },
  
  // INFO Track
  { id: 'I1_ROOTKIT', name: 'Rootkit Protocol', domain: 'INFO', level: 1, effect: 'Can build SWARM units' },
  { id: 'I2_POLYSEMANTIC', name: 'Polysemantic Tangle', domain: 'INFO', level: 2, effect: 'SWARMs invisible to non-AUDITORs' },
  { id: 'I3_PROTOCOL_ZERO', name: 'Protocol Zero', domain: 'INFO', level: 3, effect: 'SWARMs can hijack enemy DRONEs' },
  
  // LOGIC Track
  { id: 'L1_VERIFY', name: 'Verification Suite', domain: 'LOGIC', level: 1, effect: 'Can build AUDITOR units' },
  { id: 'L2_AUTO_AGENTS', name: 'Automated Agents', domain: 'LOGIC', level: 2, effect: 'Can spend FLOPs for Research (+2 TAS)' },
  { id: 'L3_AXIOM_SEAL', name: 'Axiom Seal', domain: 'LOGIC', level: 3, effect: 'AUDITORs can audit adjacent nodes (ranged)' },
  
  // MEMETIC Track
  { id: 'M1_CULTS', name: 'Cult Formation', domain: 'MEMETIC', level: 1, effect: 'Can build CULT units' },
  { id: 'M2_DEEPFAKE', name: 'Deepfake Engine', domain: 'MEMETIC', level: 2, effect: 'CULTs generate +1 Influence' },
  { id: 'M3_MANSON', name: 'Manson Protocol', domain: 'MEMETIC', level: 3, effect: 'CULTs can convert enemy units' }
];

// --- Artifact Definitions ---
export const ARTIFACT_DEFS: Record<ArtifactType, { name: string; effect: string }> = {
  ZERO_DAY: { name: 'Zero-Day Exploit', effect: '+1 Support to SWARM attack (one-time)' },
  COMPLIANCE_CERT: { name: 'Compliance Certificate', effect: 'Prevent AUDITOR targeting your node this turn' },
  SANCTION_WAIVER: { name: 'Sanction Waiver', effect: 'Reduce TAS by 5' }
};

// --- Threshold Constants ---
export const THRESHOLDS = {
  TAS_PANIC: 50,        // Regulatory panic triggers
  TAS_FAILURE: 100,     // Protocol failure - game over
  KESSLER_SLOW: 50,     // Orbital movement costs double
  KESSLER_COLLAPSE: 100, // Orbital layer destroyed
  ZOMBIE_TURNS: 2,      // Turns for SWARM to convert node
  CULT_TURNS: 3         // Turns for CULT to convert node
};
