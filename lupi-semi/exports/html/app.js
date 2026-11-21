import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { HorizontalBlurShader } from 'three/addons/shaders/HorizontalBlurShader.js';
import { VerticalBlurShader } from 'three/addons/shaders/VerticalBlurShader.js';

const stage = document.getElementById('viewer-stage');
const canvas = document.getElementById('viewer-canvas');
const loaderEl = document.getElementById('viewer-loader');
const errorEl = document.getElementById('viewer-error');
const switchBtns = document.querySelectorAll('.switch-btn');

// Offset exato (em coordenadas glTF Y-up) para encaixar a PCB dentro do case
// alinhando portas SNES na frente e DB15/módulos nos recortes traseiros
const PCB_IN_CASE_OFFSET = new THREE.Vector3(-88.14, -8.06, -4.65);

// Renderer
const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: true,
  alpha: true,
  powerPreference: 'high-performance',
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.82;

// Scene & Studio Softbox Environment (Ultra)
const scene = new THREE.Scene();
const pmremGenerator = new THREE.PMREMGenerator(renderer);

function createSoftboxEnvironment() {
  const envScene = new THREE.Scene();
  envScene.background = new THREE.Color(0x2a2e35);

  const boxGeo = new THREE.PlaneGeometry(1, 1);
  const addSoftbox = (color, intensity, pos, lookAt, scale) => {
    const mat = new THREE.MeshBasicMaterial({
      color: new THREE.Color(color).multiplyScalar(intensity),
      side: THREE.DoubleSide,
    });
    const mesh = new THREE.Mesh(boxGeo, mat);
    mesh.position.set(...pos);
    mesh.scale.set(...scale);
    mesh.lookAt(...lookAt);
    envScene.add(mesh);
  };

  addSoftbox(0xfff9f0, 3.2, [6, 12, 8], [0, 0, 0], [14, 14, 1]);
  addSoftbox(0xdbe8ff, 1.6, [-12, 4, 2], [0, 0, 0], [12, 10, 1]);
  addSoftbox(0xffffff, 2.2, [0, 8, -12], [0, 0, 0], [16, 8, 1]);
  addSoftbox(0x9aa2ad, 1.35, [0, -10, 0], [0, 0, 0], [20, 20, 1]);

  return pmremGenerator.fromScene(envScene, 0.06).texture;
}

scene.environment = createSoftboxEnvironment();
scene.environmentIntensity = 0.46;

// Textura procedural sutil de micro-granulação de PLA Mate
function createPLAMicroTexture() {
  const size = 256;
  const texCanvas = document.createElement('canvas');
  texCanvas.width = size;
  texCanvas.height = size;
  const ctx = texCanvas.getContext('2d');
  const imgData = ctx.createImageData(size, size);
  const data = imgData.data;

  let seed = 1337;
  const rand = () => {
    seed = (seed * 16807) % 2147483647;
    return (seed - 1) / 2147483646;
  };

  for (let y = 0; y < size; y++) {
    const layerWave = Math.sin((y / size) * Math.PI * 64) * 14;
    for (let x = 0; x < size; x++) {
      const grain = (rand() - 0.5) * 36;
      const v = Math.max(0, Math.min(255, Math.round(128 + layerWave + grain)));
      const idx = (y * size + x) * 4;
      data[idx] = v;
      data[idx + 1] = v;
      data[idx + 2] = v;
      data[idx + 3] = 255;
    }
  }
  ctx.putImageData(imgData, 0, 0);

  const tex = new THREE.CanvasTexture(texCanvas);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(18, 18);
  return tex;
}

const plaMicroTexture = createPLAMicroTexture();

// Camera & Controls (near=10 aumenta drasticamente a precisão do depth buffer e elimina z-fighting)
const camera = new THREE.PerspectiveCamera(34, 4 / 3, 10, 800);
camera.position.set(135, 105, 180);

const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.enableZoom = false;
controls.enablePan = false;
controls.autoRotate = false;
controls.minPolarAngle = Math.PI * 0.16;
controls.maxPolarAngle = Math.PI * 0.78;
controls.target.set(0, 0, 0);

// Iluminação de estúdio (Ultra)
const hemiLight = new THREE.HemisphereLight(0xffffff, 0x6b727d, 0.32);
hemiLight.position.set(0, 120, 0);
scene.add(hemiLight);

const keyLight = new THREE.DirectionalLight(0xfffbf2, 1.12);
keyLight.position.set(95, 165, 110);
keyLight.castShadow = true;
keyLight.shadow.mapSize.set(2048, 2048);
keyLight.shadow.camera.near = 100;
keyLight.shadow.camera.far = 320;
const d = 95;
keyLight.shadow.camera.left = -d;
keyLight.shadow.camera.right = d;
keyLight.shadow.camera.top = d;
keyLight.shadow.camera.bottom = -d;
keyLight.shadow.bias = -0.0006;
keyLight.shadow.normalBias = 0.08;
keyLight.shadow.radius = 2.5;
scene.add(keyLight);

