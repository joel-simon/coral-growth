function init_particles(particleCount) {
    const particles = new THREE.Geometry()
    // create the particle variables
    const pMaterial = new THREE.ParticleBasicMaterial({
        color: 0xFFFFFF,
        size: 1,
        map: THREE.ImageUtils.loadTexture(
            "img/circle.png"
        ),
        blending: THREE.AdditiveBlending,
        transparent: true
    })
    for (let p = 0; p < particleCount; p++) {
        let pX = (Math.random()-0.5) * 100,
            pY = Math.random() * 100,
            pZ = (Math.random()-0.5) * 100;
        let particle = new THREE.Vector3(pX, pY, pZ);
        let velocity = new THREE.Vector3((Math.random()-0.5) * .01, (Math.random()-0.5) * .01, (Math.random()-0.5) * .01)
        particle.velocity = velocity
        particles.vertices.push(particle)
    }
    // create the particle system
    const particleSystem = new THREE.Points(particles, pMaterial)
    particleSystem.sortParticles = true
    // scene.add(particleSystem)
    return particleSystem
}

function update_particles(particleSystem) {
   let particles = particleSystem.geometry
    for (var i = 0; i < particles.vertices.length; i++) {
        var particle = particles.vertices[i];
        particle.add(particle.velocity);
        if (particle.x < 0) {
            particle.x == 100;
        } else if (particle.x > 100) {
            particle.x = 0;
        }
        if (particle.y < 0) {
            particle.y == 100;
        } else if (particle.y > 100) {
            particle.y = 0;
        }
        if (particle.z < 0) {
            particle.z == 100;
        } else if (particle.z > 100) {
            particle.z = 0;
        }
    }
    particleSystem.geometry.verticesNeedUpdate = true;
}