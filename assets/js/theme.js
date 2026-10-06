(function () {
  var button = document.querySelector("[data-theme-switch]");
  if (!button) return;

  // The control exists only when it works. Shipped hidden, revealed here: a
  // button that does nothing is worse than no button, because a reader cannot
  // tell it apart from a broken page.
  button.hidden = false;

  button.addEventListener("click", function () {
    // Read the COMPUTED state, not the stored one. A reader who has never
    // chosen has nothing stored, so toggling from "no choice, system is dark"
    // has to produce light. Flipping a stored value gets that wrong on the
    // first press.
    var dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    var chosen = document.documentElement.getAttribute("data-theme");
    var current = chosen || (dark ? "dark" : "light");
    var next = current === "dark" ? "light" : "dark";
    var systemWants = dark ? "dark" : "light";

    if (next === systemWants) {
      // The reader has arrived back at what their system already prefers.
      // Recording that would pin them to it: the stored value sets data-theme
      // on every load, and the prefers-color-scheme rule can then never match
      // again. So this is the way back to following the system, using the same
      // control, which is otherwise a one-way door.
      document.documentElement.removeAttribute("data-theme");
      try {
        localStorage.removeItem("nivis-theme");
      } catch (e) {
        // Private window, or site data blocked. Nothing was stored to remove.
      }
      return;
    }

    document.documentElement.setAttribute("data-theme", next);
    try {
      localStorage.setItem("nivis-theme", next);
    } catch (e) {
      // Private window, or site data blocked. The choice is not remembered,
      // which is the correct degradation; the page still works.
    }
  });
})();
