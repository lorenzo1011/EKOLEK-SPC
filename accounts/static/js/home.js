/**
 * Home page functionality for E-KOLEK landing page
 */

(function() {
  'use strict';

  /**
   * Handle Get Started button click
   * Checks if user is authenticated and redirects accordingly
   */
  function handleGetStarted() {
    // Check if user is authenticated by checking for session/cookies
    // Since this is a public landing page, redirect to registration
    
    // Show loading state
    const buttons = document.querySelectorAll('.btn-primary');
    buttons.forEach(btn => {
      btn.style.opacity = '0.7';
      btn.style.cursor = 'wait';
    });

    // Redirect to registration page after brief delay for UX
    setTimeout(() => {
      window.location.href = '/register/';
    }, 200);
  }

  /**
   * Smooth scroll to sections
   */
  function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function(e) {
        const targetId = this.getAttribute('href');
        if (targetId === '#') return;
        
        const targetElement = document.querySelector(targetId);
        if (targetElement) {
          e.preventDefault();
          targetElement.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }
      });
    });
  }

  /**
   * Add scroll animations for better UX
   */
  function initScrollAnimations() {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('fade-in-visible');
        }
      });
    }, observerOptions);

    // Observe benefit cards
    document.querySelectorAll('.benefit-card').forEach(card => {
      card.classList.add('fade-in');
      observer.observe(card);
    });
  }

  /**
   * Initialize mobile menu toggle
   */
  function initMobileMenu() {
    const hamburger = document.querySelector('.hamburger-menu');
    const mobileNav = document.querySelector('.mobile-nav');
    
    if (hamburger && mobileNav) {
      // Toggle menu visibility
      window.toggleMobileMenu = function() {
        hamburger.classList.toggle('active');
        mobileNav.classList.toggle('active');
        
        // Prevent body scroll when menu is open
        if (mobileNav.classList.contains('active')) {
          document.body.style.overflow = 'hidden';
        } else {
          document.body.style.overflow = '';
        }
      };
      
      // Close menu when clicking a link
      mobileNav.querySelectorAll('a, button').forEach(item => {
        item.addEventListener('click', function() {
          hamburger.classList.remove('active');
          mobileNav.classList.remove('active');
          document.body.style.overflow = '';
        });
      });
      
      // Close menu when clicking outside
      document.addEventListener('click', function(event) {
        const isClickInside = hamburger.contains(event.target) || mobileNav.contains(event.target);
        if (!isClickInside && mobileNav.classList.contains('active')) {
          hamburger.classList.remove('active');
          mobileNav.classList.remove('active');
          document.body.style.overflow = '';
        }
      });
    }
  }

  /**
   * Initialize image carousel for the landing page showcase
   */
  function initImpactCarousel() {
    const carousel = document.querySelector('[data-carousel]');
    if (!carousel) return;

    const track = carousel.querySelector('[data-carousel-track]');
    const slides = Array.from(carousel.querySelectorAll('[data-slide]'));
    const previousButton = carousel.querySelector('[data-carousel-prev]');
    const nextButton = carousel.querySelector('[data-carousel-next]');
    const dots = Array.from(carousel.querySelectorAll('[data-slide-to]'));
    const viewport = carousel.querySelector('.impact-carousel-viewport');
    const counter = carousel.querySelector('[data-carousel-counter]');
    const progressBar = carousel.querySelector('[data-carousel-progress]');
    const captionTitle = carousel.querySelector('[data-carousel-caption-title]');
    const captionText = carousel.querySelector('[data-carousel-caption-text]');
    const prefersReducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (!track || !viewport || slides.length === 0 || !previousButton || !nextButton || dots.length !== slides.length) {
      return;
    }

    let currentIndex = 0;
    let autoplayTimer = null;
    let touchStartX = 0;
    let touchDeltaX = 0;

    const autoplayDelay = 4800;
    const swipeThreshold = 45;

    function formatCounterNumber(index) {
      return String(index + 1).padStart(2, '0');
    }

    function updateCarouselDetails() {
      const activeSlide = slides[currentIndex];
      if (!activeSlide) return;

      const activeImage = activeSlide.querySelector('img');
      const totalSlides = slides.length;

      if (counter) {
        counter.textContent = `${formatCounterNumber(currentIndex)} / ${String(totalSlides).padStart(2, '0')}`;
      }

      if (progressBar) {
        const progress = ((currentIndex + 1) / totalSlides) * 100;
        progressBar.style.width = `${progress}%`;
      }

      if (captionTitle || captionText) {
        const title = activeSlide.getAttribute('data-slide-title') || 'Community Impact Story';
        const description = activeSlide.getAttribute('data-slide-text') || (activeImage ? activeImage.getAttribute('alt') || '' : '');

        if (captionTitle) {
          captionTitle.textContent = title;
        }

        if (captionText) {
          captionText.textContent = description;
        }
      }
    }

    function updateViewportAspectRatio(slideIndex) {
      const activeSlide = slides[slideIndex];
      if (!activeSlide) return;

      const activeImage = activeSlide.querySelector('img');
      if (!activeImage) return;

      const applyAspectRatio = () => {
        if (!activeImage.naturalWidth || !activeImage.naturalHeight) return;

        // Keep the ratio in a practical range to avoid large layout jumps between slides.
        const rawRatio = activeImage.naturalWidth / activeImage.naturalHeight;
        const constrainedRatio = Math.min(1.9, Math.max(1.05, rawRatio));
        viewport.style.setProperty('--impact-slide-ratio', constrainedRatio.toFixed(3));
      };

      if (activeImage.complete) {
        applyAspectRatio();
      } else {
        activeImage.addEventListener('load', applyAspectRatio, { once: true });
      }
    }

    function updateCarouselUI() {
      track.style.transform = `translateX(-${currentIndex * 100}%)`;

      slides.forEach((slide, index) => {
        slide.classList.toggle('is-active', index === currentIndex);
      });

      dots.forEach((dot, index) => {
        const isActive = index === currentIndex;
        dot.classList.toggle('is-active', isActive);
        dot.setAttribute('aria-current', isActive ? 'true' : 'false');
      });

      updateCarouselDetails();
      updateViewportAspectRatio(currentIndex);
    }

    function goToSlide(targetIndex) {
      const totalSlides = slides.length;

      if (targetIndex < 0) {
        currentIndex = totalSlides - 1;
      } else if (targetIndex >= totalSlides) {
        currentIndex = 0;
      } else {
        currentIndex = targetIndex;
      }

      updateCarouselUI();
    }

    function goToNextSlide() {
      goToSlide(currentIndex + 1);
    }

    function goToPreviousSlide() {
      goToSlide(currentIndex - 1);
    }

    function stopAutoplay() {
      if (autoplayTimer) {
        window.clearInterval(autoplayTimer);
        autoplayTimer = null;
      }
    }

    function startAutoplay() {
      if (prefersReducedMotion) return;

      stopAutoplay();
      autoplayTimer = window.setInterval(() => {
        goToNextSlide();
      }, autoplayDelay);
    }

    function restartAutoplay() {
      startAutoplay();
    }

    previousButton.addEventListener('click', () => {
      goToPreviousSlide();
      restartAutoplay();
    });

    nextButton.addEventListener('click', () => {
      goToNextSlide();
      restartAutoplay();
    });

    dots.forEach((dot, index) => {
      dot.addEventListener('click', () => {
        goToSlide(index);
        restartAutoplay();
      });
    });

    carousel.setAttribute('tabindex', '0');
    carousel.addEventListener('keydown', (event) => {
      if (event.key === 'ArrowLeft') {
        event.preventDefault();
        goToPreviousSlide();
        restartAutoplay();
      }

      if (event.key === 'ArrowRight') {
        event.preventDefault();
        goToNextSlide();
        restartAutoplay();
      }
    });

    carousel.addEventListener('mouseenter', stopAutoplay);
    carousel.addEventListener('mouseleave', startAutoplay);

    carousel.addEventListener('focusin', stopAutoplay);
    carousel.addEventListener('focusout', (event) => {
      if (!carousel.contains(event.relatedTarget)) {
        startAutoplay();
      }
    });

    viewport.addEventListener('touchstart', (event) => {
      touchStartX = event.touches[0].clientX;
      touchDeltaX = 0;
      stopAutoplay();
    }, { passive: true });

    viewport.addEventListener('touchmove', (event) => {
      touchDeltaX = event.touches[0].clientX - touchStartX;
    }, { passive: true });

    viewport.addEventListener('touchend', () => {
      if (Math.abs(touchDeltaX) > swipeThreshold) {
        if (touchDeltaX < 0) {
          goToNextSlide();
        } else {
          goToPreviousSlide();
        }
      }

      startAutoplay();
    });

    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        stopAutoplay();
      } else {
        startAutoplay();
      }
    });

    if (prefersReducedMotion) {
      track.style.transition = 'none';
    }

    updateCarouselUI();
    startAutoplay();
  }

  /**
   * Initialize all functionality when DOM is ready
   */
  document.addEventListener('DOMContentLoaded', function() {
    // Make handleGetStarted globally accessible
    window.handleGetStarted = handleGetStarted;
    
    // Initialize smooth scrolling
    initSmoothScroll();
    
    // Initialize scroll animations
    initScrollAnimations();
    
    // Initialize mobile menu
    initMobileMenu();

    // Initialize image carousel
    initImpactCarousel();

    console.log('E-KOLEK landing page initialized');
  });

  // Prevent back button issues (keep existing functionality)
  window.history.pushState(null, '', window.location.href);
  window.onpopstate = function() {
    window.history.go(1);
  };

})();
