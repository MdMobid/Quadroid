/**
 * QUADROID 3.0 // 3D HOLOGRAPHIC CYBER COMMAND CENTER
 * Three.js WebGL Particle Core + WebSocket Client + Audio-Reactive State Engine
 */

let ws = null;
let currentAiState = 'idle'; // idle, listening, thinking, speaking
let isRecognizing = false;
let isAssistantSpeaking = false;
let recognition = null;
let continuousMicEnabled = false;

// ── DOM References ──
const threeContainer = document.getElementById('threejs-canvas-container');
const chatStream = document.getElementById('chatStream');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const micBtn = document.getElementById('micBtn');
const autoMicToggleBtn = document.getElementById('autoMicToggleBtn');
const toolActionBar = document.getElementById('toolActionBar');
const activeToolName = document.getElementById('activeToolName');
const aiStateBadge = document.getElementById('aiStateBadge');
const aiStateText = document.getElementById('aiStateText');
const assistantTitle = document.getElementById('assistantTitle');
const welcomeSender = document.getElementById('welcomeSender');
const wakeWordTag = document.getElementById('wakeWordTag');
const providerName = document.getElementById('providerName');
const cpuVal = document.getElementById('cpuVal');
const cpuBar = document.getElementById('cpuBar');
const ramVal = document.getElementById('ramVal');
const ramBar = document.getElementById('ramBar');
const batVal = document.getElementById('batVal');
const batIcon = document.getElementById('batIcon');
const statusPill = document.getElementById('statusPill');
const clockDisplay = document.getElementById('clockDisplay');
const memCountLabel = document.getElementById('memCountLabel');
const footerUptime = document.getElementById('footerUptime');
const footerEndpoint = document.getElementById('footerEndpoint');

// Modals
const confirmModal = document.getElementById('confirmModal');
const modalTitle = document.getElementById('modalTitle');
const modalMessage = document.getElementById('modalMessage');
const modalAllowBtn = document.getElementById('modalAllowBtn');
const modalDenyBtn = document.getElementById('modalDenyBtn');
const memoryModal = document.getElementById('memoryModal');
const memCardBtn = document.getElementById('memCardBtn');
const closeMemModal = document.getElementById('closeMemModal');

let currentConfirmId = null;
const sessionStartTime = Date.now();

// ============================================================================
// 1. THREE.JS 3D HOLOGRAPHIC AI CORE
// ============================================================================

let scene, camera, renderer, particleSphere, particleGeometry, particleMaterial;
let outerRing, ringGeometry, ringMaterial;
let targetColor = new THREE.Color(0x00f2fe);
let mouseX = 0, mouseY = 0;

function initThreeJS() {
  const width = threeContainer.clientWidth || 340;
  const height = threeContainer.clientHeight || 340;

  // Scene & Camera
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
  camera.position.z = 240;

  // Renderer
  renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  threeContainer.appendChild(renderer.domElement);

  // 1. 3D Particle Sphere (AI Core)
  const particleCount = 1800;
  particleGeometry = new THREE.BufferGeometry();
  const positions = new Float32Array(particleCount * 3);
  const originalPositions = new Float32Array(particleCount * 3);
  const radius = 64;

  for (let i = 0; i < particleCount; i++) {
    const theta = Math.acos(2 * Math.random() - 1);
    const phi = 2 * Math.PI * Math.random();

    const x = radius * Math.sin(theta) * Math.cos(phi);
    const y = radius * Math.sin(theta) * Math.sin(phi);
    const z = radius * Math.cos(theta);

    positions[i * 3] = x;
    positions[i * 3 + 1] = y;
    positions[i * 3 + 2] = z;

    originalPositions[i * 3] = x;
    originalPositions[i * 3 + 1] = y;
    originalPositions[i * 3 + 2] = z;
  }

  particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  particleGeometry.setAttribute('origPos', new THREE.BufferAttribute(originalPositions, 3));

  particleMaterial = new THREE.PointsMaterial({
    color: 0x00f2fe,
    size: 2.2,
    transparent: true,
    opacity: 0.85,
    blending: THREE.AdditiveBlending
  });

  particleSphere = new THREE.Points(particleGeometry, particleMaterial);
  scene.add(particleSphere);

  // 2. Orbital Hologram Ring
  const ringRadius = 88;
  const ringSegments = 120;
  const ringPos = new Float32Array(ringSegments * 3);
  for (let i = 0; i < ringSegments; i++) {
    const angle = (i / ringSegments) * Math.PI * 2;
    ringPos[i * 3] = ringRadius * Math.cos(angle);
    ringPos[i * 3 + 1] = 0;
    ringPos[i * 3 + 2] = ringRadius * Math.sin(angle);
  }
  ringGeometry = new THREE.BufferGeometry();
  ringGeometry.setAttribute('position', new THREE.BufferAttribute(ringPos, 3));
  ringMaterial = new THREE.LineBasicMaterial({
    color: 0x00f2fe,
    transparent: true,
    opacity: 0.4,
    linewidth: 1
  });
  outerRing = new THREE.LineLoop(ringGeometry, ringMaterial);
  outerRing.rotation.x = Math.PI / 4;
  scene.add(outerRing);

  // Mouse Interaction
  window.addEventListener('mousemove', (e) => {
    mouseX = (e.clientX - window.innerWidth / 2) * 0.0005;
    mouseY = (e.clientY - window.innerHeight / 2) * 0.0005;
  });

  window.addEventListener('resize', onWindowResize);
  animateThreeJS();
}

