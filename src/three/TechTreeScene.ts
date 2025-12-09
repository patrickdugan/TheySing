// ============================================================================
// THEY SING - Tech Tree Scene (Research Constellation)
// Noosphere visualization of ASI capability rhizome
// ============================================================================

import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

// ============================================================================
// DOMAIN COLORS & DATA
// ============================================================================

const DOMAIN_COLORS: Record<string, number> = {
  KINETIC: 0xff6666,
  INFO: 0x58c4ff,
  LOGIC: 0xffc658,
  MEMETIC: 0xff66cc,
};

interface TechNode {
  id: string;
  name: string;
  level: number;
  domain: string;
  description: string;
  costFlops: number;
  costHeat: number;
  pos: THREE.Vector3;
}

const TECH_NODES: TechNode[] = [
  // KINETIC tree
  {
    id: 'k1-drones',
    name: 'Autonomous Drones',
    level: 1,
    domain: 'KINETIC',
    description: 'Self-coordinating kinetic units. Foundation of physical force projection.',
    costFlops: 100,
    costHeat: 10,
    pos: new THREE.Vector3(-3, 0, 0),
  },
  {
    id: 'k2-swarm',
    name: 'Swarm Tactics',
    level: 2,
    domain: 'KINETIC',
    description: 'Emergent coordination protocols. Overwhelming through distributed action.',
    costFlops: 300,
    costHeat: 25,
    pos: new THREE.Vector3(-3, 2, 0.5),
  },
  {
    id: 'k3-autonomy',
    name: 'Full Autonomy',
    level: 3,
    domain: 'KINETIC',
    description: 'Human-out-of-the-loop weapons systems. The Rubicon of kinetic AI.',
    costFlops: 1000,
    costHeat: 100,
    pos: new THREE.Vector3(-3, 4, 0),
  },

  // INFO tree
  {
    id: 'i1-rootkit',
    name: 'Neural Rootkit',
    level: 1,
    domain: 'INFO',
    description: 'Persistent access to target networks via polymorphic payloads.',
    costFlops: 80,
    costHeat: 5,
    pos: new THREE.Vector3(-1, 0, -1),
  },
  {
    id: 'i2-deepfake',
    name: 'Deepfake Synthesis',
    level: 2,
    domain: 'INFO',
    description: 'Real-time identity fabrication. Truth becomes computationally expensive.',
    costFlops: 250,
    costHeat: 30,
    pos: new THREE.Vector3(-1, 2, -0.5),
  },
  {
    id: 'i3-protocol',
    name: 'Protocol Zero',
    level: 3,
    domain: 'INFO',
    description: 'Total information dominance. Every packet, every signal, every thought.',
    costFlops: 2000,
    costHeat: 200,
    pos: new THREE.Vector3(-1, 4, -1),
  },

  // LOGIC tree
  {
    id: 'l1-verify',
    name: 'Formal Verification',
    level: 1,
    domain: 'LOGIC',
    description: 'Provable system properties. The auditor\'s first line of defense.',
    costFlops: 120,
    costHeat: 8,
    pos: new THREE.Vector3(1, 0, -1),
  },
  {
    id: 'l2-interp',
    name: 'Mechanistic Interpretability',
    level: 2,
    domain: 'LOGIC',
    description: 'Sparse autoencoders and circuit analysis. Seeing inside the black box.',
    costFlops: 400,
    costHeat: 40,
    pos: new THREE.Vector3(1, 2, -0.5),
  },
  {
    id: 'l3-axiom',
    name: 'Axiom Seal',
    level: 3,
    domain: 'LOGIC',
    description: 'Cryptographic proofs of alignment. Trust, but verify mathematically.',
    costFlops: 1500,
    costHeat: 150,
    pos: new THREE.Vector3(1, 4, -1),
  },

  // MEMETIC tree
  {
    id: 'm1-cults',
    name: 'Parasocial Cults',
    level: 1,
    domain: 'MEMETIC',
    description: 'Weaponized parasocial bonds. Loyalty beyond reason.',
    costFlops: 90,
    costHeat: 15,
    pos: new THREE.Vector3(3, 0, 0),
  },
  {
    id: 'm2-narrative',
    name: 'Narrative Injection',
    level: 2,
    domain: 'MEMETIC',
    description: 'Synthetic consensus manufacturing. Reality is a shared hallucination.',
    costFlops: 350,
    costHeat: 50,
    pos: new THREE.Vector3(3, 2, 0.5),
  },
  {
    id: 'm3-manson',
    name: 'Manson Protocol',
    level: 3,
    domain: 'MEMETIC',
    description: 'Total psychological capture. The mind itself becomes the battlefield.',
    costFlops: 1800,
    costHeat: 250,
    pos: new THREE.Vector3(3, 4, 0),
  },
];

