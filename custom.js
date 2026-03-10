// JavaScript personalizado para funcionalidades adicionales
console.log('Dashboard Analytics Pro cargado');

// Función para animaciones de entrada
document.addEventListener('DOMContentLoaded', function() {
    // Animación para las tarjetas KPI
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observar elementos para animaciones
    const animatedElements = document.querySelectorAll('.kpi-card, .chart-container');
    animatedElements.forEach(function(el) {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
});

// Función para actualizar el tiempo de última actualización
function updateLastRefreshTime() {
    const now = new Date();
    const timeString = now.toLocaleString('es-ES');
    const timeElement = document.querySelector('.last-update-time');
    if (timeElement) {
        timeElement.textContent = `Última actualización: ${timeString}`;
    }
}

// Ejecutar cuando se haga clic en el botón de actualizar
document.addEventListener('click', function(e) {
    if (e.target.closest('#refresh-btn')) {
        updateLastRefreshTime();
    }
});