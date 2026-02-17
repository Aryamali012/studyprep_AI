/* ============================================================
   auth.js  –  StudyPrep AI
   Full JWT auth with silent refresh token rotation.

   Token strategy
   ──────────────
   access_token   – short-lived JWT (15 min). Stored in memory AND
                    localStorage as fallback for page reloads.
   refresh_token  – opaque 30-day token. Stored in localStorage.
                    Rotated on every /refresh call.

   Silent refresh
   ──────────────
   1. On page load, if access token is expired/missing but refresh
      token exists → silently call /refresh before doing anything.
   2. A proactive timer fires 60 s before access token expiry to
      refresh in the background while the user is still active.
   3. Any 401 with code "TOKEN_EXPIRED" from any API call triggers
      one automatic /refresh attempt, then retries the original request.
   4. If /refresh itself fails (expired or revoked) → redirect to login.
   ============================================================ */

const API_BASE = "http://localhost:5000";

// In-memory store for the current access token
// (avoids repeated localStorage reads and keeps it off the DOM)
let _accessToken = localStorage.getItem("access_token") || null;
let _refreshTimer = null;


// ─── Session storage ──────────────────────────────────────────────────────────

function saveSession(accessToken, refreshToken, user) {
    _accessToken = accessToken;
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("refresh_token", refreshToken);
    localStorage.setItem("userId", user.user_id);
    localStorage.setItem("userName", user.full_name);
    localStorage.setItem("userEmail", user.email);
    _scheduleProactiveRefresh(accessToken);
}

function updateTokens(accessToken, refreshToken) {
    _accessToken = accessToken;
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("refresh_token", refreshToken);
    _scheduleProactiveRefresh(accessToken);
}

function clearSession() {
    _accessToken = null;
    if (_refreshTimer) clearTimeout(_refreshTimer);
    ["access_token", "refresh_token", "userId", "userName", "userEmail"]
        .forEach(k => localStorage.removeItem(k));
}

// ─── JWT expiry helpers ───────────────────────────────────────────────────────

function _parseJwtPayload(token) {
    try {
        const base64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
        return JSON.parse(atob(base64));
    } catch {
        return null;
    }
}

function _tokenExpiresInMs(token) {
    const payload = _parseJwtPayload(token);
    if (!payload || !payload.exp) return 0;
    return payload.exp * 1000 - Date.now();
}

function _isTokenExpired(token) {
    return !token || _tokenExpiresInMs(token) <= 0;
}

/**
 * Schedule a silent refresh 60 seconds before the access token expires.
 * Clears any existing timer first.
 */
function _scheduleProactiveRefresh(accessToken) {
    if (_refreshTimer) clearTimeout(_refreshTimer);
    const msLeft = _tokenExpiresInMs(accessToken);
    const fireIn = Math.max(msLeft - 60_000, 0);   // 60 s before expiry

    if (fireIn > 0) {
        _refreshTimer = setTimeout(async () => {
            console.debug("[Auth] Proactive token refresh triggered.");
            await silentRefresh();
        }, fireIn);
    }
}

// ─── Core API: silent refresh ─────────────────────────────────────────────────

/**
 * Exchange the stored refresh token for a new token pair.
 * Returns true on success, false if the session is dead (user must re-login).
 */
async function silentRefresh() {
    const rawRt = localStorage.getItem("refresh_token");
    if (!rawRt) return false;

    try {
        const res = await fetch(`${API_BASE}/refresh`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh_token: rawRt }),
        });
        const data = await res.json();
        if (!res.ok) {
            console.warn("[Auth] Refresh failed:", data.error);
            clearSession();
            return false;
        }
        updateTokens(data.access_token, data.refresh_token);
        return true;
    } catch (err) {
        console.error("[Auth] Refresh network error:", err);
        return false;
    }
}

// ─── Auth guard ───────────────────────────────────────────────────────────────

/**
 * Call on every protected page.
 * 1. If access token is fine → return true immediately.
 * 2. If expired but refresh token exists → silently refresh → return true.
 * 3. Otherwise → redirect to login.
 */
async function checkAuth() {
    if (!_isTokenExpired(_accessToken)) return true;

    const refreshed = await silentRefresh();
    if (!refreshed) {
        window.location.href = "login.html";
        return false;
    }
    return true;
}

// ─── Smart fetch (auto-retry on 401 TOKEN_EXPIRED) ────────────────────────────

/**
 * Drop-in replacement for fetch() on protected endpoints.
 * Automatically injects Authorization header and retries once on TOKEN_EXPIRED.
 */
