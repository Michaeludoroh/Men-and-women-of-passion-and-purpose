/**
 * Streams of Joy Inspired Main JS - Video Controls + Elementor Animations
 * Features: Video hero toggle, scroll reveals, stagger animations, smooth scroll
 */

document.addEventListener('DOMContentLoaded', function() {
    // Hero background videos only — never touch sermon preview videos
    const heroVideos = document.querySelectorAll(
        'section:first-of-type video:not(.sermon-preview-video)'
    );
    heroVideos.forEach((video) => {
        video.muted = true;
        video.playsInline = true;
        video.play().catch(() => {});
    });

    // Elementor-style Scroll Animations (IntersectionObserver)
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in', 'animate-slide-up');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe cards, sections for reveal
    document.querySelectorAll('.card, .sermon-card, .card-hero-video, .card-vision, section > div > div > div').forEach(el => {
        observer.observe(el);
    });

    // Stagger Animation (Enhanced from original)
    const animateElements = document.querySelectorAll('.card, .btn-hero-gold, .nav-link, .sermon-card');
    animateElements.forEach((el, index) => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        setTimeout(() => {
            el.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        }, 150 * index);
    });

    // Smooth Internal Links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Navbar Scroll Effect
    let lastScrollY = window.scrollY;
    window.addEventListener('scroll', () => {
        const nav = document.querySelector('nav');
        if (window.scrollY > 100) {
            nav.classList.add('nav-scrolled');
        } else {
            nav.classList.remove('nav-scrolled');
        }

        // Hide/show on scroll direction (mobile)
        if (window.innerWidth <= 768) {
            if (window.scrollY > lastScrollY && window.scrollY > 100) {
                nav.style.transform = 'translateY(-100%)';
            } else {
                nav.style.transform = 'translateY(0)';
            }
        }
        lastScrollY = window.scrollY;
    });

    // Parallax Effect for Hero (subtle) — exclude sermon previews
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        const heroVideo = document.querySelector(
            'section:first-of-type video:not(.sermon-preview-video)'
        );
        if (heroVideo) {
            heroVideo.style.transform = `translateY(${scrolled * 0.5}px)`;
        }
    });

    // Hotspot Pulse Animation (Elementor-style from codes.txt)
    const hotspots = document.querySelectorAll('.hotspot-icon');
    hotspots.forEach((hotspot, index) => {
        hotspot.style.animationDelay = `${index * 0.3}s`;
    });

    /**
     * SermonPreviewVideo
     * - Only ONE muted autoplay preview at a time
     * - Pause when leaving viewport (IntersectionObserver)
     * - prefers-reduced-motion → poster only
     * - Homepage cards link to /sermons#sermon-id
     * - External cards open the platform; uploaded MP4 uses sermon-player.js
     */
    const sermonPreviews = document.querySelectorAll('[data-sermon-preview]');
    const prefersReducedMotion = window.matchMedia(
        '(prefers-reduced-motion: reduce)'
    ).matches;
    let activeSermonPreview = null;

    const showPreviewFallback = (preview) => {
        const video = preview.querySelector('.sermon-preview-video');
        const poster = preview.querySelector('.sermon-preview-poster');
        preview.classList.add('is-fallback');
        preview.classList.remove('is-playing');
        if (video) {
            try {
                video.pause();
            } catch (e) {
                /* ignore */
            }
        }
        if (poster) {
            poster.hidden = false;
            poster.classList.add('is-visible');
        }
    };

    const preparePreviewVideo = (video) => {
        video.muted = true;
        video.defaultMuted = true;
        video.playsInline = true;
        video.loop = true;
        video.controls = false;
        video.disablePictureInPicture = true;
        video.setAttribute('muted', '');
        video.setAttribute('playsinline', '');
        video.setAttribute('webkit-playsinline', '');
        video.removeAttribute('controls');
    };

    const loadPreviewSource = (video) => {
        const src = video.dataset.src;
        if (!src || video.getAttribute('src') === src) {
            return Promise.resolve();
        }
        return new Promise((resolve, reject) => {
            const onLoaded = () => {
                cleanup();
                resolve();
            };
            const onError = () => {
                cleanup();
                reject(new Error('preview media failed'));
            };
            const cleanup = () => {
                video.removeEventListener('loadeddata', onLoaded);
                video.removeEventListener('error', onError);
            };
            video.addEventListener('loadeddata', onLoaded, { once: true });
            video.addEventListener('error', onError, { once: true });
            video.src = src;
            video.load();
        });
    };

    const pausePreview = (preview) => {
        if (!preview) return;
        const video = preview.querySelector('.sermon-preview-video');
        const iframe = preview.querySelector('iframe.sermon-preview-iframe');
        if (video) {
            try {
                video.pause();
            } catch (e) {}
        }
        if (iframe) iframe.remove();
        preview.classList.remove('is-playing');
        if (activeSermonPreview === preview) activeSermonPreview = null;
    };

    const tryPlayPreview = (preview) => {
        if (prefersReducedMotion) {
            showPreviewFallback(preview);
            return;
        }

        // Enforce single autoplay across the page
        if (activeSermonPreview && activeSermonPreview !== preview) {
            pausePreview(activeSermonPreview);
        }

        const embed = preview.dataset.previewEmbed;
        if (embed && preview.dataset.mediaType === 'external') {
            const media = preview.querySelector('.sermon-preview-media');
            if (media && !media.querySelector('iframe.sermon-preview-iframe')) {
                const iframe = document.createElement('iframe');
                iframe.className = 'sermon-preview-iframe';
                iframe.setAttribute('title', 'Muted sermon preview');
                iframe.setAttribute('allow', 'autoplay; encrypted-media');
                iframe.setAttribute('loading', 'lazy');
                iframe.src = embed;
                media.appendChild(iframe);
            }
            activeSermonPreview = preview;
            preview.classList.add('is-playing');
            return;
        }

        const video = preview.querySelector('.sermon-preview-video');
        if (!video) return;

        preparePreviewVideo(video);
        loadPreviewSource(video)
            .then(() => {
                preparePreviewVideo(video);
                const playPromise = video.play();
                if (playPromise && typeof playPromise.then === 'function') {
                    return playPromise.then(() => {
                        preview.classList.add('is-playing');
                        preview.classList.remove('is-fallback');
                        activeSermonPreview = preview;
                    });
                }
                preview.classList.add('is-playing');
                activeSermonPreview = preview;
            })
            .catch(() => showPreviewFallback(preview));

        video.addEventListener('error', () => showPreviewFallback(preview), {
            once: true,
        });
    };

    if ('IntersectionObserver' in window) {
        const previewObserver = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        tryPlayPreview(entry.target);
                    } else {
                        pausePreview(entry.target);
                    }
                });
            },
            { rootMargin: '40px 0px', threshold: 0.45 }
        );
        sermonPreviews.forEach((preview) => previewObserver.observe(preview));
    } else if (sermonPreviews.length) {
        tryPlayPreview(sermonPreviews[0]);
    }

    sermonPreviews.forEach((preview) => {
        preview.addEventListener('keydown', (event) => {
            if (event.key === ' ' || event.key === 'Spacebar') {
                if (preview.tagName === 'A' || preview.tagName === 'BUTTON') {
                    event.preventDefault();
                    preview.click();
                }
            }
        });
    });

    document.addEventListener('visibilitychange', () => {
        if (document.hidden && activeSermonPreview) {
            pausePreview(activeSermonPreview);
        }
    });

    /**
     * Leader profile videos — lazy-load sources when in view.
     * Controls remain enabled; no autoplay.
     */
    const lazyLeaderVideos = document.querySelectorAll(
        '.leader-video source[data-src], .leader-admin-video source[data-src]'
    );
    const loadLeaderVideoSource = (source) => {
        if (!source.dataset.src) return;
        source.src = source.dataset.src;
        source.removeAttribute('data-src');
        const video = source.parentElement;
        if (video && typeof video.load === 'function') {
            video.load();
        }
    };
    if ('IntersectionObserver' in window) {
        const leaderVideoObserver = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (!entry.isIntersecting) return;
                    const video = entry.target;
                    video.querySelectorAll('source[data-src]').forEach(loadLeaderVideoSource);
                    leaderVideoObserver.unobserve(video);
                });
            },
            { rootMargin: '150px 0px', threshold: 0.05 }
        );
        document.querySelectorAll('.leader-video, .leader-admin-video').forEach((video) => {
            if (video.querySelector('source[data-src]')) {
                leaderVideoObserver.observe(video);
            }
        });
    } else {
        lazyLeaderVideos.forEach(loadLeaderVideoSource);
    }

    /**
     * Expandable leader biographies — Read More / Read Less.
     * Full text always remains in the DOM; only visual clamp changes.
     */
    document.querySelectorAll('[data-leader-bio]').forEach((wrap) => {
        const content = wrap.querySelector('.leader-bio-content');
        const toggle = wrap.querySelector('[data-bio-toggle]');
        if (!content || !toggle) return;

        const needsToggle = () => {
            // Temporarily expand to measure full height vs clamped height
            const wasExpanded = wrap.classList.contains('is-expanded');
            wrap.classList.remove('is-expanded');
            const clamped = content.scrollHeight > content.clientHeight + 2;
            if (wasExpanded) wrap.classList.add('is-expanded');
            return clamped;
        };

        const refresh = () => {
            if (needsToggle()) {
                toggle.hidden = false;
            } else {
                toggle.hidden = true;
                wrap.classList.remove('is-expanded');
                toggle.setAttribute('aria-expanded', 'false');
                toggle.textContent = 'Read More';
            }
        };

        refresh();
        window.addEventListener('resize', refresh);

        toggle.addEventListener('click', () => {
            const expanding = !wrap.classList.contains('is-expanded');
            wrap.classList.toggle('is-expanded', expanding);
            toggle.setAttribute('aria-expanded', expanding ? 'true' : 'false');
            toggle.textContent = expanding ? 'Read Less' : 'Read More';
        });
    });

    // Preloader (if needed)
    const preloader = document.querySelector('.preloader');
    if (preloader) {
        window.addEventListener('load', () => {
            preloader.style.opacity = '0';
            setTimeout(() => preloader.remove(), 500);
        });
    }
});

// Custom CSS animations via JS
const style = document.createElement('style');
style.textContent = `
  @keyframes slide-up {
    from { 
      opacity: 0; 
      transform: translateY(50px); 
    }
    to { 
      opacity: 1; 
      transform: translateY(0); 
    }
  }
  @keyframes fade-in {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  .nav-scrolled {
    box-shadow: 0 -4px 20px rgba(0,0,0,0.1) !important;
  }
`;
document.head.appendChild(style);

// Mobile menu smooth open/close
document.querySelector('.mobile-menu-button')?.addEventListener('click', function() {
    document.querySelector('.md\\:hidden')?.classList.toggle('menu-open');
});

