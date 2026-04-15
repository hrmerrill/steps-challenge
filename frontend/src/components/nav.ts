/**
 * Navigation bar component.
 */

import { isAuthenticated, logout, getCurrentUser } from "../auth";
import { navigate } from "../router";

export function renderNav(container: HTMLElement): void {
  const user = getCurrentUser();
  const authed = isAuthenticated();

  container.innerHTML = `
    <nav class="nav">
      <a href="#/" class="nav-brand">Carbon Steps Challenge</a>
      <ul class="nav-links">
        ${authed ? `
          <li><a href="#/">Dashboard</a></li>
          <li><a href="#/log">Log Steps</a></li>
          <li><a href="#/profile" class="nav-user">${user?.display_name ?? "User"}</a></li>
          <li><button class="btn btn-secondary" id="logout-btn">Logout</button></li>
        ` : `
          <li><a href="#/login">Login</a></li>
          <li><a href="#/register" class="btn btn-primary">Sign Up</a></li>
        `}
        <li><button class="theme-toggle" id="theme-toggle-btn" title="Toggle dark/light mode">Dark</button></li>
      </ul>
    </nav>
  `;

  const logoutBtn = container.querySelector("#logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      logout();
      navigate("/login");
    });
  }

  // Theme toggle
  const themeBtn = container.querySelector("#theme-toggle-btn")!;
  const currentTheme = document.documentElement.getAttribute("data-theme");
  themeBtn.textContent = currentTheme === "dark" ? "Light" : "Dark";
  themeBtn.addEventListener("click", () => {
    const isDark = document.documentElement.getAttribute("data-theme") === "dark";
    const next = isDark ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
    themeBtn.textContent = next === "dark" ? "Light" : "Dark";
  });
}
