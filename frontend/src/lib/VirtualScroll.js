/**
 * Scroll controller for the nine-chapter ClearHire application story.
 * Keeps the page viewport steady while wheel, touch, keyboard, and chapter
 * controls update one shared progress value for the HTML copy and 3D scene.
 */
export class VirtualScroll {
  constructor(options = {}) {
    this.maxProgress = options.maxProgress ?? 8.0; // Nine chapters: 0.0 to 8.0
    this.baseSensitivity = options.sensitivity ?? 0.0016;

    this.target = 0;
    this.current = 0;
    this.velocity = 0;
    this.speed = 0;
    this.reducedMotion = false;

    this.onUpdateCallbacks = [];
    this.onSectorChangeCallbacks = [];
    this.currentSector = 0;

    this.bound = false;
  }

  getSectorSpeedMultiplier(progress) {
    // Make the first wheel movement visibly push toward the monitor. Keep later
    // chapters slower so the complete paper-to-HR journey still takes time.
    if (progress < 0.9) return 3.0;
    if (progress >= 7) return 0.8;
    return 0.92;
  }

  bindEvents() {
    if (this.bound || typeof window === "undefined") return;
    this.bound = true;

    // 1. Mouse Wheel with Momentum Flick Accumulation
    this.wheelHandler = (e) => {
      // Allow native scrolling inside nested scrollable areas like inputs or modals
      const target = e.target;
      if (target && target.closest("input, textarea, select, [contenteditable='true']")) {
        return;
      }

      // Check if user is scrolling inside an internal scrollable container
      let el = target instanceof Element ? target : null;
      while (el && el !== document.body) {
        const style = window.getComputedStyle(el);
        const scrollable = /(auto|scroll)/.test(style.overflowY) && el.scrollHeight > el.clientHeight + 1;
        if (scrollable) {
          const canUp = el.scrollTop > 0;
          const canDown = el.scrollTop + el.clientHeight < el.scrollHeight - 1;
          if ((e.deltaY < 0 && canUp) || (e.deltaY > 0 && canDown)) return;
        }
        el = el.parentElement;
      }

      if (e.cancelable) {
        e.preventDefault();
      }

      const delta = e.deltaY * (e.deltaMode === 1 ? 25 : e.deltaMode === 2 ? window.innerHeight : 1);
      const sectorMult = this.getSectorSpeedMultiplier(this.current);
      const flickBoost = 1.0 + Math.min(this.speed * 0.45, 2.0);

      const effectiveSensitivity = this.baseSensitivity * sectorMult * flickBoost;
      this.target += delta * effectiveSensitivity;
      this.target = Math.max(0, Math.min(this.maxProgress, this.target));
    };
    window.addEventListener("wheel", this.wheelHandler, { passive: false });

    // 2. Touch Gestures with Inertial Flick
    let touchStartY = 0;
    let lastTouchTime = 0;
    let touchTarget = null;
    this.touchStartHandler = (e) => {
      if (e.touches.length === 1) {
        touchStartY = e.touches[0].clientY;
        lastTouchTime = performance.now();
        touchTarget = e.target;
      }
    };
    this.touchMoveHandler = (e) => {
      if (e.touches.length === 1) {
        const touchY = e.touches[0].clientY;
        const delta = touchStartY - touchY;

        if (touchTarget instanceof Element && touchTarget.closest("input, textarea, select, [contenteditable='true']")) {
          touchStartY = touchY;
          lastTouchTime = performance.now();
          return;
        }

        let el = touchTarget instanceof Element ? touchTarget : null;
        while (el && el !== document.body) {
          const style = window.getComputedStyle(el);
          const scrollable = /(auto|scroll)/.test(style.overflowY) && el.scrollHeight > el.clientHeight + 1;
          if (scrollable) {
            const canUp = el.scrollTop > 0;
            const canDown = el.scrollTop + el.clientHeight < el.scrollHeight - 1;
            if ((delta < 0 && canUp) || (delta > 0 && canDown)) {
              touchStartY = touchY;
              lastTouchTime = performance.now();
              return;
            }
          }
          el = el.parentElement;
        }

        touchStartY = touchY;

        const now = performance.now();
        const dt = Math.max(1, now - lastTouchTime);
        lastTouchTime = now;

        const touchVelocity = Math.abs(delta / dt);
        const flickBoost = 1.0 + Math.min(touchVelocity * 0.7, 2.2);
        const sectorMult = this.getSectorSpeedMultiplier(this.current);

        this.target += delta * this.baseSensitivity * 1.8 * sectorMult * flickBoost;
        this.target = Math.max(0, Math.min(this.maxProgress, this.target));
      }
    };
    window.addEventListener("touchstart", this.touchStartHandler, { passive: true });
    window.addEventListener("touchmove", this.touchMoveHandler, { passive: true });

    // 3. Keyboard Arrow & Page Navigation
    this.keyHandler = (e) => {
      if (e.target && (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.isContentEditable)) {
        return;
      }

      if (e.code === "ArrowDown" || e.code === "ArrowRight" || e.code === "PageDown") {
        e.preventDefault();
        this.nextSector();
      } else if (e.code === "ArrowUp" || e.code === "ArrowLeft" || e.code === "PageUp") {
        e.preventDefault();
        this.prevSector();
      } else if (e.code === "Home") {
        e.preventDefault();
        this.scrollToSector(0);
      } else if (e.code === "End") {
        e.preventDefault();
        this.scrollToSector(this.maxProgress);
      }
    };
    window.addEventListener("keydown", this.keyHandler);
  }

  unbindEvents() {
    if (!this.bound || typeof window === "undefined") return;
    window.removeEventListener("wheel", this.wheelHandler);
    window.removeEventListener("touchstart", this.touchStartHandler);
    window.removeEventListener("touchmove", this.touchMoveHandler);
    window.removeEventListener("keydown", this.keyHandler);
    this.bound = false;
  }

  scrollToSector(index) {
    this.target = Math.max(0, Math.min(this.maxProgress, Number(index)));
  }

  nextSector() {
    this.scrollToSector(Math.min(this.maxProgress, Math.round(this.current) + 1));
  }

  prevSector() {
    this.scrollToSector(Math.max(0, Math.round(this.current) - 1));
  }

  update(delta) {
    const prev = this.current;

    // Exponential damping keeps the same scroll response across frame rates.
    const frameSeconds = Math.max(0, Number(delta) || 0);
    const damping = this.reducedMotion ? 1 : 1 - Math.exp(-3.9 * frameSeconds);
    this.current += (this.target - this.current) * damping;

    // Instantaneous velocity calculation
    this.velocity = (this.current - prev) / Math.max(0.001, delta);
    this.speed = Math.abs(this.velocity);

    // Sector change trigger
    const sector = Math.max(0, Math.min(Math.round(this.maxProgress), Math.round(this.current)));
    if (sector !== this.currentSector) {
      this.currentSector = sector;
      for (const cb of this.onSectorChangeCallbacks) {
        cb(sector);
      }
    }

    // Dispatch update to subscribers
    for (const cb of this.onUpdateCallbacks) {
      cb(this.current, this.velocity, this.speed);
    }
  }

  onUpdate(cb) {
    this.onUpdateCallbacks.push(cb);
  }

  onSectorChange(cb) {
    this.onSectorChangeCallbacks.push(cb);
  }
}
