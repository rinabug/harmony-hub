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

    function drawWave(amplitude, frequency, phase, color) {
        ctx.beginPath();
        ctx.moveTo(0, canvas.height / 2);

        for (let x = 0; x < canvas.width; x++) {
            const y = canvas.height / 2 + amplitude * Math.sin((x * frequency + phase) * (Math.PI / 180));
            ctx.lineTo(x, y);
        }

        ctx.strokeStyle = color;
        ctx.lineWidth = 4;
        ctx.stroke();
    }

    let phase = 0;

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        //drawWave(100, 0.05, phase, 'rgba(255, 0, 0, 0.5)'); //red
        //drawWave(80, 0.1, phase + 45, 'rgba(0, 255, 0, 0.5)'); //green
        drawWave(60, 0.2, phase + 90, 'rgba(0, 0, 255, 0.5)'); //blue
        drawWave(90, 0.12, phase + 40, 'rgba(75, 0, 130, 0.5)'); //indigo
        drawWave(50, 0.1, phase + 75, 'rgba(238, 130, 238, 0.5)'); //violet

        phase += 0.8;

        requestAnimationFrame(animate);
    }

    animate();
});

