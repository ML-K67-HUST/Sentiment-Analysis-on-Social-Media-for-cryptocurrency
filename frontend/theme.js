document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('theme-toggle');
    const body = document.body;
    const icon = toggleBtn.querySelector('.icon');

    // Check saved preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        body.classList.add('light-mode');
        updateIcon(true);
    } else {
        updateIcon(false);
    }

    toggleBtn.addEventListener('click', () => {
        body.classList.toggle('light-mode');
        const isLight = body.classList.contains('light-mode');

        // Save preference
        localStorage.setItem('theme', isLight ? 'light' : 'dark');

        // Update icon
        updateIcon(isLight);
    });

    function updateIcon(isLight) {
        if (isLight) {
            toggleBtn.innerHTML = '☀️'; // Sun icon
        } else {
            toggleBtn.innerHTML = '🌙'; // Moon icon
        }
    }
});
