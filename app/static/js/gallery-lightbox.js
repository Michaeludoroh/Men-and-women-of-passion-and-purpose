(function () {
  const lightbox = document.getElementById("gallery-lightbox");
  if (!lightbox) return;

  const triggers = Array.from(document.querySelectorAll(".gallery-lightbox-trigger"));
  if (!triggers.length) return;

  const imageEl = document.getElementById("gallery-lightbox-image");
  const titleEl = document.getElementById("gallery-lightbox-title");
  const metaEl = document.getElementById("gallery-lightbox-meta");
  const descriptionEl = document.getElementById("gallery-lightbox-description");
  const closeBtn = lightbox.querySelector(".gallery-lightbox-close");
  const prevBtn = lightbox.querySelector(".gallery-lightbox-prev");
  const nextBtn = lightbox.querySelector(".gallery-lightbox-next");

  const items = triggers.map((node) => ({
    src: node.dataset.src,
    title: node.dataset.title || "",
    description: node.dataset.description || "",
    category: node.dataset.category || "",
  }));

  let currentIndex = 0;

  function render(index) {
    const item = items[index];
    if (!item) return;
    currentIndex = index;
    imageEl.src = item.src;
    imageEl.alt = item.title;
    titleEl.textContent = item.title;
    metaEl.textContent = item.category;
    descriptionEl.textContent = item.description;
    prevBtn.disabled = index === 0;
    nextBtn.disabled = index === items.length - 1;
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
