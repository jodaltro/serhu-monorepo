/**
 * Three.js scene setup — camera, renderer, lights, starfield cosmos.
 *
 * Provides a dark cosmic backdrop with subtle stars that the Being
 * floats in front of. The camera is positioned to frame the Being
 * comfortably in the viewport center.
 */

import * as THREE from "three";

/**
 * Initialize the Three.js scene, camera, renderer and background.
 *
 * @param {HTMLElement} container  DOM element to attach the canvas to.
 * @returns {{ scene: THREE.Scene, camera: THREE.PerspectiveCamera, renderer: THREE.WebGLRenderer }}
 */
export function initScene(container) {
  // -- Scene ---------------------------------------------------------------
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x050510);
  scene.fog = new THREE.FogExp2(0x050510, 0.04);

  // -- Camera --------------------------------------------------------------
  const camera = new THREE.PerspectiveCamera(
    60,
    container.clientWidth / container.clientHeight,
    0.1,
    1000,
  );
  camera.position.set(0, 0, 5);
  camera.lookAt(0, 0, 0);

  // -- Renderer ------------------------------------------------------------
  const renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: false,
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.2;
  container.appendChild(renderer.domElement);

  // -- Lights --------------------------------------------------------------
  const ambient = new THREE.AmbientLight(0x333355, 0.6);
  scene.add(ambient);

  const keyLight = new THREE.DirectionalLight(0xffffff, 1.0);
  keyLight.position.set(3, 4, 5);
  scene.add(keyLight);

  const fillLight = new THREE.DirectionalLight(0x8888ff, 0.3);
  fillLight.position.set(-2, -1, 3);
  scene.add(fillLight);

  // -- Starfield -----------------------------------------------------------
  createStarfield(scene);

  // -- Resize handling -----------------------------------------------------
  const onResize = () => {
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
  };
  window.addEventListener("resize", onResize);

  return { scene, camera, renderer };
}

/**
 * Create a starfield particle system for the cosmos background.
 * @param {THREE.Scene} scene
 */
function createStarfield(scene) {
  const COUNT = 1500;
  const positions = new Float32Array(COUNT * 3);
  const sizes = new Float32Array(COUNT);

  for (let i = 0; i < COUNT; i++) {
    positions[i * 3] = (Math.random() - 0.5) * 100;
    positions[i * 3 + 1] = (Math.random() - 0.5) * 100;
    positions[i * 3 + 2] = (Math.random() - 0.5) * 100;
    sizes[i] = Math.random() * 1.5 + 0.5;
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("size", new THREE.BufferAttribute(sizes, 1));

  const material = new THREE.PointsMaterial({
    color: 0xffffff,
    size: 0.08,
    sizeAttenuation: true,
    transparent: true,
    opacity: 0.6,
  });

  const stars = new THREE.Points(geometry, material);
  scene.add(stars);
}
