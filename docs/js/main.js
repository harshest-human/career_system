/**
 * AYUSH SAHU — CAREER PORTFOLIO
 * Interactive Controller & Dynamic Behaviors
 */

document.addEventListener('DOMContentLoaded', () => {
  initNavbar();
  initTheme();
  initTimeline();
  initCounters();
  initGalleryFilters();
  initLightbox();
  initCvModal();
  initSmoothScroll();
});

/* ==========================================================================
   1. Navbar & Scroll-Spy
   ========================================================================== */
function initNavbar() {
  const navbar = document.getElementById('navbar');
  const mobileToggle = document.getElementById('mobileToggle');
  const navMenu = document.getElementById('navMenu');
  const navLinks = document.querySelectorAll('.nav-link');

  // Sticky navbar shadow on scroll
  window.addEventListener('scroll', () => {
    if (window.scrollY > 40) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  });

  // Mobile menu toggle
  if (mobileToggle && navMenu) {
    mobileToggle.addEventListener('click', () => {
      navMenu.classList.toggle('open');
      const isOpen = navMenu.classList.contains('open');
      mobileToggle.innerHTML = isOpen ? '✕' : '☰';
    });

    // Close mobile menu on link click
    navLinks.forEach(link => {
      link.addEventListener('click', () => {
        navMenu.classList.remove('open');
        mobileToggle.innerHTML = '☰';
      });
    });
  }

  // Active section scroll spy
  const sections = document.querySelectorAll('section[id]');
  window.addEventListener('scroll', () => {
    const scrollY = window.pageYOffset;
    sections.forEach(current => {
      const sectionHeight = current.offsetHeight;
      const sectionTop = current.offsetTop - 120;
      const sectionId = current.getAttribute('id');
      const matchingLink = document.querySelector(`.nav-link[href*="${sectionId}"]`);
      
      if (matchingLink) {
        if (scrollY > sectionTop && scrollY <= sectionTop + sectionHeight) {
          matchingLink.classList.add('active');
        } else {
          matchingLink.classList.remove('active');
        }
      }
    });
  });
}

/* ==========================================================================
   2. Theme Switcher (Dark / Light)
   ========================================================================== */
function initTheme() {
  const themeToggle = document.getElementById('themeToggle');
  const savedTheme = localStorage.getItem('theme') || 'dark';

  document.documentElement.setAttribute('data-theme', savedTheme);
  updateThemeIcon(savedTheme);

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme');
      const newTheme = currentTheme === 'light' ? 'dark' : 'light';
      
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('theme', newTheme);
      updateThemeIcon(newTheme);
    });
  }

  function updateThemeIcon(theme) {
    if (!themeToggle) return;
    themeToggle.innerHTML = theme === 'light' ? '🌙' : '☀️';
    themeToggle.setAttribute('title', theme === 'light' ? 'Switch to Dark Mode' : 'Switch to Light Mode');
  }
}

/* ==========================================================================
   3. Interactive Timeline
   ========================================================================== */
function initTimeline() {
  const nodes = document.querySelectorAll('.timeline-node');

  nodes.forEach(node => {
    node.addEventListener('click', (e) => {
      // Toggle current node
      const isActive = node.classList.contains('active');
      
      // Close all other nodes for clean focus
      nodes.forEach(n => {
        n.classList.remove('active');
        const btn = n.querySelector('.timeline-expand-btn');
        if (btn) btn.innerHTML = 'Click to expand details ↓';
      });

      if (!isActive) {
        node.classList.add('active');
        const btn = node.querySelector('.timeline-expand-btn');
        if (btn) btn.innerHTML = 'Show less ↑';
      }
    });
  });
}

/* ==========================================================================
   4. Animated Number Counters
   ========================================================================== */
