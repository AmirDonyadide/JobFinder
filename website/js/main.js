/* ===========================================================================
   JobFinder website — interactivity
   Vanilla JS, no dependencies. Every handler guards for missing elements so
   the same script can power both index.html and developers.html.
   =========================================================================== */
(function () {
  "use strict";

  /* ---- Theme (light / dark) with persistence --------------------------- */
  var root = document.documentElement;
  var stored = null;
  try { stored = localStorage.getItem("jf-theme"); } catch (e) {}
  if (stored) {
    root.setAttribute("data-theme", stored);
  } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
    root.setAttribute("data-theme", "dark");
  }
  var themeToggle = document.getElementById("themeToggle");
  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("jf-theme", next); } catch (e) {}
    });
  }

  /* ---- Mobile navigation ------------------------------------------------ */
  var nav = document.getElementById("nav");
  var navToggle = document.getElementById("navToggle");
  if (nav && navToggle) {
    navToggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      navToggle.setAttribute("aria-expanded", String(open));
    });
    // Close the menu after tapping a link
    var navLinks = document.getElementById("navLinks");
    if (navLinks) {
      navLinks.addEventListener("click", function (e) {
        if (e.target.tagName === "A") {
          nav.classList.remove("open");
          navToggle.setAttribute("aria-expanded", "false");
        }
      });
    }
  }

  /* ---- Copy buttons ----------------------------------------------------- */
  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }
    // Fallback for non-secure contexts
    return new Promise(function (resolve, reject) {
      try {
        var ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
        resolve();
      } catch (err) { reject(err); }
    });
  }

  document.querySelectorAll(".code .copy").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var pre = btn.parentElement.querySelector("pre");
      if (!pre) return;
      copyText(pre.innerText.trim()).then(function () {
        var original = btn.textContent;
        btn.classList.add("copied");
        btn.textContent = "Copied!";
        setTimeout(function () {
          btn.classList.remove("copied");
          btn.textContent = original;
        }, 1600);
      });
    });
  });

  /* ---- Tabs ------------------------------------------------------------- */
  document.querySelectorAll(".tabs__btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var targetId = btn.getAttribute("data-tab");
      var list = btn.closest(".tabs__list");
      if (list) {
        list.querySelectorAll(".tabs__btn").forEach(function (b) {
          b.classList.remove("is-active");
          b.setAttribute("aria-selected", "false");
        });
      }
      btn.classList.add("is-active");
      btn.setAttribute("aria-selected", "true");
      document.querySelectorAll(".tabs__panel").forEach(function (panel) {
        panel.classList.toggle("is-active", panel.id === targetId);
      });
    });
  });

  /* ---- FAQ accordion ---------------------------------------------------- */
  document.querySelectorAll(".acc-trigger").forEach(function (trigger) {
    trigger.addEventListener("click", function () {
      var panel = trigger.nextElementSibling;
      var expanded = trigger.getAttribute("aria-expanded") === "true";
      trigger.setAttribute("aria-expanded", String(!expanded));
      if (panel) {
        panel.style.maxHeight = expanded ? null : panel.scrollHeight + "px";
      }
    });
  });

  /* ---- Command builder -------------------------------------------------- */
  var bAction = document.getElementById("bAction");
  var bSource = document.getElementById("bSource");
  var builderOut = document.getElementById("builderOut");
  if (bAction && bSource && builderOut) {
    var render = function () {
      var src = bSource.value;
      var sourcesEnv = "JOBFINDER_SCRAPER_SOURCES=" + src + " ";
      var cmd;
      switch (bAction.value) {
        case "excel":
          cmd = sourcesEnv + "JOBFINDER_SCRAPER_OUTPUT_MODE=excel python linkedin_job_scraper.py";
          break;
        case "sheets":
          cmd = sourcesEnv + "python run_job_pipeline.py --mode scrape_only";
          break;
        case "evaluate":
          cmd = sourcesEnv + "python run_job_pipeline.py --mode scrape_and_evaluate";
          break;
        default:
          cmd = sourcesEnv + "python linkedin_job_scraper.py";
      }
      builderOut.textContent = cmd;
    };
    bAction.addEventListener("change", render);
    bSource.addEventListener("change", render);
    render();
  }

  /* ---- Reveal on scroll ------------------------------------------------- */
  var reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && reveals.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("in");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add("in"); });
  }

  /* ---- Scroll-spy (highlight active nav link) --------------------------- */
  var spyLinks = Array.prototype.slice.call(
    document.querySelectorAll('.nav__links a[href^="#"]')
  );
  if (spyLinks.length && "IntersectionObserver" in window) {
    var byId = {};
    spyLinks.forEach(function (link) {
      var id = link.getAttribute("href").slice(1);
      var sec = document.getElementById(id);
      if (sec) byId[id] = link;
    });
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          spyLinks.forEach(function (l) { l.classList.remove("is-active"); });
          var active = byId[entry.target.id];
          if (active) active.classList.add("is-active");
        }
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    Object.keys(byId).forEach(function (id) {
      spy.observe(document.getElementById(id));
    });
  }

  /* ---- Footer year ------------------------------------------------------ */
  var yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());
})();