function onWindowResize() {
  if (!threeContainer || !camera || !renderer) return;
  const width = threeContainer.clientWidth;
  const height = threeContainer.clientHeight;
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);
}

let clock = new THREE.Clock();

function animateThreeJS() {
  requestAnimationFrame(animateThreeJS);

  const elapsedTime = clock.getElapsedTime();
  const positions = particleGeometry.attributes.position.array;
  const origPos = particleGeometry.attributes.origPos.array;

  // State-based animation parameters
  let waveSpeed = 2.0;
  let waveAmp = 4.0;
  let rotSpeed = 0.006;

  if (currentAiState === 'listening') {
    waveSpeed = 4.5;
    waveAmp = 12.0;
    targetColor.setHex(0xf43f5e); // Neon Red
  } else if (currentAiState === 'thinking') {
    waveSpeed = 6.0;
    waveAmp = 8.0;
    rotSpeed = 0.025;
    targetColor.setHex(0x9d4edd); // Purple
  } else if (currentAiState === 'speaking') {
    waveSpeed = 3.5;
    waveAmp = 9.0;
    targetColor.setHex(0x10b981); // Emerald
  } else {
    targetColor.setHex(0x00f2fe); // Cyan
  }

  // Smooth color morphing
  particleMaterial.color.lerp(targetColor, 0.08);
  ringMaterial.color.lerp(targetColor, 0.08);

  // Particle deformation wave
  for (let i = 0; i < positions.length; i += 3) {
    const ox = origPos[i];
    const oy = origPos[i + 1];
    const oz = origPos[i + 2];

    const dist = Math.sqrt(ox * ox + oy * oy + oz * oz);
    const offset = Math.sin(dist * 0.08 - elapsedTime * waveSpeed) * waveAmp;

    positions[i] = ox + (ox / dist) * offset;
    positions[i + 1] = oy + (oy / dist) * offset;
    positions[i + 2] = oz + (oz / dist) * offset;
  }
  particleGeometry.attributes.position.needsUpdate = true;

  // Rotation
  particleSphere.rotation.y += rotSpeed + mouseX;
  particleSphere.rotation.x += mouseY * 0.5;

  outerRing.rotation.z += 0.004;
  outerRing.rotation.y += 0.006;

  renderer.render(scene, camera);
}

// ============================================================================
// 2. WEBSOCKET CLIENT & REAL-TIME LINK
// ============================================================================

function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log('[WS] Connected to Quadroid Core');
    footerEndpoint.textContent = 'WS: LINKED';
    footerEndpoint.style.color = 'var(--neon-emerald)';
  };

  ws.onmessage = (event) => {
    try {
      const data = jsonParseSafe(event.data);
      handleIncomingMessage(data);
    } catch (e) {
      console.error('[WS] Parse error:', e);
    }
  };

  ws.onclose = () => {
    console.log('[WS] Disconnected. Reconnecting in 2s...');
    footerEndpoint.textContent = 'WS: RECONNECTING';
    footerEndpoint.style.color = 'var(--neon-rose)';
    setTimeout(connectWebSocket, 2000);
  };

  ws.onerror = (err) => {
    console.error('[WS] Error:', err);
  };
}