const fillLight = new THREE.DirectionalLight(0xdce6f5, 0.24);
fillLight.position.set(-140, 50, -80);
scene.add(fillLight);

const rimLight = new THREE.DirectionalLight(0xffffff, 0.28);
rimLight.position.set(-20, 90, -160);
scene.add(rimLight);

// Contact Shadow difusa de estúdio
const CONTACT_PLANE_W = 240;
const CONTACT_PLANE_H = 220;
const CONTACT_CAM_HEIGHT = 48;

const contactShadowGroup = new THREE.Group();
contactShadowGroup.position.y = -20;
scene.add(contactShadowGroup);

const rtContact = new THREE.WebGLRenderTarget(256, 256);
rtContact.texture.generateMipmaps = false;
const rtContactBlur = new THREE.WebGLRenderTarget(256, 256);
rtContactBlur.texture.generateMipmaps = false;

const contactPlaneGeo = new THREE.PlaneGeometry(CONTACT_PLANE_W, CONTACT_PLANE_H).rotateX(Math.PI / 2);
const contactShadowPlane = new THREE.Mesh(
  contactPlaneGeo,
  new THREE.MeshBasicMaterial({
    map: rtContact.texture,
    opacity: 0.58,
    transparent: true,
    depthWrite: false,
  })
);
contactShadowPlane.scale.y = -1;
contactShadowGroup.add(contactShadowPlane);

const blurPlane = new THREE.Mesh(contactPlaneGeo);
blurPlane.visible = false;
contactShadowGroup.add(blurPlane);

const contactCamera = new THREE.OrthographicCamera(
  -CONTACT_PLANE_W / 2,
  CONTACT_PLANE_W / 2,
  CONTACT_PLANE_H / 2,
  -CONTACT_PLANE_H / 2,
  0,
  CONTACT_CAM_HEIGHT
);
contactCamera.rotation.x = Math.PI / 2;
contactShadowGroup.add(contactCamera);

const contactDepthMaterial = new THREE.MeshDepthMaterial();
contactDepthMaterial.onBeforeCompile = (shader) => {
  shader.fragmentShader = shader.fragmentShader.replace(
    'gl_FragColor = vec4( vec3( 1.0 - fragCoordZ ), opacity );',
    'gl_FragColor = vec4( vec3( 0.07, 0.08, 0.10 ), ( 1.0 - pow( fragCoordZ, 1.35 ) ) * 0.92 );'
  );
};
contactDepthMaterial.depthTest = false;
contactDepthMaterial.depthWrite = false;

const hBlurMat = new THREE.ShaderMaterial(HorizontalBlurShader);
hBlurMat.depthTest = false;
const vBlurMat = new THREE.ShaderMaterial(VerticalBlurShader);
vBlurMat.depthTest = false;

function blurContactShadow(amount) {
  blurPlane.visible = true;

  blurPlane.material = hBlurMat;
  blurPlane.material.uniforms.tDiffuse.value = rtContact.texture;
  hBlurMat.uniforms.h.value = amount / 256;
  renderer.setRenderTarget(rtContactBlur);
  renderer.render(blurPlane, contactCamera);

  blurPlane.material = vBlurMat;
  blurPlane.material.uniforms.tDiffuse.value = rtContactBlur.texture;
  vBlurMat.uniforms.v.value = amount / 256;
  renderer.setRenderTarget(rtContact);
  renderer.render(blurPlane, contactCamera);

  blurPlane.visible = false;
}

function updateContactShadow() {
  const prevBackground = scene.background;
  const prevOverride = scene.overrideMaterial;
  const prevClearAlpha = renderer.getClearAlpha();
  const prevShadowEnabled = renderer.shadowMap.enabled;

  scene.background = null;
  scene.overrideMaterial = contactDepthMaterial;
  renderer.shadowMap.enabled = false;
  contactShadowPlane.visible = false;

  renderer.setClearAlpha(0);
  renderer.setRenderTarget(rtContact);
  renderer.clear();
  renderer.render(scene, contactCamera);

  scene.overrideMaterial = null;
  blurContactShadow(5.5);
  blurContactShadow(3.0);

  renderer.setRenderTarget(null);
  renderer.setClearAlpha(prevClearAlpha);
  renderer.shadowMap.enabled = prevShadowEnabled;
  scene.background = prevBackground;
  scene.overrideMaterial = prevOverride;
  contactShadowPlane.visible = true;
}

// Grupo principal do modelo
const consoleGroup = new THREE.Group();
scene.add(consoleGroup);

function resizeRenderer() {
  const { clientWidth, clientHeight } = stage;
  if (!clientWidth || !clientHeight) return;
  camera.aspect = clientWidth / clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(clientWidth, clientHeight, false);
}

