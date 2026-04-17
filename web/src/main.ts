/*
  Entry point for the frontend web application.
*/
import { registerRoute, initRouter, registerNotFound, navigate } from "./router.js";
import { mountForm } from "./form.js";
import { 
  showLanding,
  showForm,
  showAPI,
  showUnknown,
  showFormSubmitted,
  mountFormSubmittedView,
} from "./views.js";
import { mountFormInterceptor } from "./form_interceptor.js";


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
  mountFormInterceptor();
});

registerRoute("/form/submitted", () => {
  showFormSubmitted();
  mountFormSubmittedView();
});

registerRoute("/api", showAPI);

registerNotFound(showUnknown);

initRouter();