function handleIncomingMessage(data) {
  const type = data.type;

  if (type === 'handshake') {
    assistantTitle.textContent = (data.assistant_name || 'QUADROID').toUpperCase();
    welcomeSender.textContent = `◆ ${(data.assistant_name || 'QUADROID').toUpperCase()}`;
    wakeWordTag.textContent = `"Hey ${data.assistant_name || 'Quadroid'}"`;
    providerName.textContent = `${(data.provider || 'NEMOTRON').toUpperCase()} 30B`;
    if (data.is_offline) {
      statusPill.className = 'status-pill offline';
    }
  } else if (type === 'telemetry') {
    updateTelemetry(data);
  } else if (type === 'state') {
    setAiState(data.state);
    if (data.state === 'speaking') {
      isAssistantSpeaking = true;
      if (recognition && isRecognizing) {
        try { recognition.abort(); } catch (e) {}
        isRecognizing = false;
      }
      currentTranscriptBuffer = "";
      userInput.value = "";
      if (speechDebounceTimer) clearTimeout(speechDebounceTimer);
    } else if (data.state === 'idle') {
      isAssistantSpeaking = false;
      // Re-enable mic ONLY after assistant finished speaking and safety cooldown passed
      if (continuousMicEnabled) {
        setTimeout(() => {
          if (!isAssistantSpeaking && currentAiState === 'idle') {
            triggerVoiceRecognition();
          }
        }, 500);
      }
    }
  } else if (type === 'wake_detected') {
    if (!isAssistantSpeaking && currentAiState === 'idle') {
      console.log('[WAKE] Wake-word detected! Activating mic...');
      triggerVoiceRecognition();
    }
  } else if (type === 'tool_action') {
    showToolAction(data.tool, data.args);
    appendActionChipToFeed(data.tool, data.args);
  } else if (type === 'assistant_response') {
    hideToolAction();
    appendMessage(data.text, false);
  } else if (type === 'confirmation_request') {
    showConfirmModal(data.id, data.title, data.message);
  }
}

// ============================================================================
// 3. UI STATE & FEED UPDATES
// ============================================================================

function setAiState(state) {
  currentAiState = state;
  aiStateBadge.className = `state-badge ${state}`;

  if (state === 'listening') {
    aiStateText.textContent = 'LISTENING...';
    micBtn.classList.add('active');
  } else if (state === 'thinking') {
    aiStateText.textContent = 'NEURAL COMPUTING...';
    micBtn.classList.remove('active');
  } else if (state === 'speaking') {
    aiStateText.textContent = 'VOICE ACTIVE...';
    micBtn.classList.remove('active');
  } else {
    aiStateText.textContent = 'AI CORE READY';
    micBtn.classList.remove('active');
  }
}

function updateTelemetry(data) {
  // CPU
  cpuVal.textContent = `${data.cpu}%`;
  cpuBar.style.width = `${Math.min(data.cpu, 100)}%`;

  // RAM
  ramVal.textContent = `${data.ram}%`;
  ramBar.style.width = `${Math.min(data.ram, 100)}%`;

  // Battery
  batVal.textContent = `${data.battery}%`;
  if (data.power_plugged) {
    batIcon.className = 'fa-solid fa-bolt';
    batIcon.style.color = 'var(--neon-emerald)';
  } else {
    batIcon.className = 'fa-solid fa-battery-half';
    batIcon.style.color = 'var(--neon-cyan)';
  }

  // Memory
  if (data.memory_entries !== undefined) {
    memCountLabel.textContent = `${data.memory_entries} Entries Stored`;
  }
}

function appendMessage(text, isUser = false) {
  const bubble = document.createElement('div');
  bubble.className = `msg-bubble ${isUser ? 'user-bubble' : 'assistant-bubble'}`;

  const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const sender = isUser ? 'OPERATOR' : (assistantTitle.textContent || 'QUADROID');

  bubble.innerHTML = `
    <div class="bubble-meta">
      <span class="sender-tag">${isUser ? '👤' : '◆'} ${sender}</span>
      <span class="time-tag">${timeStr}</span>
    </div>
    <div class="bubble-text">${formatMarkdown(text)}</div>
  `;

  chatStream.appendChild(bubble);
  chatStream.scrollTop = chatStream.scrollHeight;
}

function showToolAction(tool, args) {
  const argsStr = Object.entries(args || {}).map(([k, v]) => `${k}=${v}`).join(', ');
  activeToolName.textContent = `EXECUTING: ${tool}(${argsStr})`;
  toolActionBar.style.display = 'flex';
}