function initCounters() {
  const counters = document.querySelectorAll('[data-counter]');
  let hasAnimated = false;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting && !hasAnimated) {
        hasAnimated = true;
        counters.forEach(counter => {
          const target = parseFloat(counter.getAttribute('data-counter'));
          const prefix = counter.getAttribute('data-prefix') || '';
          const suffix = counter.getAttribute('data-suffix') || '';
          const duration = 1500;
          const start = 0;
          const startTime = performance.now();

          function updateCounter(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const currentVal = Math.floor(start + (target - start) * easeOut);

            counter.textContent = `${prefix}${currentVal}${suffix}`;

            if (progress < 1) {
              requestAnimationFrame(updateCounter);
            } else {
              counter.textContent = `${prefix}${target}${suffix}`;
            }
          }

          requestAnimationFrame(updateCounter);
        });
      }
    });
  }, { threshold: 0.3 });

  const counterSection = document.querySelector('.counters-banner') || document.querySelector('.hero-stats');
  if (counterSection) {
    observer.observe(counterSection);
  }
}

/* ==========================================================================
   5. Gallery Filtering
   ========================================================================== */
function initGalleryFilters() {
  const filterBtns = document.querySelectorAll('.filter-btn');
  const galleryCards = document.querySelectorAll('.gallery-card');

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const filterValue = btn.getAttribute('data-filter');

      galleryCards.forEach(card => {
        const cardCategory = card.getAttribute('data-category');
        if (filterValue === 'all' || cardCategory === filterValue) {
          card.style.display = 'block';
          setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'scale(1)';
          }, 50);
        } else {
          card.style.opacity = '0';
          card.style.transform = 'scale(0.95)';
          setTimeout(() => {
            card.style.display = 'none';
          }, 250);
        }
      });
    });
  });
}

/* ==========================================================================
   6. Interactive Lightbox Modal
   ========================================================================== */
function initLightbox() {
  const lightboxModal = document.getElementById('lightboxModal');
  const lightboxImg = document.getElementById('lightboxImg');
  const lightboxTitle = document.getElementById('lightboxTitle');
  const lightboxSub = document.getElementById('lightboxSub');
  const lightboxClose = document.getElementById('lightboxClose');

  if (!lightboxModal) return;

  const triggerElements = document.querySelectorAll('[data-lightbox]');

  triggerElements.forEach(el => {
    el.addEventListener('click', () => {
      const imgSrc = el.getAttribute('data-img') || el.querySelector('img')?.getAttribute('src');
      const title = el.getAttribute('data-title') || el.querySelector('.gallery-title')?.textContent || 'Gallery Photo';
      const caption = el.getAttribute('data-caption') || el.querySelector('.gallery-caption')?.textContent || '';

      if (imgSrc) {
        lightboxImg.src = imgSrc;
        lightboxTitle.textContent = title;
        lightboxSub.textContent = caption;
        lightboxModal.classList.add('active');
        document.body.style.overflow = 'hidden';
      }
    });
  });

  function closeLightbox() {
    lightboxModal.classList.remove('active');
    document.body.style.overflow = 'auto';
  }

  lightboxClose?.addEventListener('click', closeLightbox);
  
  lightboxModal.addEventListener('click', (e) => {
    if (e.target === lightboxModal) {
      closeLightbox();
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && lightboxModal.classList.contains('active')) {
      closeLightbox();
    }
  });
}

/* ==========================================================================
   7. CV Download & Preview Modal
   ========================================================================== */
function initCvModal() {
  const cvModal = document.getElementById('cvModal');
  const cvButtons = document.querySelectorAll('[data-open-cv]');
  const cvClose = document.getElementById('cvClose');

  if (!cvModal) return;

  cvButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      cvModal.classList.add('active');
      document.body.style.overflow = 'hidden';
    });
  });

  function closeCv() {
    cvModal.classList.remove('active');
    document.body.style.overflow = 'auto';
  }

  cvClose?.addEventListener('click', closeCv);

  cvModal.addEventListener('click', (e) => {
    if (e.target === cvModal) {
      closeCv();
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && cvModal.classList.contains('active')) {
      closeCv();
    }
  });
}

/* ==========================================================================
   8. Smooth Scrolling
   ========================================================================== */
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      
      const targetElement = document.querySelector(targetId);
      if (targetElement) {
        e.preventDefault();
        const headerOffset = 70;
        const elementPosition = targetElement.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

        window.scrollTo({
          top: offsetPosition,
          behavior: 'smooth'
        });
      }
    });
  });
}
