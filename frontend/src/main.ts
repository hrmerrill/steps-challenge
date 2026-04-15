/**
 * Steps Challenge — App entry point.
 * Sets up routing and mounts the application.
 */

import { renderNav } from "./components/nav";
import { addRoute, initRouter } from "./router";
import { renderLanding } from "./pages/landing";
import { renderLogin } from "./pages/login";
import { renderRegister } from "./pages/register";
import { renderLogSteps } from "./pages/log-steps";
import { renderProfile } from "./pages/profile";
import { isAuthenticated, fetchMe } from "./auth";
import "./styles/global.css";
import "./styles/cards.css";
import "./styles/components.css";

async function boot(): Promise<void> {
  const appEl = document.getElementById("app");
  if (!appEl) return;

  // Layout: nav + content
  appEl.innerHTML = `
    <div id="nav-container"></div>
    <main id="content"></main>
  `;

  const navEl = document.getElementById("nav-container")!;
  const contentEl = document.getElementById("content")!;

  // If we have a token, try to fetch the user profile
  if (isAuthenticated()) {
    try {
      await fetchMe();
    } catch {
      // Token expired — will redirect to login
    }
  }

  // Re-render nav on every route change
  const withNav = (handler: (el: HTMLElement) => void | Promise<void>) => {
    return (el: HTMLElement) => {
      renderNav(navEl);
      return handler(el);
    };
  };

  addRoute("/", withNav(renderLanding));
  addRoute("/login", withNav(renderLogin));
  addRoute("/register", withNav(renderRegister));
  addRoute("/log", withNav(renderLogSteps));
  addRoute("/profile", withNav(renderProfile));

  initRouter(contentEl);
}

boot();
