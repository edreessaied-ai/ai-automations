/*
  Entry point for the frontend web application.
*/
import { registerRoute, initRouter, registerNotFound, navigate } from "./router";
import { mountForm } from "./form";
import { showLanding, showForm, showSlack, showAPI, showUnknown } from "./views";


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

registerRoute("/", showLanding);

registerRoute("/form", () => {
  showForm();
  mountForm();
});

registerRoute("/slack", showSlack);
registerRoute("/api", showAPI);

registerNotFound(showUnknown);

initRouter();

window.addEventListener("DOMContentLoaded", () => {
  attachNavigation();
});
