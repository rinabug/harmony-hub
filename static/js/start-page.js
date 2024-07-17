/* moving background animation*/
document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('backgroundCanvas');
    const ctx = canvas.getContext('2d');

    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    function drawWave(amplitude, frequency, phase, color, lineWidth, opacity) {
        ctx.beginPath();
        ctx.moveTo(0, canvas.height / 2);

        for (let x = 0; x < canvas.width; x++) {
            const y = canvas.height / 2 + amplitude * Math.sin((x * frequency + phase) * (Math.PI / 180));
            ctx.lineTo(x, y);
        }

        ctx.strokeStyle = `rgba(${color}, ${opacity})`;
        ctx.lineWidth = lineWidth;
        ctx.stroke();
    }

    let phase = 0;
    let opacityPhase = 0;

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Purple color in RGB format
        const purpleColor = '139, 99, 218';  // The RGB equivalent of the purple used in the login buttons

        // Draw waves with the same purple color, dynamic line widths, and animated opacity
        for (let i = 0; i < 6; i++) {
            const amplitude = 50 + i * 10;
            const frequency = 0.05 + i * 0.02;
            const lineWidth = 2 + i;
            const opacity = 0.5 + 0.5 * Math.sin((opacityPhase + i * 20) * (Math.PI / 180));

            drawWave(amplitude, frequency, phase + i * 30, purpleColor, lineWidth, opacity);
        }

        phase += 0.5; // Adjust this value to change the speed of the waves
        opacityPhase += 1; // Adjust this value to change the speed of opacity animation

        requestAnimationFrame(animate);
    }

    animate();
});