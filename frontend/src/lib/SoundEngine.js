/**
 * ClearHire Sound Engine (Disabled)
 * Sound has been completely removed from the entire application.
 * All methods are silent no-ops to preserve API compatibility without creating AudioContext.
 */
export class SoundEngine {
  constructor() {
    this.ctx = null;
    this.isMuted = true;
    this.initialized = false;
  }

  init() {}

  toggleAudio() {
    return false;
  }

  setMuted() {}

  updateVelocity() {}

  playHoverSound() {}

  playClickSound() {}

  playWarpPulse() {}

  playStellarChime() {}

  playChimeSound() {}
}
