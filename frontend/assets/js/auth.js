/* ============================================================
   auth.js  –  StudyPrep AI
   Token management + UI: session, JWT helpers, silent refresh,
   auth guard, authFetch, forms, nav update, logout.
   ============================================================ */

// ─── Config ───────────────────────────────────────────────────────────────────
const API_BASE = "http://localhost:5000";

// ── In-memory access token ────────────────────────────────────────────────────
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

// ─── JWT helpers ──────────────────────────────────────────────────────────────

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

// ─── Proactive refresh timer ──────────────────────────────────────────────────

function _scheduleProactiveRefresh(accessToken) {
    if (_refreshTimer) clearTimeout(_refreshTimer);
    const fireIn = Math.max(_tokenExpiresInMs(accessToken) - 60_000, 0);
    if (fireIn > 0) {
        _refreshTimer = setTimeout(async () => {
            console.debug("[Auth] Proactive refresh triggered.");
            await silentRefresh();
        }, fireIn);
    }
}

// ─── Silent refresh ───────────────────────────────────────────────────────────

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
        console.error("[Auth] Network error:", err);
        return false;
    }
}

// ─── Auth guard ───────────────────────────────────────────────────────────────

async function checkAuth() {
    if (!_isTokenExpired(_accessToken)) return true;
    const ok = await silentRefresh();
    if (!ok) { window.location.href = "login.html"; return false; }
    return true;
}

// ─── authFetch ────────────────────────────────────────────────────────────────

async function authFetch(url, options = {}) {
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

    if (res.status === 401 && data.code === "TOKEN_EXPIRED") {
        const ok = await silentRefresh();
        if (!ok) { window.location.href = "login.html"; throw new Error("Session expired."); }
        res = await doRequest();
        data = await res.json().catch(() => ({}));
    }

    if (!res.ok) throw Object.assign(new Error(data.error || "Request failed."), { data });
    return data;
}

// ─── Restore proactive timer on page load ─────────────────────────────────────
if (_accessToken && !_isTokenExpired(_accessToken)) {
    _scheduleProactiveRefresh(_accessToken);
}

// ─── API wrappers ─────────────────────────────────────────────────────────────

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
        }).catch(() => { });
    }
    clearSession();
    window.location.href = "login.html";
}

// ─── Nav / UI update ──────────────────────────────────────────────────────────

function updateNavForAuth() {
    const userName = localStorage.getItem("userName");
    const userEmail = localStorage.getItem("userEmail");
    const isLoggedIn = !!userName;

    // Hide login/signup buttons when logged in
    document.querySelectorAll(".nav-login-btn").forEach(el => {
        el.style.display = isLoggedIn ? "none" : "";
    });
    // Remove any previously added profile/logout elements
    document.querySelectorAll(".nav-user-profile, .nav-logout-btn").forEach(el => el.remove());

    if (isLoggedIn) {
        document.querySelectorAll(".nav-links").forEach(navLinks => {
            const themeBtn = navLinks.querySelector("#theme-toggle");

            const profile = document.createElement("span");
            profile.className = "nav-user-profile";
            profile.innerHTML = `<span class="nav-user-avatar">${userName.charAt(0)}</span>${userName.split(" ")[0]}`;

            const logout = document.createElement("a");
            logout.href = "#";
            logout.className = "nav-logout-btn";
            logout.textContent = "Logout";
            logout.addEventListener("click", e => { e.preventDefault(); apiLogout(); });

            if (themeBtn) {
                navLinks.insertBefore(profile, themeBtn);
                navLinks.insertBefore(logout, themeBtn);
            } else {
                navLinks.appendChild(profile);
                navLinks.appendChild(logout);
            }
        });

        const heroBtn = document.querySelector(".hero .btn");
        if (heroBtn && heroBtn.textContent.trim() === "Get Started Free") {
            heroBtn.textContent = "Go to Dashboard";
            heroBtn.href = "dashboard.html";
        }
    }

    const infoCard = document.getElementById("user-info-card");
    if (infoCard && isLoggedIn) {
        infoCard.innerHTML = `
            <div class="user-info-avatar">${userName.charAt(0)}</div>
            <h2>Welcome, ${userName}!</h2>
            <p class="user-email">${userEmail}</p>
            <span class="user-status">Account Verified</span>
            <br>
            <button class="logout-btn" onclick="apiLogout()">Logout</button>
        `;
    }
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

// ─── DOMContentLoaded ─────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {

    updateNavForAuth();

    // Password visibility toggle
    document.querySelectorAll(".password-toggle").forEach(btn => {
        btn.addEventListener("click", e => {
            e.preventDefault();
            const input = btn.parentElement.querySelector("input");
            input.type = input.type === "password" ? "text" : "password";
            btn.textContent = input.type === "password" ? "Show" : "Hide";
        });
    });

    // Password strength meter (signup page only)
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

    // Login form
    const loginForm = document.getElementById("loginForm");
    if (loginForm) {
        const btn = loginForm.querySelector(".auth-submit");
        const msgEl = document.getElementById("authMessage");

        loginForm.addEventListener("submit", async e => {
            e.preventDefault();
            const email = document.getElementById("email").value.trim();
            const password = document.getElementById("password").value;

            if (!email || !password) { showMessage(msgEl, "Please fill in all fields.", "error"); return; }
            if (!isValidEmail(email)) { showMessage(msgEl, "Please enter a valid email address.", "error"); return; }

            setLoading(btn, "Signing in...", true);
            try {
                const data = await apiLogin(email, password);
                saveSession(data.access_token, data.refresh_token, data.user);
                showMessage(msgEl, "Login successful! Redirecting...", "success");
                setTimeout(() => window.location.href = "dashboard.html", 1200);
            } catch (err) {
                showMessage(msgEl, err.message, "error");
            } finally {
                setLoading(btn, "", false);
            }
        });
    }

    // Signup form
    const signupForm = document.getElementById("signupForm");
    if (signupForm) {
        const btn = signupForm.querySelector(".auth-submit");
        const msgEl = document.getElementById("authMessage");

        signupForm.addEventListener("submit", async e => {
            e.preventDefault();
            const full_name = document.getElementById("fullname").value.trim();
            const email = document.getElementById("email").value.trim();
            const password = document.getElementById("password").value;
            const confirmPassword = document.getElementById("confirmPassword").value;
            const terms = document.getElementById("terms");

            if (!full_name || !email || !password || !confirmPassword) { showMessage(msgEl, "Please fill in all fields.", "error"); return; }
            if (!isValidEmail(email)) { showMessage(msgEl, "Please enter a valid email address.", "error"); return; }
            if (password.length < 6) { showMessage(msgEl, "Password must be at least 6 characters.", "error"); return; }
            if (password !== confirmPassword) { showMessage(msgEl, "Passwords do not match.", "error"); return; }
            if (terms && !terms.checked) { showMessage(msgEl, "Please accept the Terms & Conditions.", "error"); return; }

            setLoading(btn, "Creating account...", true);
            try {
                await apiRegister(full_name, email, password);
                showMessage(msgEl, "Account created! Please sign in.", "success");
                setTimeout(() => window.location.href = "login.html", 1500);
            } catch (err) {
                showMessage(msgEl, err.message, "error");
            } finally {
                setLoading(btn, "", false);
            }
        });
    }

    // data-logout buttons
    document.querySelectorAll("[data-logout]").forEach(btn => {
        btn.addEventListener("click", e => {
            e.preventDefault();
            apiLogout(btn.dataset.logout === "all");
        });
    });
});