function hideToolAction() {
  toolActionBar.style.display = 'none';
}

function appendActionChipToFeed(tool, args) {
  const argsStr = Object.entries(args || {}).map(([k, v]) => `${k}=${v}`).join(', ');
  const chip = document.createElement('div');
  chip.className = 'action-chip-card';
  chip.innerHTML = `<i class="fa-solid fa-gear fa-spin"></i> <span>⚙️ ${tool}(${argsStr})</span>`;
  chatStream.appendChild(chip);
  chatStream.scrollTop = chatStream.scrollHeight;
}

function formatMarkdown(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>');
}

function jsonParseSafe(str) {
  try { return JSON.parse(str); } catch { return {}; }
}

// ============================================================================
// 4. USER ACTIONS & VOICE SPEECH RECOGNITION
// ============================================================================

function sendMessage(text) {
  if (!text.trim() || !ws || ws.readyState !== WebSocket.OPEN) return;
  appendMessage(text, true);
  ws.send(JSON.stringify({ type: 'user_message', text: text.trim() }));
  userInput.value = '';
}

sendBtn.addEventListener('click', () => {
  sendMessage(userInput.value);
});

userInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    sendMessage(userInput.value);
  }
});

// Quick action pills
document.querySelectorAll('.quick-pill').forEach((pill) => {
  pill.addEventListener('click', () => {
    const cmd = pill.getAttribute('data-cmd');
    if (cmd) sendMessage(cmd);
  });
});

document.getElementById('clearChatBtn').addEventListener('click', () => {
  chatStream.innerHTML = '';
});

// In-Browser Speech Recognition (Web Speech API with smart sentence buffering)
let speechDebounceTimer = null;
let currentTranscriptBuffer = "";

function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    console.log('[STT] Web Speech API not supported in this browser.');
    return;
  }

  recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = 'en-US';

  recognition.onstart = () => {
    isRecognizing = true;
    currentTranscriptBuffer = "";
    if (!isAssistantSpeaking) {
      setAiState('listening');
    }
  };

  recognition.onresult = (event) => {
    // If assistant is currently speaking or computing, ignore all audio to prevent self-feedback loop
    if (isAssistantSpeaking || currentAiState === 'speaking' || currentAiState === 'thinking') {
      currentTranscriptBuffer = "";
      userInput.value = "";
      if (speechDebounceTimer) clearTimeout(speechDebounceTimer);
      return;
    }

    let interimTranscript = '';
    let finalTranscript = '';

    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        finalTranscript += event.results[i][0].transcript;
      } else {
        interimTranscript += event.results[i][0].transcript;
      }
    }

    const liveText = (finalTranscript || interimTranscript).trim();
    if (liveText && !isAssistantSpeaking) {
      currentTranscriptBuffer = liveText;
      userInput.value = liveText;

      // Reset silence debounce timer: wait 1.2s of silence after speaking before sending
      if (speechDebounceTimer) clearTimeout(speechDebounceTimer);
      speechDebounceTimer = setTimeout(() => {
        if (currentTranscriptBuffer.trim() && !isAssistantSpeaking) {
          const toSend = currentTranscriptBuffer.trim();
          currentTranscriptBuffer = "";
          userInput.value = "";
          if (recognition && isRecognizing) {
            recognition.stop();
          }
          sendMessage(toSend);
        }
      }, 1200);
    }
  };

  recognition.onerror = (e) => {
    console.warn('[STT] Recognition error:', e);
    if (speechDebounceTimer) clearTimeout(speechDebounceTimer);
    isRecognizing = false;
    if (!isAssistantSpeaking) setAiState('idle');
  };

  recognition.onend = () => {
    isRecognizing = false;
    if (speechDebounceTimer) {
      clearTimeout(speechDebounceTimer);
    }
    // Only send buffered text if assistant was NOT speaking
    if (currentTranscriptBuffer.trim() && !isAssistantSpeaking && currentAiState !== 'speaking' && currentAiState !== 'thinking') {
      const toSend = currentTranscriptBuffer.trim();
      currentTranscriptBuffer = "";
      userInput.value = "";
      sendMessage(toSend);
    } else if (currentAiState === 'listening') {
      setAiState('idle');
    }
  };
}

function triggerVoiceRecognition() {
  if (isAssistantSpeaking || currentAiState === 'speaking' || currentAiState === 'thinking') {
    return;
  }

  if (!recognition) {
    initSpeechRecognition();
  }

  if (recognition && !isRecognizing) {
    try {
      recognition.start();
    } catch (e) {
      console.warn('STT start error:', e);
    }
  }
}

