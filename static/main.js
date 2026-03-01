// -------------------- Console Log --------------------
console.log("🇮🇳 NCC Infosphere Loaded");

// -------------------- Floating Logo Animation (optional extra) --------------------
const logo = document.querySelector('.floating-logo');
let yPos = 0;
let direction = 1;

function floatLogo() {
    yPos += direction * 0.3; // speed
    if (yPos > 10 || yPos < -10) direction *= -1;
    if (logo) logo.style.transform = `translateY(${yPos}px)`;
    requestAnimationFrame(floatLogo);
}
floatLogo();

// -------------------- Optional: Smooth Scroll for links --------------------
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e){
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});
