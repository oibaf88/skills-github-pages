---
layout: default
title: Mi Portfolio
---

<style>
  body {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: 'Segoe UI', system-ui, sans-serif;
    margin: 0;
    padding: 0;
  }

  .container {
    max-width: 860px;
    margin: 0 auto;
    padding: 60px 24px;
  }

  /* Hero */
  .hero {
    border-bottom: 1px solid #21262d;
    padding-bottom: 48px;
    margin-bottom: 48px;
  }

  .hero h1 {
    font-size: 2.8rem;
    font-weight: 700;
    margin: 0 0 12px;
    background: linear-gradient(90deg, #58a6ff, #79c0ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .hero .tagline {
    font-size: 1.2rem;
    color: #8b949e;
    margin: 0 0 20px;
  }

  .hero .bio {
    font-size: 1rem;
    color: #c9d1d9;
    line-height: 1.7;
    max-width: 600px;
  }

  /* Secciones */
  section {
    margin-bottom: 56px;
  }

  section h2 {
    font-size: 1.4rem;
    color: #58a6ff;
    border-left: 3px solid #58a6ff;
    padding-left: 12px;
    margin-bottom: 24px;
  }

  /* Proyectos */
  .projects-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 20px;
  }

  .project-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 20px;
    transition: border-color 0.2s;
  }

  .project-card:hover {
    border-color: #58a6ff;
  }

  .project-card h3 {
    margin: 0 0 8px;
    font-size: 1rem;
    color: #e6edf3;
  }

  .project-card p {
    margin: 0 0 16px;
    font-size: 0.9rem;
    color: #8b949e;
    line-height: 1.6;
  }

  .project-card a {
    font-size: 0.85rem;
    color: #58a6ff;
    text-decoration: none;
  }

  .project-card a:hover {
    text-decoration: underline;
  }

  /* Skills */
  .skills-list {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .skills-list li {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 20px;
    padding: 6px 16px;
    font-size: 0.9rem;
    color: #c9d1d9;
  }

  footer {
    border-top: 1px solid #21262d;
    padding-top: 24px;
    color: #8b949e;
    font-size: 0.85rem;
    text-align: center;
  }
</style>

<div class="container">

  <div class="hero">
    <h1>Tu Nombre</h1>
    <p class="tagline">Developer · Data Scientist · Builder</p>
    <p class="bio">
      Hola, soy un desarrollador apasionado por resolver problemas con código.
      Me especializo en Python, análisis de datos y desarrollo web.
      Siempre aprendiendo, siempre construyendo.
    </p>
  </div>

  <section>
    <h2>Proyectos</h2>
    <div class="projects-grid">

      <div class="project-card">
        <h3>Proyecto Uno</h3>
        <p>Descripción breve del proyecto. Qué hace, qué problema resuelve y qué tecnologías usa.</p>
        <a href="https://github.com/tu-usuario/proyecto-uno">Ver en GitHub →</a>
      </div>

      <div class="project-card">
        <h3>Proyecto Dos</h3>
        <p>Descripción breve del proyecto. Qué hace, qué problema resuelve y qué tecnologías usa.</p>
        <a href="https://github.com/tu-usuario/proyecto-dos">Ver en GitHub →</a>
      </div>

      <div class="project-card">
        <h3>Proyecto Tres</h3>
        <p>Descripción breve del proyecto. Qué hace, qué problema resuelve y qué tecnologías usa.</p>
        <a href="https://github.com/tu-usuario/proyecto-tres">Ver en GitHub →</a>
      </div>

    </div>
  </section>

  <section>
    <h2>Skills</h2>
    <ul class="skills-list">
      <li>Python</li>
      <li>Pandas</li>
      <li>NumPy</li>
      <li>Scikit-learn</li>
      <li>Jupyter</li>
      <li>HTML / CSS</li>
      <li>Git & GitHub</li>
      <li>SQL</li>
      <!-- Añade o elimina los que quieras -->
    </ul>
  </section>

  <footer>
    <p>Hecho con GitHub Pages · 2026</p>
  </footer>

</div>