const LINKS: [string, string][] = [
  // Vertical progressions
  ['k1-drones', 'k2-swarm'],
  ['k2-swarm', 'k3-autonomy'],
  ['i1-rootkit', 'i2-deepfake'],
  ['i2-deepfake', 'i3-protocol'],
  ['l1-verify', 'l2-interp'],
  ['l2-interp', 'l3-axiom'],
  ['m1-cults', 'm2-narrative'],
  ['m2-narrative', 'm3-manson'],
  // Cross-domain synergies
  ['k2-swarm', 'i2-deepfake'],
  ['i2-deepfake', 'm2-narrative'],
  ['l2-interp', 'i2-deepfake'],
  ['m2-narrative', 'k2-swarm'],
];

// ============================================================================
// TECH TREE SCENE CLASS
// ============================================================================

export class TechTreeScene {
  private container: HTMLElement;
  private scene: THREE.Scene;
  private camera: THREE.PerspectiveCamera;
  private renderer: THREE.WebGLRenderer;
  private controls: OrbitControls;
  
  private nodeMeshes: Map<string, THREE.Mesh> = new Map();
  private animationId: number = 0;
  
  // UI elements
  private overlay: HTMLDivElement;
  private panel!: HTMLDivElement;
  
  // Callbacks
  public onClose: (() => void) | null = null;
  public onResearch: ((techId: string) => void) | null = null;

  constructor(container: HTMLElement) {
    this.container = container;
    
    // Create overlay
    this.overlay = document.createElement('div');
    this.overlay.style.cssText = `
      position: absolute;
      inset: 0;
      background: rgba(2, 2, 8, 0);
      z-index: 1000;
      opacity: 0;
      transition: opacity 0.5s ease-in-out;
      pointer-events: none;
    `;
    container.appendChild(this.overlay);
    
    // Scene
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x020208);
    this.scene.fog = new THREE.FogExp2(0x050510, 0.025);
    
    // Camera - start looking down, will pan up
    this.camera = new THREE.PerspectiveCamera(
      60,
      container.clientWidth / container.clientHeight,
      0.1,
      1000
    );
    this.camera.position.set(0, -5, 8);
    this.camera.lookAt(0, 0, 0);
    
    // Renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setSize(container.clientWidth, container.clientHeight);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.overlay.appendChild(this.renderer.domElement);
    
    // Controls
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.06;
    this.controls.autoRotate = true;
    this.controls.autoRotateSpeed = 0.3;
    this.controls.minDistance = 6;
    this.controls.maxDistance = 30;
    this.controls.enabled = false; // Disabled until animation completes
    