const resizeObserver = new ResizeObserver(resizeRenderer);
resizeObserver.observe(stage);
resizeRenderer();

// Converte materiais para MeshPhysicalMaterial (PLA Mate no Case, acabamento de placa/solda na PCB)
function upgradeMaterial(stdMat, modelKey) {
  if (modelKey === 'pcb') {
    const isSolderMask =
      stdMat.name === 'pcb_solder_mask' ||
      stdMat.name === 'pcb_bottom_tex' ||
      stdMat.name === 'pico_green' ||
      stdMat.name === 'esp_black_pcb' ||
      stdMat.name === 'daughter_cyan';
    return new THREE.MeshPhysicalMaterial({
      name: stdMat.name,
      color: stdMat.map ? new THREE.Color(0xffffff) : stdMat.color.clone(),
      map: stdMat.map || null,
      roughness: stdMat.roughness,
      metalness: stdMat.metalness,
      aoMap: stdMat.aoMap,
      aoMapIntensity: 0.9,
      clearcoat: isSolderMask ? 0.35 : 0.05,
      clearcoatRoughness: 0.28,
    });
  }

  const phys = new THREE.MeshPhysicalMaterial({
    name: stdMat.name,
    color: stdMat.color.clone(),
    roughness: stdMat.roughness,
    metalness: stdMat.metalness,
    aoMap: stdMat.aoMap,
    aoMapIntensity: 0.92,
    bumpMap: plaMicroTexture,
    bumpScale: 0.09,
    sheen: 0.32,
    sheenRoughness: 0.82,
    sheenColor: new THREE.Color(0xffffff),
  });
  if (phys.name === 'mat_primary' || phys.name === 'mat_screw') phys.color.set('#f4f1ea');
  if (phys.name === 'mat_accent') phys.color.set('#ff6b1a');
  return phys;
}

function prepareScene(root, modelKey, hideCasePorts = false) {
  const upgradedMap = new Map();
  root.traverse((child) => {
    if (hideCasePorts && child.name === 'snes_ports') {
      child.visible = false;
      return;
    }
    if (child.isMesh) {
      child.castShadow = true;
      child.receiveShadow = true;

      const convertMat = (m) => {
        if (!m) return m;
        if (!upgradedMap.has(m)) {
          upgradedMap.set(m, upgradeMaterial(m, modelKey));
        }
        return upgradedMap.get(m);
      };

      if (Array.isArray(child.material)) {
        child.material = child.material.map(convertMat);
      } else {
        child.material = convertMat(child.material);
      }
    }
  });
  return root;
}

const gltfLoader = new GLTFLoader();
const loadGLB = (url) =>
  new Promise((resolve, reject) => {
    gltfLoader.load(url, resolve, undefined, reject);
  });

let cachedCaseRoot = null;
let cachedPcbRoot = null;

function showModel(modelKey) {
  if (!cachedCaseRoot || !cachedPcbRoot) return;

  consoleGroup.clear();
  const orientationGroup = new THREE.Group();
  orientationGroup.rotation.y = Math.PI;

  if (modelKey === 'case') {
    cachedCaseRoot.position.set(0, 0, 0);
    cachedPcbRoot.position.copy(PCB_IN_CASE_OFFSET);
    orientationGroup.add(cachedCaseRoot, cachedPcbRoot);
  } else {
    cachedPcbRoot.position.set(0, 0, 0);
    orientationGroup.add(cachedPcbRoot);
  }

  // Centraliza o conjunto ativo na origem
  orientationGroup.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(orientationGroup);
  const center = box.getCenter(new THREE.Vector3());
  orientationGroup.position.sub(center);

  const size = box.getSize(new THREE.Vector3());
  contactShadowGroup.position.y = -size.y / 2 - 2;

  consoleGroup.add(orientationGroup);
  updateContactShadow();
}

// Carrega Case e PCB em paralelo uma única vez (troca instantânea entre abas)
Promise.all([
  loadGLB('./lupi-high.glb'),
  loadGLB('./lupi-pcb.glb'),
])
  .then(([caseGltf, pcbGltf]) => {
    cachedCaseRoot = prepareScene(caseGltf.scene, 'case', true);
    cachedPcbRoot = prepareScene(pcbGltf.scene, 'pcb', false);
    showModel('case');
    loaderEl.hidden = true;
  })
  .catch((err) => {
    console.error('Erro ao carregar GLB:', err);
    loaderEl.hidden = true;
    errorEl.hidden = false;
  });

switchBtns.forEach((btn) => {
  btn.addEventListener('click', () => {
    const modelKey = btn.dataset.model;
    switchBtns.forEach((b) => b.classList.toggle('is-active', b === btn));
    showModel(modelKey);
  });
});

function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}

animate();
