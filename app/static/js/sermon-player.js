/**
 * In-site sermon MP4 player modal.
 * External sermons redirect to the platform — they never use this player.
 */
(function () {
  const modal = document.getElementById("sermon-player-modal");
  if (!modal) return;

  const video = document.getElementById("sermon-player-video");
  const titleEl = document.getElementById("sermon-player-title");
  const descEl = document.getElementById("sermon-player-description");
  const loadingEl = document.getElementById("sermon-player-loading");
  const errorEl = document.getElementById("sermon-player-error");
  const playBtn = document.getElementById("sermon-btn-play");
  const muteBtn = document.getElementById("sermon-btn-mute");
  const seek = document.getElementById("sermon-seek");
  const volume = document.getElementById("sermon-volume");
  const speed = document.getElementById("sermon-speed");
  const pipBtn = document.getElementById("sermon-btn-pip");
  const fsBtn = document.getElementById("sermon-btn-fs");
  const elapsedEl = document.getElementById("sermon-time-elapsed");
  const remainingEl = document.getElementById("sermon-time-remaining");
  const closeEls = modal.querySelectorAll("[data-sermon-player-close]");

  let lastFocus = null;

  function formatTime(sec) {
    if (!isFinite(sec) || sec < 0) return "0:00";
    const total = Math.floor(sec);
    const m = Math.floor(total / 60);
    const s = total % 60;
    return m + ":" + String(s).padStart(2, "0");
  }

  function setLoading(on) {
    if (loadingEl) loadingEl.hidden = !on;
  }

  function setError(msg) {
    if (!errorEl) return;
    if (msg) {
      errorEl.textContent = msg;
      errorEl.hidden = false;
    } else {
      errorEl.textContent = "";
      errorEl.hidden = true;
    }
  }

  function stop() {
    try {
      video.pause();
    } catch (e) {}
    video.removeAttribute("src");
    video.removeAttribute("poster");
    while (video.firstChild) video.removeChild(video.firstChild);
    video.load();
  }

  function openPlayer(opts) {
    lastFocus = document.activeElement;
    setError("");
    setLoading(true);
    titleEl.textContent = opts.title || "";
    descEl.textContent = opts.description || "";
    stop();
    if (opts.poster) video.setAttribute("poster", opts.poster);
    const source = document.createElement("source");
    source.src = opts.src;
    source.type = "video/mp4";
    video.appendChild(source);
    video.load();
    modal.hidden = false;
    modal.classList.remove("hidden");
    document.body.classList.add("sermon-player-open");
    playBtn.focus();

    const onReady = () => {
      setLoading(false);
      video.play().catch(() => {});
      updatePlayBtn();
    };
    const onErr = () => {
      setLoading(false);
      setError("Unable to play this sermon video. Please try again later.");
    };
    video.addEventListener("loadeddata", onReady, { once: true });
    video.addEventListener("error", onErr, { once: true });
  }

  function closePlayer() {
    stop();
    setLoading(false);
    setError("");
    modal.classList.add("hidden");
    modal.hidden = true;
    document.body.classList.remove("sermon-player-open");
    if (lastFocus && typeof lastFocus.focus === "function") {
      try {
        lastFocus.focus();
      } catch (e) {}
    }
  }

  function updatePlayBtn() {
    playBtn.textContent = video.paused ? "▶" : "❚❚";
    playBtn.setAttribute("aria-label", video.paused ? "Play" : "Pause");
  }

  function updateMuteBtn() {
    muteBtn.textContent = video.muted || video.volume === 0 ? "🔇" : "🔊";
    muteBtn.setAttribute("aria-label", video.muted ? "Unmute" : "Mute");
  }

  function updateTimes() {
    const cur = video.currentTime || 0;
    const dur = video.duration || 0;
    elapsedEl.textContent = formatTime(cur);
    remainingEl.textContent = formatTime(Math.max(0, dur - cur));
    if (dur > 0 && seek && !seek.matches(":active")) {
      seek.value = String(Math.round((cur / dur) * 1000));
    }
  }

  playBtn.addEventListener("click", () => {
    if (video.paused) video.play().catch(() => {});
    else video.pause();
    updatePlayBtn();
  });

  muteBtn.addEventListener("click", () => {
    video.muted = !video.muted;
    updateMuteBtn();
  });

  volume.addEventListener("input", () => {
    video.volume = parseFloat(volume.value) || 0;
    video.muted = video.volume === 0;
    updateMuteBtn();
  });

  seek.addEventListener("input", () => {
    if (!video.duration) return;
    video.currentTime = (parseInt(seek.value, 10) / 1000) * video.duration;
  });

  speed.addEventListener("change", () => {
    video.playbackRate = parseFloat(speed.value) || 1;
  });

  if (pipBtn) {
    if (!document.pictureInPictureEnabled) pipBtn.hidden = true;
    pipBtn.addEventListener("click", async () => {
      try {
        if (document.pictureInPictureElement) await document.exitPictureInPicture();
        else if (video.requestPictureInPicture) await video.requestPictureInPicture();
      } catch (e) {}
    });
  }

  fsBtn.addEventListener("click", () => {
    const stage = modal.querySelector(".sermon-player-stage") || video;
    if (document.fullscreenElement) {
      document.exitFullscreen().catch(() => {});
    } else if (stage.requestFullscreen) {
      stage.requestFullscreen().catch(() => {});
    }
  });

  video.addEventListener("play", updatePlayBtn);
  video.addEventListener("pause", updatePlayBtn);
  video.addEventListener("timeupdate", updateTimes);
  video.addEventListener("loadedmetadata", updateTimes);
  video.addEventListener("volumechange", updateMuteBtn);

  closeEls.forEach((el) => el.addEventListener("click", closePlayer));

  document.addEventListener("click", (event) => {
    const trigger = event.target.closest && event.target.closest(".sermon-play-trigger");
    if (!trigger) return;
    const src = trigger.dataset.playSrc;
    if (!src) return;
    event.preventDefault();
    openPlayer({
      src: src,
      poster: trigger.dataset.poster || "",
      title: trigger.dataset.title || "",
      description: trigger.dataset.description || "",
    });
  });

  document.addEventListener("keydown", (event) => {
    if (modal.classList.contains("hidden") || modal.hidden) return;
    if (event.key === "Escape") {
      closePlayer();
      return;
    }
    if (event.key === " " || event.code === "Space") {
      event.preventDefault();
      playBtn.click();
    }
    if (event.key === "m" || event.key === "M") muteBtn.click();
    if (event.key === "f" || event.key === "F") fsBtn.click();
    if (event.key === "ArrowLeft") video.currentTime = Math.max(0, video.currentTime - 5);
    if (event.key === "ArrowRight") {
      video.currentTime = Math.min(video.duration || 0, video.currentTime + 5);
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      video.volume = Math.min(1, video.volume + 0.1);
      volume.value = String(video.volume);
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      video.volume = Math.max(0, video.volume - 0.1);
      volume.value = String(video.volume);
    }
  });
})();
