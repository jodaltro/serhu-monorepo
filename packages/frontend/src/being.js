/**
 * Being 3D mesh — morphogenesis-driven geometry, material, and animation.
 *
 * The Being starts as a small white glowing point (sensorimotor stage) and
 * evolves its shape, color, and movement as its personality develops.
 *
 * Geometry follows the Kiki/Bouba principle:
 *   - High agreeableness → round, bulbous (Bouba)
 *   - Low agreeableness  → angular, spiky  (Kiki)
 *
 * Color is HSL-driven from personality traits.
 * Animation reflects temperament (pulse, drift, glow).
 *
 * References:
 *   - Kiki/Bouba effect: https://en.wikipedia.org/wiki/Bouba/kiki_effect
 *   - Shape psychology:  https://uxdesign.cc/the-psychology-behind-shapes-and-colors-17dd93ce08a2
 */

import * as THREE from "three";

/** Default visual state (tabula rasa / sensorimotor newborn). */
const DEFAULTS = {
  hue: 0,
  saturation: 0,
  lightness: 1,
  alpha: 0.3,
  roundness: 0.5,
  complexity: 0,
  symmetry: 0.5,
  scale: 0.1,
  spikiness: 0,
  organic_noise: 0,
  pulse_rate: 1,
  movement_speed: 0,
  center_attraction: 0.5,
  glow_intensity: 0.5,
  roughness: 0.5,
  cognitive_stage: "sensorimotor",
  cognitive_age: 0,
};

/**
 * Create the Being object and return update/animate handles.
 *
 * @param {THREE.Scene} scene
 * @returns {{ update: (vs: object) => void, animate: (time: number) => void, mesh: THREE.Mesh }}
 */
export function createBeing(scene) {
  let state = { ...DEFAULTS };

  // -- Base geometry (icosahedron, subdivided for smooth deformation) -------
  const detail = 4; // ~2560 faces — enough for smooth organic shapes
  const baseGeo = new THREE.IcosahedronGeometry(1, detail);

  // Clone positions for reference (original sphere)
  const origPositions = Float32Array.from(baseGeo.attributes.position.array);

  // -- Material (PBR physical with emissive glow) --------------------------
  const material = new THREE.MeshPhysicalMaterial({
    color: new THREE.Color().setHSL(0, 0, 1),
    emissive: new THREE.Color().setHSL(0, 0, 1),
    emissiveIntensity: 0.8,
    roughness: 0.5,
    metalness: 0.1,
    clearcoat: 0.3,
    clearcoatRoughness: 0.4,
    transparent: true,
    opacity: 0.3,
  });

  const mesh = new THREE.Mesh(baseGeo, material);
  mesh.scale.setScalar(0.1); // start tiny (tabula rasa)
  scene.add(mesh);

  // -- Deform geometry based on visual state parameters --------------------

  /**
   * Apply Kiki/Bouba vertex displacement to the sphere.
   * High roundness → stays spherical. High spikiness → pointed vertex extrusion.
   * Organic noise adds simplex-like undulation (approximated with sin waves).
   */
  function deformGeometry() {
    const pos = baseGeo.attributes.position;
    const count = pos.count;
    const { roundness, spikiness, organic_noise, complexity } = state;

    for (let i = 0; i < count; i++) {
      const ox = origPositions[i * 3];
      const oy = origPositions[i * 3 + 1];
      const oz = origPositions[i * 3 + 2];

      // Normalized direction from center
      const len = Math.sqrt(ox * ox + oy * oy + oz * oz) || 1;
      const nx = ox / len;
      const ny = oy / len;
      const nz = oz / len;

      // Spherical coordinates for noise sampling
      const theta = Math.atan2(ny, nx);
      const phi = Math.acos(nz / len);

      // Spike displacement: sharper extrusion at certain vertices
      // Use a mix of harmonics for organic spikiness
      const spikeFreq = 3 + complexity * 8;
      const spike =
        spikiness *
        0.3 *
        Math.max(
          0,
          Math.sin(theta * spikeFreq) * Math.cos(phi * spikeFreq * 0.7),
        );

      // Organic noise: multi-octave sin-based approximation
      const noiseVal =
        organic_noise *
        0.15 *
        (Math.sin(theta * 5.0 + phi * 3.0) * 0.5 +
          Math.sin(theta * 11.0 - phi * 7.0) * 0.3 +
          Math.sin(theta * 17.0 + phi * 13.0) * 0.2);

      // Roundness damps displacements (1 = perfect sphere, 0 = full deformation)
      const dampFactor = 1 - roundness * 0.8;

      const displacement = (spike + noiseVal) * dampFactor;

      pos.setXYZ(
        i,
        ox + nx * displacement,
        oy + ny * displacement,
        oz + nz * displacement,
      );
    }

    pos.needsUpdate = true;
    baseGeo.computeVertexNormals();
  }

  // -- Update visual state from API data -----------------------------------

  /**
   * Update the Being's visual representation from a VisualState object.
   * @param {object} vs  VisualState from API (or partial update)
   */
  function update(vs) {
    state = { ...state, ...vs };

    // Scale (size grows with development)
    const targetScale = Math.max(0.05, state.scale * 2.0);
    mesh.scale.setScalar(targetScale);

    // Color: HSL → Three.js Color
    const hue = state.hue / 360;
    const sat = state.saturation;
    const light = state.lightness;

    material.color.setHSL(hue, sat, light);

    // Emissive color (same hue, boosted for glow effect)
    material.emissive.setHSL(hue, sat, Math.min(light * 1.2, 1.0));
    material.emissiveIntensity = state.glow_intensity * 1.5;

    // Opacity (newborns are translucent)
    material.opacity = state.alpha;

    // PBR surface properties
    material.roughness = state.roughness;
    material.metalness = (1 - state.roughness) * 0.3;
    material.clearcoat = state.glow_intensity * 0.5;

    // Deform geometry
    deformGeometry();
  }

  // -- Animation loop (called every frame) ---------------------------------

  /**
   * Per-frame animation: pulse breathing, drift movement, rotation.
   * @param {number} time  Elapsed time in seconds.
   */
  function animate(time) {
    // Pulse breathing: scale oscillation
    const pulseAmplitude = 0.03 + state.glow_intensity * 0.05;
    const pulsePhase = Math.sin(time * state.pulse_rate * Math.PI * 2);
    const baseScale = Math.max(0.05, state.scale * 2.0);
    const breathScale = baseScale + pulsePhase * pulseAmplitude * baseScale;
    mesh.scale.setScalar(breathScale);

    // Emissive glow oscillation
    const glowOsc = 0.8 + pulsePhase * 0.2;
    material.emissiveIntensity = state.glow_intensity * 1.5 * glowOsc;

    // Drift movement (novelty seeking → explores, harm avoidance → stays centered)
    const driftRadius = state.movement_speed * 1.5;
    const attraction = state.center_attraction;
    const driftSpeed = 0.1 + state.movement_speed * 0.4;

    // Lissajous-like path for organic movement
    const targetX = driftRadius * Math.sin(time * driftSpeed * 1.3);
    const targetY = driftRadius * Math.cos(time * driftSpeed * 0.9) * 0.6;

    // Attract toward center
    mesh.position.x += (targetX - mesh.position.x) * (0.02 + attraction * 0.05);
    mesh.position.y += (targetY - mesh.position.y) * (0.02 + attraction * 0.05);

    // Gentle rotation
    mesh.rotation.y += 0.002 + state.movement_speed * 0.003;
    mesh.rotation.x += 0.001;
  }

  // Initial deform
  deformGeometry();

  return { update, animate, mesh };
}
