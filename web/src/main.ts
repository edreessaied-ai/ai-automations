/*
  Entry point for the frontend web application.
*/
import { registerRoute, initRouter, registerNotFound, navigate } from "./router.js";
import { mountForm } from "./form.js";
import { showLanding, showForm, showSlack, showAPI, showUnknown } from "./views.js";


(window as any).navigate = navigate;

function attachNavigation() {
  document.querySelectorAll<HTMLElement>("[data-nav]").forEach(el => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      const path = el.dataset.nav;
      if (path) navigate(path);
    });
  });
}

window.addEventListener("DOMContentLoaded", () => {
  attachNavigation();
});

registerRoute("/", showLanding);

registerRoute("/form", () => {
  showForm();
  mountForm();
});

registerRoute("/slack", showSlack);
registerRoute("/api", showAPI);

registerNotFound(showUnknown);

initRouter();
