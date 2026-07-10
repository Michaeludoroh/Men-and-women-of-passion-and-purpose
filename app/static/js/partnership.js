/**
 * Partnership page UI — particles, reveal, counters, arms accordion,
 * carousel, FAQ, clipboard, schedule cards, ripple, smooth scroll.
 * No backend / form field changes.
 */
(function () {
  "use strict";

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function initReveal() {
    const nodes = document.querySelectorAll("[data-kp-reveal]");
    if (!nodes.length) return;
    if (reduceMotion || !("IntersectionObserver" in window)) {
      nodes.forEach((el) => el.classList.add("is-visible"));
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          io.unobserve(entry.target);
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -36px 0px" }
    );
    nodes.forEach((el) => io.observe(el));
  }

  function animateCounter(el) {
    const target = Number(el.getAttribute("data-target") || 0);
    const suffix = el.getAttribute("data-suffix") || "";
    if (reduceMotion) {
      el.textContent = target.toLocaleString() + suffix;
      return;
    }
    const duration = 1700;
    const start = performance.now();
    function tick(now) {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      el.textContent = Math.round(target * eased).toLocaleString() + suffix;
      if (t < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  function initCounters() {
    const counters = document.querySelectorAll("[data-counter]");
    if (!counters.length) return;
    if (!("IntersectionObserver" in window)) {
      counters.forEach(animateCounter);
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          animateCounter(entry.target);
          io.unobserve(entry.target);
        });
      },
      { threshold: 0.35 }
    );
    counters.forEach((el) => io.observe(el));
  }

  function showToast(message) {
    const toast = document.getElementById("kp-toast");
    if (!toast) return;
    toast.textContent = message || "Account number copied";
    toast.hidden = false;
    toast.classList.add("is-show");
    clearTimeout(showToast._timer);
    showToast._timer = setTimeout(() => {
      toast.classList.remove("is-show");
      setTimeout(() => {
        toast.hidden = true;
      }, 280);
    }, 2200);
  }

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise((resolve, reject) => {
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.left = "-9999px";
      document.body.appendChild(ta);
      ta.select();
      try {
        document.execCommand("copy");
        resolve();
      } catch (err) {
        reject(err);
      } finally {
        document.body.removeChild(ta);
      }
    });
  }

  function initCopyButtons() {
    document.querySelectorAll("[data-copy]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const value = btn.getAttribute("data-copy") || "";
        copyText(value)
          .then(() => {
            showToast("Account number copied");
            btn.classList.add("is-copied");
            setTimeout(() => btn.classList.remove("is-copied"), 1400);
          })
          .catch(() => showToast("Unable to copy — please copy manually"));
      });
    });
  }

  function initArmsAccordion() {
    const root = document.querySelector("[data-kp-arms]");
    if (!root) return;

    function setToggleLabel(btn, expanded) {
      const icon = btn.querySelector("i");
      btn.textContent = "";
      btn.appendChild(document.createTextNode(expanded ? "Show Less " : "Learn More "));
      const i = document.createElement("i");
      i.className = expanded ? "fas fa-minus" : "fas fa-plus";
      i.setAttribute("aria-hidden", "true");
      btn.appendChild(i);
      if (icon && icon.parentNode === btn) {
        /* replaced */
      }
    }

    root.querySelectorAll("[data-arm-toggle]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const panelId = btn.getAttribute("aria-controls");
        const panel = panelId ? document.getElementById(panelId) : null;
        const card = btn.closest(".kp-arm-card");
        const expanded = btn.getAttribute("aria-expanded") === "true";

        root.querySelectorAll("[data-arm-toggle]").forEach((other) => {
          if (other === btn) return;
          other.setAttribute("aria-expanded", "false");
          const oid = other.getAttribute("aria-controls");
          const op = oid ? document.getElementById(oid) : null;
          if (op) op.hidden = true;
          other.closest(".kp-arm-card")?.classList.remove("is-expanded");
          setToggleLabel(other, false);
        });

        const nextExpanded = !expanded;
        btn.setAttribute("aria-expanded", nextExpanded ? "true" : "false");
        if (panel) panel.hidden = !nextExpanded;
        card?.classList.toggle("is-expanded", nextExpanded);
        setToggleLabel(btn, nextExpanded);
      });
    });
  }

  function initCarousel() {
    const root = document.querySelector("[data-kp-carousel]");
    if (!root) return;
    const slides = Array.from(root.querySelectorAll("[data-kp-slide]"));
    const dotsWrap = root.querySelector("[data-kp-dots]");
    const prevBtn = root.querySelector("[data-kp-prev]");
    const nextBtn = root.querySelector("[data-kp-next]");
    if (slides.length < 2) return;

    let index = 0;
    let timer = null;

    slides.forEach((_, i) => {
      const dot = document.createElement("button");
      dot.type = "button";
      dot.className = "kp-carousel-dot" + (i === 0 ? " is-active" : "");
      dot.setAttribute("aria-label", "Go to testimonial " + (i + 1));
      dot.setAttribute("role", "tab");
      dot.addEventListener("click", () => go(i));
      dotsWrap.appendChild(dot);
    });
    const dots = Array.from(dotsWrap.querySelectorAll(".kp-carousel-dot"));

    function go(i) {
      index = (i + slides.length) % slides.length;
      slides.forEach((slide, s) => {
        const active = s === index;
        slide.classList.toggle("is-active", active);
        slide.setAttribute("aria-hidden", active ? "false" : "true");
      });
      dots.forEach((dot, d) => dot.classList.toggle("is-active", d === index));
      restart();
    }

    function restart() {
      if (reduceMotion) return;
      clearInterval(timer);
      timer = setInterval(() => go(index + 1), 5500);
    }

    if (prevBtn) prevBtn.addEventListener("click", () => go(index - 1));
    if (nextBtn) nextBtn.addEventListener("click", () => go(index + 1));
    root.addEventListener("mouseenter", () => clearInterval(timer));
    root.addEventListener("mouseleave", restart);
    root.addEventListener("focusin", () => clearInterval(timer));
    root.addEventListener("focusout", restart);
    restart();
  }

  function initFaq() {
    const faq = document.querySelector("[data-kp-faq]");
    if (!faq) return;
    faq.querySelectorAll(".kp-faq-trigger").forEach((btn) => {
      btn.addEventListener("click", () => {
        const item = btn.closest(".kp-faq-item");
        const expanded = btn.getAttribute("aria-expanded") === "true";
        const icon = btn.querySelector(".kp-faq-icon i");

        faq.querySelectorAll(".kp-faq-item").forEach((other) => {
          if (other === item) return;
          other.classList.remove("is-open");
          const ob = other.querySelector(".kp-faq-trigger");
          if (ob) ob.setAttribute("aria-expanded", "false");
          const oi = other.querySelector(".kp-faq-icon i");
          if (oi) oi.className = "fas fa-plus";
        });

        if (expanded) {
          item?.classList.remove("is-open");
          btn.setAttribute("aria-expanded", "false");
          if (icon) icon.className = "fas fa-plus";
        } else {
          item?.classList.add("is-open");
          btn.setAttribute("aria-expanded", "true");
          if (icon) icon.className = "fas fa-minus";
        }
      });
    });
  }

  function initScheduleCards() {
    const group = document.querySelector("[data-kp-schedule]");
    if (!group) return;
    group.querySelectorAll("[data-select-card]").forEach((card) => {
      card.addEventListener("click", () => {
        group.querySelectorAll("[data-select-card]").forEach((c) => {
          c.classList.remove("is-selected");
          c.setAttribute("aria-pressed", "false");
        });
        card.classList.add("is-selected");
        card.setAttribute("aria-pressed", "true");
      });
    });
  }

  function initParticles() {
    const canvas = document.querySelector("[data-kp-particles]");
    if (!canvas || reduceMotion) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let particles = [];
    let raf = 0;
    let w = 0;
    let h = 0;

    function resize() {
      const parent = canvas.parentElement;
      w = parent.clientWidth;
      h = parent.clientHeight;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      canvas.style.width = w + "px";
      canvas.style.height = h + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const count = Math.min(42, Math.floor((w * h) / 28000));
      particles = Array.from({ length: count }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        r: 1 + Math.random() * 2.2,
        vy: 0.15 + Math.random() * 0.35,
        vx: (Math.random() - 0.5) * 0.25,
        a: 0.25 + Math.random() * 0.45,
      }));
    }

    function draw() {
      ctx.clearRect(0, 0, w, h);
      particles.forEach((p) => {
        p.y -= p.vy;
        p.x += p.vx;
        if (p.y < -10) {
          p.y = h + 10;
          p.x = Math.random() * w;
        }
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(212, 175, 55," + p.a + ")";
        ctx.fill();
      });
      raf = requestAnimationFrame(draw);
    }

    resize();
    draw();
    window.addEventListener("resize", resize, { passive: true });
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) cancelAnimationFrame(raf);
      else raf = requestAnimationFrame(draw);
    });
  }

  function initParallax() {
    if (reduceMotion) return;
    const hero = document.querySelector(".kp-hero");
    const bg = document.querySelector(".kp-hero-bg");
    if (!hero || !bg) return;
    let ticking = false;
    window.addEventListener(
      "scroll",
      () => {
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(() => {
          const rect = hero.getBoundingClientRect();
          if (rect.bottom > 0 && rect.top < window.innerHeight) {
            const offset = Math.min(40, Math.max(-40, -rect.top * 0.12));
            bg.style.transform = "scale(1.08) translate3d(0," + offset + "px,0)";
          }
          ticking = false;
        });
      },
      { passive: true }
    );
  }

  function initRipple() {
    document.querySelectorAll(".kp-ripple").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        if (reduceMotion) return;
        const rect = btn.getBoundingClientRect();
        const ripple = document.createElement("span");
        ripple.className = "kp-ripple-ink";
        const size = Math.max(rect.width, rect.height);
        ripple.style.width = ripple.style.height = size + "px";
        ripple.style.left = e.clientX - rect.left - size / 2 + "px";
        ripple.style.top = e.clientY - rect.top - size / 2 + "px";
        btn.appendChild(ripple);
        setTimeout(() => ripple.remove(), 600);
      });
    });
  }

  function initSmoothAnchors() {
    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
      anchor.addEventListener("click", (e) => {
        const id = anchor.getAttribute("href");
        if (!id || id === "#") return;
        const target = document.querySelector(id);
        if (!target) return;
        e.preventDefault();
        target.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
        if (target.id === "partner-form") {
          const first = target.querySelector("input, select, textarea, button");
          if (first) setTimeout(() => first.focus({ preventScroll: true }), 400);
        }
      });
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    initReveal();
    initCounters();
    initCopyButtons();
    initArmsAccordion();
    initCarousel();
    initFaq();
    initScheduleCards();
    initParticles();
    initParallax();
    initRipple();
    initSmoothAnchors();
  });
})();