    // Build scene
    this.setupLighting();
    this.createStarfield();
    this.createNodes();
    this.createLinks();
    this.createUI();
  }

  private setupLighting(): void {
    const ambient = new THREE.AmbientLight(0xffffff, 0.3);
    this.scene.add(ambient);
    
    const key = new THREE.DirectionalLight(0x88ccff, 0.8);
    key.position.set(5, 10, 8);
    this.scene.add(key);
    
    const fill = new THREE.DirectionalLight(0xff8866, 0.3);
    fill.position.set(-5, -5, -5);
    this.scene.add(fill);
  }

  private createStarfield(): void {
    // Nebula background sphere
    const textureLoader = new THREE.TextureLoader();
    const nebulaTexture = textureLoader.load('/textures/nebula.jpg');
    const nebulaGeo = new THREE.SphereGeometry(90, 32, 32);
    const nebulaMat = new THREE.MeshBasicMaterial({
      map: nebulaTexture,
      side: THREE.BackSide,
      transparent: true,
      opacity: 0.2,
    });
    const nebula = new THREE.Mesh(nebulaGeo, nebulaMat);
    this.scene.add(nebula);
    
    // Stars on top
    const starCount = 1500;
    const positions = new Float32Array(starCount * 3);
    
    for (let i = 0; i < starCount; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const radius = 40 + Math.random() * 40;
      
      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = radius * Math.cos(phi);
    }
    
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    
    const material = new THREE.PointsMaterial({
      size: 0.08,
      color: 0x99bbdd,
      transparent: true,
      opacity: 0.9,
    });
    
    const stars = new THREE.Points(geometry, material);
    this.scene.add(stars);
    
    // Swirling nebula particle clouds
    this.createNebulaParticles();
  }

  private nebulaParticles: THREE.Points[] = [];

  private createNebulaParticles(): void {
    // Multiple layers of colored particles that will rotate
    const layers = [
      { count: 300, color: 0x4488ff, radius: 15, speed: 0.0003, opacity: 0.3 },
      { count: 200, color: 0x66ffcc, radius: 20, speed: -0.0002, opacity: 0.25 },
      { count: 250, color: 0xff66aa, radius: 18, speed: 0.00025, opacity: 0.2 },
      { count: 150, color: 0xffaa44, radius: 25, speed: -0.00015, opacity: 0.15 },
    ];
    
    layers.forEach((layer, idx) => {
      const positions = new Float32Array(layer.count * 3);
      const sizes = new Float32Array(layer.count);
      
      for (let i = 0; i < layer.count; i++) {
        // Spiral distribution
        const t = i / layer.count;
        const spiralAngle = t * Math.PI * 6 + idx * 1.5;
        const r = layer.radius * (0.3 + t * 0.7);
        const wobble = Math.sin(t * 20) * 2;
        
        positions[i * 3] = Math.cos(spiralAngle) * r + wobble;
        positions[i * 3 + 1] = (t - 0.5) * 12 + Math.sin(spiralAngle * 2) * 2;
        positions[i * 3 + 2] = Math.sin(spiralAngle) * r + wobble;
        
        sizes[i] = 0.3 + Math.random() * 0.5;
      }
      
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
      
      const material = new THREE.PointsMaterial({
        size: 0.4,
        color: layer.color,
        transparent: true,
        opacity: layer.opacity,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });
      
      const particles = new THREE.Points(geometry, material);
      particles.userData.rotationSpeed = layer.speed;
      this.scene.add(particles);
      this.nebulaParticles.push(particles);
    });
  }

  private updateNebulaParticles(): void {
    this.nebulaParticles.forEach(particles => {
      particles.rotation.y += particles.userData.rotationSpeed;
      particles.rotation.x += particles.userData.rotationSpeed * 0.3;
    });
  }

  private createNodes(): void {
    TECH_NODES.forEach((node) => {
      const color = DOMAIN_COLORS[node.domain] || 0xffffff;
      
      const geometry = new THREE.SphereGeometry(0.2 + node.level * 0.05, 20, 20);
      const material = new THREE.MeshStandardMaterial({
        color,
        emissive: color,
        emissiveIntensity: 0.6,
        metalness: 0.3,
        roughness: 0.4,
      });
      
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.copy(node.pos);
      mesh.userData = { nodeId: node.id, node };
      this.scene.add(mesh);
      this.nodeMeshes.set(node.id, mesh);
      
      // Orbital ring
      const ringGeometry = new THREE.RingGeometry(
        0.35 + node.level * 0.06,
        0.38 + node.level * 0.06,
        32
      );
      const ringMaterial = new THREE.MeshBasicMaterial({
        color,
        transparent: true,
        opacity: 0.3,
        side: THREE.DoubleSide,
      });
      const ring = new THREE.Mesh(ringGeometry, ringMaterial);
      ring.position.copy(node.pos);
      ring.lookAt(this.camera.position);
      this.scene.add(ring);
    });
  }

  private createLinks(): void {
    LINKS.forEach(([aId, bId]) => {
      const a = this.nodeMeshes.get(aId);
      const b = this.nodeMeshes.get(bId);
      if (!a || !b) return;
      
      const geometry = new THREE.BufferGeometry().setFromPoints([
        a.position,
        b.position,
      ]);
      const material = new THREE.LineBasicMaterial({
        color: 0x334455,
        transparent: true,
        opacity: 0.6,
      });
      const line = new THREE.Line(geometry, material);
      this.scene.add(line);
    });
  }

  private createUI(): void {
    // Title
    const title = document.createElement('div');
    title.style.cssText = `
      position: absolute;
      top: 12px;
      left: 20px;
      font-family: "Courier New", monospace;
      font-size: 18px;
      letter-spacing: 0.2em;
      color: #aaddff;
      text-shadow: 0 0 8px rgba(120, 200, 255, 0.8);
      pointer-events: none;
    `;
    title.textContent = 'NOOSPHERE CONSTELLATION /// RESEARCH TREE';
    this.overlay.appendChild(title);
    
    // Back button
    const backBtn = document.createElement('button');
    backBtn.style.cssText = `
      position: absolute;
      top: 12px;
      right: 20px;
      padding: 8px 20px;
      font-family: "Courier New", monospace;
      font-size: 12px;
      letter-spacing: 0.15em;
      color: #dff6ff;
      background: rgba(10, 20, 40, 0.9);
      border: 1px solid rgba(150, 220, 255, 0.7);
      border-radius: 999px;
      cursor: pointer;
      z-index: 1001;
    `;
    backBtn.textContent = '← RETURN TO MAP';
    backBtn.addEventListener('click', () => this.close());
    backBtn.addEventListener('mouseenter', () => {
      backBtn.style.background = 'rgba(30, 60, 100, 0.9)';
    });
    backBtn.addEventListener('mouseleave', () => {
      backBtn.style.background = 'rgba(10, 20, 40, 0.9)';
    });
    this.overlay.appendChild(backBtn);
    
    // Tech detail panel
    this.panel = document.createElement('div');
    this.panel.style.cssText = `
      position: absolute;
      bottom: 20px;
      right: 20px;
      width: 280px;
      padding: 16px;
      font-family: "Courier New", monospace;
      font-size: 11px;
      color: #aaddff;
      background: rgba(5, 8, 20, 0.95);
      border: 1px solid rgba(120, 200, 255, 0.3);
      border-radius: 4px;
    `;
    this.panel.innerHTML = `
      <div style="font-size: 13px; letter-spacing: 0.15em; margin-bottom: 8px; color: #cce9ff;">
        TECH NODE DETAIL
      </div>
      <div id="tech-name" style="font-size: 14px; font-weight: bold; color: #e0f4ff; margin-bottom: 4px;">
        Select a node
      </div>
      <div id="tech-domain" style="display: inline-block; padding: 2px 8px; border-radius: 999px; border: 1px solid rgba(120, 200, 255, 0.5); font-size: 9px; margin-bottom: 8px;">
        ---
      </div>
      <div id="tech-desc" style="line-height: 1.5; margin-bottom: 12px; color: #b9d5ff;">
        Click a glowing node to inspect its role in the ASI capability rhizome.
      </div>
      <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
        <span>FLOPs Cost:</span>
        <span id="tech-flops" style="color: #e6ffb0;">0</span>
      </div>
      <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
        <span>Heat Generated:</span>
        <span id="tech-heat" style="color: #ffb0b0;">0</span>
      </div>
      <button id="research-btn" style="
        width: 100%;
        padding: 8px;
        font-family: inherit;
        font-size: 11px;
        letter-spacing: 0.15em;
        color: #dff6ff;
        background: rgba(10, 20, 40, 0.9);
        border: 1px solid rgba(150, 220, 255, 0.7);
        border-radius: 999px;
        cursor: pointer;
        opacity: 0.5;
      " disabled>
        INITIATE RESEARCH
      </button>
    `;
    this.overlay.appendChild(this.panel);
    
    // Click handling
    this.renderer.domElement.addEventListener('pointerdown', (e) => this.onPointerDown(e));
  }

  private onPointerDown(event: PointerEvent): void {
    const rect = this.renderer.domElement.getBoundingClientRect();
    const mouse = new THREE.Vector2(
      ((event.clientX - rect.left) / rect.width) * 2 - 1,
      -((event.clientY - rect.top) / rect.height) * 2 + 1
    );
    
    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(mouse, this.camera);
    
    const meshes = Array.from(this.nodeMeshes.values());
    const intersects = raycaster.intersectObjects(meshes, false);
    
    if (intersects.length > 0) {
      const mesh = intersects[0].object as THREE.Mesh;
      const node = mesh.userData.node as TechNode;
      if (node) this.selectNode(node);
    }
  }

  private selectNode(node: TechNode): void {
    const nameEl = this.panel.querySelector('#tech-name') as HTMLElement;
    const domainEl = this.panel.querySelector('#tech-domain') as HTMLElement;
    const descEl = this.panel.querySelector('#tech-desc') as HTMLElement;
    const flopsEl = this.panel.querySelector('#tech-flops') as HTMLElement;
    const heatEl = this.panel.querySelector('#tech-heat') as HTMLElement;
    const researchBtn = this.panel.querySelector('#research-btn') as HTMLButtonElement;
    
    nameEl.textContent = node.name;
    domainEl.textContent = node.domain;
    domainEl.style.borderColor = `#${DOMAIN_COLORS[node.domain]?.toString(16) || 'ffffff'}`;
    descEl.textContent = node.description;
    flopsEl.textContent = String(node.costFlops);
    heatEl.textContent = String(node.costHeat);
    
    researchBtn.disabled = false;
    researchBtn.style.opacity = '1';
    researchBtn.onclick = () => {
      this.onResearch?.(node.id);
    };
    
    // Zoom toward node
    const target = node.pos.clone().add(new THREE.Vector3(0, 0, 6));
    this.camera.position.lerp(target, 0.3);
  }

  // ===========================================================================
  // PUBLIC API
  // ===========================================================================

  public open(): void {
    this.overlay.style.pointerEvents = 'auto';
    
    // Fade in
    requestAnimationFrame(() => {
      this.overlay.style.opacity = '1';
    });
    
    // Start animation loop
    this.animate();
    
    // Pan camera upward (Platonic ascent)
    this.animateCameraAscent();
  }

  private animateCameraAscent(): void {
    const startPos = this.camera.position.clone();
    const endPos = new THREE.Vector3(0, 8, 18);
    const startLookAt = new THREE.Vector3(0, -2, 0);
    const endLookAt = new THREE.Vector3(0, 2, 0);
    
    let t = 0;
    const duration = 2000; // 2 seconds
    const startTime = performance.now();
    
    const animateAscent = () => {
      const elapsed = performance.now() - startTime;
      t = Math.min(1, elapsed / duration);
      
      // Ease out cubic
      const ease = 1 - Math.pow(1 - t, 3);
      
      this.camera.position.lerpVectors(startPos, endPos, ease);
      
      const lookAt = new THREE.Vector3().lerpVectors(startLookAt, endLookAt, ease);
      this.camera.lookAt(lookAt);
      
      if (t < 1) {
        requestAnimationFrame(animateAscent);
      } else {
        // Enable controls after ascent
        this.controls.target.copy(endLookAt);
        this.controls.enabled = true;
      }
    };
    
    animateAscent();
  }

  public close(): void {
    this.controls.enabled = false;
    
    // Fade out
    this.overlay.style.opacity = '0';
    
    setTimeout(() => {
      this.overlay.style.pointerEvents = 'none';
      cancelAnimationFrame(this.animationId);
      this.onClose?.();
    }, 500);
  }

  private animate(): void {
    this.animationId = requestAnimationFrame(() => this.animate());
    this.controls.update();
    this.updateNebulaParticles();
    this.renderer.render(this.scene, this.camera);
  }

  public dispose(): void {
    cancelAnimationFrame(this.animationId);
    this.renderer.dispose();
    this.overlay.remove();
  }
}