async function authFetch(url, options = {}) {
    // Ensure access token is fresh before the request
    if (_isTokenExpired(_accessToken)) {
        const ok = await silentRefresh();
        if (!ok) { window.location.href = "login.html"; throw new Error("Session expired."); }
    }

    const doRequest = () => fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {}),
            "Authorization": `Bearer ${_accessToken}`,
        },
    });

    let res = await doRequest();
    let data = await res.json().catch(() => ({}));

    // One automatic retry if the server says the token just expired
    if (res.status === 401 && data.code === "TOKEN_EXPIRED") {
        const ok = await silentRefresh();
        if (!ok) { window.location.href = "login.html"; throw new Error("Session expired."); }
        res = await doRequest();
        data = await res.json().catch(() => ({}));
    }

    if (!res.ok) throw Object.assign(new Error(data.error || "Request failed."), { data });
    return data;
}

// ─── Public API helpers ───────────────────────────────────────────────────────

async function apiRegister(full_name, email, password) {
    const res = await fetch(`${API_BASE}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ full_name, email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Registration failed.");
    return data;
}

async function apiLogin(email, password) {
    const res = await fetch(`${API_BASE}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Login failed.");
    return data;
}

async function apiGetMe() {
    return authFetch(`${API_BASE}/me`);
}

async function apiLogout(allDevices = false) {
    const rawRt = localStorage.getItem("refresh_token");
    if (rawRt) {
        await fetch(`${API_BASE}/logout`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh_token: rawRt, all_devices: allDevices }),
        }).catch(() => { });   // best-effort; always clear locally
    }
    clearSession();
    window.location.href = "login.html";
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function showMessage(el, text, type) {
    if (!el) return;
    el.textContent = text;
    el.className = "auth-message " + type;
    el.style.display = "block";
}

function setLoading(btn, label, loading) {
    if (loading) {
        btn.dataset.originalLabel = btn.textContent;
        btn.textContent = label;
        btn.disabled = true;
    } else {
        btn.textContent = btn.dataset.originalLabel || btn.textContent;
        btn.disabled = false;
    }
}

// ─── On page load: restore proactive refresh timer ────────────────────────────

if (_accessToken && !_isTokenExpired(_accessToken)) {
    _scheduleProactiveRefresh(_accessToken);
}

// ─── Nav / UI update based on auth state ──────────────────────────────────────

/**
 * Update the navigation bar on every page:
 *  • If logged in → hide Login / Sign Up btns, show user-profile pill + Logout
 *  • If not       → show Login / Sign Up btns (the default HTML state)
 * Also populates the dashboard user-info card if present.
 */
function updateNavForAuth() {
    const userName = localStorage.getItem("userName");
    const userEmail = localStorage.getItem("userEmail");
    const isLoggedIn = !!userName;

    // ── Nav buttons ──────────────────────────────────────────────────────────
    document.querySelectorAll(".nav-login-btn").forEach(el => {
        el.style.display = isLoggedIn ? "none" : "";
    });

    // Remove any previously injected profile elements (avoids duplicates)
    document.querySelectorAll(".nav-user-profile, .nav-logout-btn").forEach(el => el.remove());

    if (isLoggedIn) {
        // Find every .nav-links container and inject the profile pill + logout
        document.querySelectorAll(".nav-links").forEach(navLinks => {
            const themeBtn = navLinks.querySelector("#theme-toggle");

            // User profile pill
            const profile = document.createElement("span");
            profile.className = "nav-user-profile";
            profile.innerHTML = `<span class="nav-user-avatar">${userName.charAt(0)}</span>${userName.split(" ")[0]}`;

            // Logout button
            const logout = document.createElement("a");
            logout.href = "#";
            logout.className = "nav-logout-btn";
            logout.textContent = "Logout";
            logout.addEventListener("click", (e) => { e.preventDefault(); apiLogout(); });

            // Insert before the theme-toggle button
            if (themeBtn) {
                navLinks.insertBefore(profile, themeBtn);
                navLinks.insertBefore(logout, themeBtn);
            } else {
                navLinks.appendChild(profile);
                navLinks.appendChild(logout);
            }
        });

        // ── Update the "Get Started Free" hero CTA on home page ──────────────
        const heroBtn = document.querySelector(".hero .btn");
        if (heroBtn && heroBtn.textContent.trim() === "Get Started Free") {
            heroBtn.textContent = "Go to Dashboard";
            heroBtn.href = "dashboard.html";
        }
    }

    // ── Dashboard user-info card ─────────────────────────────────────────────
    const infoCard = document.getElementById("user-info-card");
    if (infoCard && isLoggedIn) {
        const initial = userName.charAt(0);
        infoCard.innerHTML = `
            <div class="user-info-avatar">${initial}</div>
            <h2>Welcome, ${userName}!</h2>
            <p class="user-email">📧 ${userEmail}</p>
            <span class="user-status">✅ Account Verified</span>
            <br>
            <button class="logout-btn" onclick="apiLogout()">Logout</button>
        `;
    }
}


