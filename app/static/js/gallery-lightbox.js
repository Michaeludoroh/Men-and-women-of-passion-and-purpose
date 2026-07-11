(function () {
  const lightbox = document.getElementById("gallery-lightbox");
  const triggers = Array.from(document.querySelectorAll(".gallery-lightbox-trigger"));
  const previewVideos = Array.from(document.querySelectorAll(".gallery-preview-video"));
  const externalThumbs = Array.from(document.querySelectorAll(".gallery-external-thumb"));

  // --- Muted autoplay for uploaded MP4 thumbs (Intersection Observer) ---
  if (previewVideos.length && "IntersectionObserver" in window) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const video = entry.target;
          if (entry.isIntersecting) {
            if (!video.getAttribute("src") && video.dataset.src) {
              video.src = video.dataset.src;
            }
            const playPromise = video.play();
            if (playPromise && typeof playPromise.catch === "function") {
              playPromise.catch(function () {});
            }
          } else {
            try {
              video.pause();
            } catch (e) {}
          }
        });
      },
      { rootMargin: "80px", threshold: 0.35 }
    );
    previewVideos.forEach((v) => {
      v.muted = true;
      io.observe(v);
    });
  }

  // --- YouTube muted preview when visible; click still goes to platform via parent <a> ---
  if (externalThumbs.length && "IntersectionObserver" in window) {
    const eio = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const thumb = entry.target;
          const embed = thumb.dataset.previewEmbed;
          if (!embed) return;
          let iframe = thumb.querySelector("iframe.gallery-preview-iframe");
          if (entry.isIntersecting) {
            if (!iframe) {
              iframe = document.createElement("iframe");
              iframe.className = "gallery-preview-iframe";
              iframe.setAttribute("title", "Muted video preview");
              iframe.setAttribute("allow", "autoplay; encrypted-media");
              iframe.setAttribute("loading", "lazy");
              iframe.src = embed;
              thumb.appendChild(iframe);
              const muteBtn = thumb.querySelector(".gallery-mute-btn");
              if (muteBtn) muteBtn.hidden = false;
            }
          } else if (iframe) {
            iframe.remove();
            const muteBtn = thumb.querySelector(".gallery-mute-btn");
            if (muteBtn) muteBtn.hidden = true;
          }
        });
      },
      { rootMargin: "40px", threshold: 0.4 }
    );
    externalThumbs.forEach((t) => eio.observe(t));
  }

  // Mute button on external cards is decorative for YouTube muted embeds (always muted)
  document.querySelectorAll(".gallery-mute-btn").forEach((btn) => {
    btn.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      // Previews stay muted by platform policy; button acknowledges state for a11y
      btn.setAttribute("aria-label", "Preview is muted");
      btn.dataset.muted = "true";
    });
  });

  if (!lightbox) return;
  if (!triggers.length) return;

  const imageEl = document.getElementById("gallery-lightbox-image");
  const videoWrap = lightbox.querySelector(".gallery-lightbox-video-wrap");
  const videoEl = document.getElementById("gallery-lightbox-video");
  const titleEl = document.getElementById("gallery-lightbox-title");
  const metaEl = document.getElementById("gallery-lightbox-meta");
  const descriptionEl = document.getElementById("gallery-lightbox-description");
  const closeBtn = lightbox.querySelector(".gallery-lightbox-close");
  const prevBtn = lightbox.querySelector(".gallery-lightbox-prev");
  const nextBtn = lightbox.querySelector(".gallery-lightbox-next");
  const rateSelect = document.getElementById("gallery-playback-rate");
  const pipBtn = document.getElementById("gallery-pip-btn");

  const items = triggers.map((node) => ({
    src: node.dataset.src,
    poster: node.dataset.poster || "",
    mediaType: node.dataset.mediaType || "image",
    title: node.dataset.title || "",
    description: node.dataset.description || "",
    category: node.dataset.category || "",
    eventName: node.dataset.event || "",
  }));

  let currentIndex = 0;

  function stopVideo() {
    if (!videoEl) return;
    try {
      videoEl.pause();
    } catch (e) {}
    videoEl.removeAttribute("src");
    videoEl.removeAttribute("poster");
    while (videoEl.firstChild) videoEl.removeChild(videoEl.firstChild);
    videoEl.load();
  }

  function render(index) {
    const item = items[index];
    if (!item) return;
    currentIndex = index;

    titleEl.textContent = item.title;
    const bits = [item.category];
    if (item.eventName) bits.push(item.eventName);
    if (item.mediaType === "video") bits.push("Video");
    metaEl.textContent = bits.filter(Boolean).join(" · ");
    descriptionEl.textContent = item.description;
    prevBtn.disabled = index === 0;
    nextBtn.disabled = index === items.length - 1;

    if (item.mediaType === "video") {
      imageEl.hidden = true;
      imageEl.removeAttribute("src");
      stopVideo();
      if (videoWrap) videoWrap.hidden = false;
      videoEl.hidden = false;
      if (item.poster) videoEl.setAttribute("poster", item.poster);
      const source = document.createElement("source");
      source.src = item.src;
      source.type = "video/mp4";
      videoEl.appendChild(source);
      if (rateSelect) videoEl.playbackRate = parseFloat(rateSelect.value) || 1;
      videoEl.load();
      const playPromise = videoEl.play();
      if (playPromise && typeof playPromise.catch === "function") {
        playPromise.catch(function () {});
      }
    } else {
      stopVideo();
      if (videoWrap) videoWrap.hidden = true;
      if (videoEl) videoEl.hidden = true;
      imageEl.hidden = false;
      imageEl.src = item.src;
      imageEl.alt = item.title;
    }
  }

  function open(index) {
    render(index);
    lightbox.classList.remove("hidden");
    document.body.classList.add("gallery-lightbox-open");
    closeBtn.focus();
  }

  function close() {
    lightbox.classList.add("hidden");
    document.body.classList.remove("gallery-lightbox-open");
    imageEl.src = "";
    imageEl.hidden = true;
    stopVideo();
    if (videoWrap) videoWrap.hidden = true;
    if (videoEl) videoEl.hidden = true;
  }

  function showPrev() {
    if (currentIndex > 0) open(currentIndex - 1);
  }

  function showNext() {
    if (currentIndex < items.length - 1) open(currentIndex + 1);
  }

  triggers.forEach((trigger) => {
    trigger.addEventListener("click", (event) => {
      // Ignore clicks that bubbled from nested interactive controls if any
      if (event.target.closest && event.target.closest("a.gallery-external-link")) return;
      open(triggers.indexOf(trigger));
    });
    trigger.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        open(triggers.indexOf(trigger));
      }
    });
  });

  closeBtn.addEventListener("click", close);
  prevBtn.addEventListener("click", showPrev);
  nextBtn.addEventListener("click", showNext);

  lightbox.addEventListener("click", (event) => {
    if (event.target === lightbox) close();
  });

  if (rateSelect && videoEl) {
    rateSelect.addEventListener("change", () => {
      videoEl.playbackRate = parseFloat(rateSelect.value) || 1;
    });
  }

  if (pipBtn && videoEl) {
    if (!document.pictureInPictureEnabled) {
      pipBtn.hidden = true;
    }
    pipBtn.addEventListener("click", async () => {
      try {
        if (document.pictureInPictureElement) {
          await document.exitPictureInPicture();
        } else if (videoEl.requestPictureInPicture) {
          await videoEl.requestPictureInPicture();
        }
      } catch (e) {}
    });
  }

  document.addEventListener("keydown", (event) => {
    if (lightbox.classList.contains("hidden")) return;
    if (event.key === "Escape") close();
    if (event.key === "ArrowLeft") showPrev();
    if (event.key === "ArrowRight") showNext();

    if (!videoEl || videoEl.hidden) return;
    if (event.key === " " || event.code === "Space") {
      event.preventDefault();
      if (videoEl.paused) videoEl.play();
      else videoEl.pause();
    }
    if (event.key === "m" || event.key === "M") {
      videoEl.muted = !videoEl.muted;
    }
    if (event.key === "f" || event.key === "F") {
      if (document.fullscreenElement) {
        document.exitFullscreen().catch(function () {});
      } else if (videoEl.requestFullscreen) {
        videoEl.requestFullscreen().catch(function () {});
      }
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      videoEl.volume = Math.min(1, videoEl.volume + 0.1);
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      videoEl.volume = Math.max(0, videoEl.volume - 0.1);
    }
  });
})();
