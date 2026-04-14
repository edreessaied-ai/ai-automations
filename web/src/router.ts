/*
* Utility to manage client-side routing for frontend.
*/

type RouteHandler = () => void;
const routes: Record<string, RouteHandler> = {};

let notFoundHandler: RouteHandler = () => {};

export function registerRoute(path: string, handler: RouteHandler) {
  routes[path] = handler;
}

export function registerNotFound(handler: RouteHandler) {
  notFoundHandler = handler;
}

export function navigate(path: string) {
  history.pushState({}, "", path);
  router();
}

export function router() {
  const path = window.location.pathname;
  const handler = routes[path];

  if (handler) {
    handler();
  } else {
    notFoundHandler();
  }
}

export function initRouter() {
  window.addEventListener("popstate", router);
  router();
}