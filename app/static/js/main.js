/**
 * Streams of Joy Inspired Main JS - Video Controls + Elementor Animations
 * Features: Video hero toggle, scroll reveals, stagger animations, smooth scroll
 */

document.addEventListener('DOMContentLoaded', function() {
    // Video Hero Controls (Reference MP4 autoplay/mute toggle)
    const heroVideos = document.querySelectorAll('section:first-of-type video');
    heroVideos.forEach(video => {
        video.muted = true;
        video.play().catch(e => console.log('Autoplay prevented:', e));
        
        // Play/Pause toggle on click
        video.addEventListener('click', () => {
            if (video.paused) {
                video.play();
            } else {
                video.pause();
            }
        });
    });

    // Mute/Unmute toggle button (add to HTML if needed)
    const toggleMuteBtn = document.createElement('button');
    toggleMuteBtn.innerHTML = '<i class="fas fa-volume-mute"></i>';
    toggleMuteBtn.className = 'absolute top-6 right-6 z-30 p-3 bg-black/50 hover:bg-black/70 rounded-full text-white transition-all duration-200';
    toggleMuteBtn.onclick = () => {
        heroVideos.forEach(v => v.muted = !v.muted);
        toggleMuteBtn.innerHTML = heroVideos[0].muted ? '<i class="fas fa-volume-mute"></i>' : '<i class="fas fa-volume-up"></i>';
    };
    if (heroVideos.length) {
        heroVideos[0].parentNode.appendChild(toggleMuteBtn);
    }

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

    // Parallax Effect for Hero (subtle)
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        const heroVideo = document.querySelector('section:first-of-type video');
        if (heroVideo) {
            heroVideo.style.transform = `translateY(${scrolled * 0.5}px)`;
        }
    });

    // Hotspot Pulse Animation (Elementor-style from codes.txt)
    const hotspots = document.querySelectorAll('.hotspot-icon');
    hotspots.forEach((hotspot, index) => {
        hotspot.style.animationDelay = `${index * 0.3}s`;
    });

    // Sermon Cards Hover Effects
    document.querySelectorAll('.sermon-card').forEach(card => {
        card.addEventListener('mouseenter', () => {
            const video = card.querySelector('video');
            if (video) {
                video.currentTime = 0;
                video.play();
            }
        });
        card.addEventListener('mouseleave', () => {
            const video = card.querySelector('video');
            if (video) video.pause();
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

    // Lazy load background images/videos below fold
    const lazyVideos = document.querySelectorAll('video[data-src]');
    const videoObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const video = entry.target;
                video.src = video.dataset.src;
                video.load();
                videoObserver.unobserve(video);
            }
        });
    });
    lazyVideos.forEach(video => videoObserver.observe(video));
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

