import type { Directive } from "vue";

// Lightweight scroll-reveal (no dependency). Elements fade/slide in when they
// enter the viewport once. Honors prefers-reduced-motion by showing immediately.
export const reveal: Directive<HTMLElement> = {
  mounted(el) {
    el.classList.add("reveal");
    const reduce = typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce || typeof IntersectionObserver === "undefined") {
      el.classList.add("reveal-in");
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            el.classList.add("reveal-in");
            observer.unobserve(el);
          }
        }
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" },
    );
    observer.observe(el);
  },
};
