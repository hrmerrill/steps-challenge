/**
 * Simple client-side router — hash-based routing.
 * Maps URL hashes (#/login, #/register, etc.) to page render functions.
 */

export type RouteHandler = (container: HTMLElement) => void | Promise<void>;

const routes = new Map<string, RouteHandler>();

/** Register a route. */
export function addRoute(path: string, handler: RouteHandler): void {
  routes.set(path, handler);
}

/** Navigate to a route programmatically. */
export function navigate(path: string): void {
  window.location.hash = path;
}

/** Get current route path from hash. */
export function currentRoute(): string {
  return window.location.hash.slice(1) || "/";
}

/** Initialize the router — listens to hashchange events. */
export function initRouter(container: HTMLElement): void {
  const handleRoute = () => {
    const path = currentRoute();
    const handler = routes.get(path) ?? routes.get("*");
    if (handler) {
      handler(container);
    } else {
      container.innerHTML = `<div class="card"><h2>404</h2><p>Page not found</p></div>`;
    }
  };

  window.addEventListener("hashchange", handleRoute);
  handleRoute();
}