// ─── DOMContentLoaded ─────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {

    // ── Update nav based on auth state ──────────────────────────────────────
    updateNavForAuth();

    // ── Password visibility toggle ──────────────────────────────────────────
    document.querySelectorAll(".password-toggle").forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.preventDefault();
            const input = btn.parentElement.querySelector("input");
            input.type = input.type === "password" ? "text" : "password";
            btn.textContent = input.type === "password" ? "👁️" : "🙈";
        });
    });

    // ── Password strength meter (signup only) ───────────────────────────────
    const passwordInput = document.getElementById("password");
    const strengthFill = document.querySelector(".strength-fill");
    const strengthText = document.querySelector(".strength-text");

    if (passwordInput && strengthFill) {
        passwordInput.addEventListener("input", () => {
            const result = checkPasswordStrength(passwordInput.value);
            strengthFill.style.width = result.percent + "%";
            strengthFill.style.background = result.color;
            if (strengthText) {
                strengthText.textContent = passwordInput.value ? result.label : "";
                strengthText.style.color = result.color;
            }
        });
    }

    function checkPasswordStrength(pw) {
        let s = 0;
        if (pw.length >= 6) s++;
        if (pw.length >= 10) s++;
        if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) s++;
        if (/\d/.test(pw)) s++;
        if (/[^a-zA-Z0-9]/.test(pw)) s++;
        return [
            { percent: 0, color: "#e2e8f0", label: "" },
            { percent: 20, color: "#f56565", label: "Very Weak" },
            { percent: 40, color: "#ed8936", label: "Weak" },
            { percent: 60, color: "#ecc94b", label: "Fair" },
            { percent: 80, color: "#48bb78", label: "Strong" },
            { percent: 100, color: "#38a169", label: "Very Strong" },
        ][Math.min(s, 5)];
    }

    // ── Login form ──────────────────────────────────────────────────────────
    const loginForm = document.getElementById("loginForm");
    if (loginForm) {
        const btn = loginForm.querySelector(".auth-submit");
        const msgEl = document.getElementById("authMessage");

        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const email = document.getElementById("email").value.trim();
            const password = document.getElementById("password").value;

            if (!email || !password) {
                showMessage(msgEl, "Please fill in all fields.", "error"); return;
            }
            if (!isValidEmail(email)) {
                showMessage(msgEl, "Please enter a valid email address.", "error"); return;
            }

            setLoading(btn, "Signing in…", true);
            try {
                const data = await apiLogin(email, password);
                saveSession(data.access_token, data.refresh_token, data.user);
                showMessage(msgEl, "✅ Login successful! Redirecting…", "success");
                setTimeout(() => window.location.href = "dashboard.html", 1200);
            } catch (err) {
                showMessage(msgEl, err.message, "error");
            } finally {
                setLoading(btn, "", false);
            }
        });
    }

    // ── Signup form ─────────────────────────────────────────────────────────
    const signupForm = document.getElementById("signupForm");
    if (signupForm) {
        const btn = signupForm.querySelector(".auth-submit");
        const msgEl = document.getElementById("authMessage");

        signupForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const full_name = document.getElementById("fullname").value.trim();
            const email = document.getElementById("email").value.trim();
            const password = document.getElementById("password").value;
            const confirmPassword = document.getElementById("confirmPassword").value;
            const terms = document.getElementById("terms");

            if (!full_name || !email || !password || !confirmPassword) {
                showMessage(msgEl, "Please fill in all fields.", "error"); return;
            }
            if (!isValidEmail(email)) {
                showMessage(msgEl, "Please enter a valid email address.", "error"); return;
            }
            if (password.length < 6) {
                showMessage(msgEl, "Password must be at least 6 characters.", "error"); return;
            }
            if (password !== confirmPassword) {
                showMessage(msgEl, "Passwords do not match.", "error"); return;
            }
            if (terms && !terms.checked) {
                showMessage(msgEl, "Please accept the Terms & Conditions.", "error"); return;
            }

            setLoading(btn, "Creating account…", true);
            try {
                const data = await apiRegister(full_name, email, password);
                saveSession(data.access_token, data.refresh_token, data.user);
                showMessage(msgEl, "🎉 Account created! Redirecting…", "success");
                setTimeout(() => window.location.href = "dashboard.html", 1200);
            } catch (err) {
                showMessage(msgEl, err.message, "error");
            } finally {
                setLoading(btn, "", false);
            }
        });
    }

    // ── Logout button (if present on any page) ───────────────────────────────
    document.querySelectorAll("[data-logout]").forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.preventDefault();
            const allDevices = btn.dataset.logout === "all";
            apiLogout(allDevices);
        });
    });
});
