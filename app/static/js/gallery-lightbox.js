(function () {
  const lightbox = document.getElementById("gallery-lightbox");
  if (!lightbox) return;

  const triggers = Array.from(document.querySelectorAll(".gallery-lightbox-trigger"));
  if (!triggers.length) return;

  const imageEl = document.getElementById("gallery-lightbox-image");
  const videoEl = document.getElementById("gallery-lightbox-video");
  const titleEl = document.getElementById("gallery-lightbox-title");
  const metaEl = document.getElementById("gallery-lightbox-meta");
  const descriptionEl = document.getElementById("gallery-lightbox-description");
  const closeBtn = lightbox.querySelector(".gallery-lightbox-close");
  const prevBtn = lightbox.querySelector(".gallery-lightbox-prev");
  const nextBtn = lightbox.querySelector(".gallery-lightbox-next");

  const items = triggers.map((node) => ({
    src: node.dataset.src,
    poster: node.dataset.poster || "",
    mediaType: node.dataset.mediaType || "image",
    title: node.dataset.title || "",
    description: node.dataset.description || "",
    category: node.dataset.category || "",
  }));

  let currentIndex = 0;

  function stopVideo() {
    if (!videoEl) return;
    try {
      videoEl.pause();
    } catch (e) {
      /* ignore */
    }
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
    metaEl.textContent = item.category + (item.mediaType === "video" ? " · Video" : "");
    descriptionEl.textContent = item.description;
    prevBtn.disabled = index === 0;
    nextBtn.disabled = index === items.length - 1;

    if (item.mediaType === "video") {
      imageEl.hidden = true;
      imageEl.removeAttribute("src");
      stopVideo();
      videoEl.hidden = false;
      if (item.poster) videoEl.setAttribute("poster", item.poster);
      const source = document.createElement("source");
      source.src = item.src;
      const ext = (item.src.split(".").pop() || "mp4").split("?")[0].toLowerCase();
      source.type = ext === "webm" ? "video/webm" : "video/mp4";
      videoEl.appendChild(source);
      videoEl.load();
    } else {
      stopVideo();
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
    if (videoEl) videoEl.hidden = true;
  }

  function showPrev() {
    if (currentIndex > 0) open(currentIndex - 1);
  }

  function showNext() {
    if (currentIndex < items.length - 1) open(currentIndex + 1);
  }

  triggers.forEach((trigger) => {
    trigger.addEventListener("click", () => open(Number(trigger.dataset.index)));
    trigger.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        open(Number(trigger.dataset.index));
      }
    });
  });

  closeBtn.addEventListener("click", close);
  prevBtn.addEventListener("click", showPrev);
  nextBtn.addEventListener("click", showNext);

  lightbox.addEventListener("click", (event) => {
    if (event.target === lightbox) close();
  });

  document.addEventListener("keydown", (event) => {
    if (lightbox.classList.contains("hidden")) return;
    if (event.key === "Escape") close();
    if (event.key === "ArrowLeft") showPrev();
    if (event.key === "ArrowRight") showNext();
  });
})();
