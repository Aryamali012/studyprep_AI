/* Main JS for StudyPrep AI */

document.addEventListener('DOMContentLoaded', () => {
    console.log('StudyPrep AI Loaded');

    // Theme Toggle Logic
    const toggleBtn = document.getElementById('theme-toggle');
    const storedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (storedTheme === 'dark' || (!storedTheme && prefersDark)) {
        document.documentElement.setAttribute('data-theme', 'dark');
        if (toggleBtn) toggleBtn.textContent = 'Light Mode';
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
        if (toggleBtn) toggleBtn.textContent = 'Dark Mode';
    }

    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            toggleBtn.textContent = newTheme === 'dark' ? 'Light Mode' : 'Dark Mode';
        });
    }

    // Add scroll effect to header
    const header = document.querySelector('header');

    function updateHeaderState() {
        if (window.scrollY > 50) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    }

    if (header) {
        window.addEventListener('scroll', updateHeaderState);
        updateHeaderState(); // Init on load
    }
});

