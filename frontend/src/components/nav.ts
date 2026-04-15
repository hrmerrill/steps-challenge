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
      <a href="#/" class="nav-brand">🚶 Steps Challenge</a>
      <ul class="nav-links">
        ${authed ? `
          <li><a href="#/">Dashboard</a></li>
          <li><a href="#/log">Log Steps</a></li>
          <li><span class="nav-user">${user?.display_name ?? "User"}</span></li>
          <li><button class="btn btn-secondary" id="logout-btn">Logout</button></li>
        ` : `
          <li><a href="#/login">Login</a></li>
          <li><a href="#/register" class="btn btn-primary">Sign Up</a></li>
        `}
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
}
