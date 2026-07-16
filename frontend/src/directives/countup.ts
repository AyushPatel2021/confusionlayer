import type { Directive } from "vue";

// Count a number up from 0 to the bound value when it scrolls into view.
// Usage: <span v-countup="12" data-suffix="+">12</span>
export const countup: Directive<HTMLElement, number> = {
  mounted(el, binding) {
    const target = Number(binding.value) || 0;
    const suffix = el.dataset.suffix ?? "";
    const prefix = el.dataset.prefix ?? "";
    const render = (n: number) => (el.textContent = `${prefix}${n}${suffix}`);

    const reduce = typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce || typeof IntersectionObserver === "undefined") {
      render(target);
      return;
    }
    render(0);

    const run = () => {
      const duration = 1100;
      const start = performance.now();
      const tick = (now: number) => {
        const t = Math.min(1, (now - start) / duration);
        const eased = 1 - Math.pow(1 - t, 3);
        render(Math.round(eased * target));
        if (t < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    };

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            run();
            observer.unobserve(el);
          }
        }
      },
      { threshold: 0.5 },
    );
    observer.observe(el);
  },
};