micBtn.addEventListener('click', () => {
  if (!recognition) {
    initSpeechRecognition();
  }

  if (recognition) {
    if (isRecognizing) {
      recognition.stop();
    } else {
      triggerVoiceRecognition();
    }
  } else {
    userInput.focus();
  }
});

// Continuous Mic Toggle Button
autoMicToggleBtn.addEventListener('click', () => {
  continuousMicEnabled = !continuousMicEnabled;
  if (continuousMicEnabled) {
    autoMicToggleBtn.classList.add('active');
    triggerVoiceRecognition();
  } else {
    autoMicToggleBtn.classList.remove('active');
    if (recognition && isRecognizing) {
      recognition.stop();
    }
  }
});

// ============================================================================
// 5. SECURITY CONFIRMATION MODAL & MEMORY BANK
// ============================================================================

function showConfirmModal(id, title, message) {
  currentConfirmId = id;
  modalTitle.textContent = title || 'SECURITY OVERRIDE';
  modalMessage.textContent = message || 'Authorize this action?';
  confirmModal.style.display = 'flex';
}

modalAllowBtn.addEventListener('click', () => {
  confirmModal.style.display = 'none';
  if (ws && currentConfirmId) {
    ws.send(JSON.stringify({ type: 'confirm_response', id: currentConfirmId, approved: true }));
  }
  currentConfirmId = null;
});

modalDenyBtn.addEventListener('click', () => {
  confirmModal.style.display = 'none';
  if (ws && currentConfirmId) {
    ws.send(JSON.stringify({ type: 'confirm_response', id: currentConfirmId, approved: false }));
  }
  currentConfirmId = null;
});

// Memory Modal
memCardBtn.addEventListener('click', async () => {
  try {
    const res = await fetch('/api/memory');
    const data = await res.json();

    document.getElementById('memTotalCount').textContent = data.stats.total_conversations || 0;
    document.getElementById('memVectorCount').textContent = data.stats.vector_entries || 0;
    document.getElementById('memFactsCount').textContent = Object.keys(data.profile.facts || {}).length;

    // Profile facts
    const chipsContainer = document.getElementById('profileChips');
    chipsContainer.innerHTML = '';
    const facts = data.profile.facts || {};
    if (Object.keys(facts).length === 0) {
      chipsContainer.innerHTML = '<span class="empty-hint">No learned facts yet. Tell Quadroid your name or preferences!</span>';
    } else {
      for (const [k, v] of Object.entries(facts)) {
        const chip = document.createElement('span');
        chip.className = 'fact-chip';
        chip.textContent = `${k}: ${v}`;
        chipsContainer.appendChild(chip);
      }
    }

    // Recent list
    const recentList = document.getElementById('recentMemList');
    recentList.innerHTML = '';
    const convs = data.conversations || [];
    if (convs.length === 0) {
      recentList.innerHTML = '<span class="empty-hint">No past conversations recorded.</span>';
    } else {
      convs.forEach((c) => {
        const item = document.createElement('div');
        item.className = 'mem-history-card';
        item.innerHTML = `
          <div class="date">${(c.timestamp || '').slice(0, 16).replace('T', ' ')}</div>
          <div><strong>Q:</strong> ${formatMarkdown(c.user_input)}</div>
          <div><strong>A:</strong> ${formatMarkdown(c.assistant_response)}</div>
        `;
        recentList.appendChild(item);
      });
    }

    memoryModal.style.display = 'flex';
  } catch (e) {
    console.error('Failed to load memory data:', e);
  }
});

closeMemModal.addEventListener('click', () => {
  memoryModal.style.display = 'none';
});

// ============================================================================
// 6. CLOCK & UPTIME LOOP
// ============================================================================

function updateClock() {
  const now = new Date();
  clockDisplay.textContent = now.toLocaleTimeString([], { hour12: false });

  const elapsedSec = Math.floor((Date.now() - sessionStartTime) / 1000);
  const m = Math.floor(elapsedSec / 60);
  const s = elapsedSec % 60;
  footerUptime.textContent = `UPTIME: ${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

setInterval(updateClock, 1000);
updateClock();

// Initialize Three.js & WebSocket on Load
window.addEventListener('DOMContentLoaded', () => {
  initThreeJS();
  connectWebSocket();
  initSpeechRecognition();
});
