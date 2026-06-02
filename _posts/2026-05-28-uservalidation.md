---
title: uservalidation
date: 2026-05-28
permalink: /blog/uservalidation/
---

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="description" content="Blog post about a small Python user validation function." />
  <title>uservalidation | B. Fabio Mejías Fernández</title>

  <style>
    :root {
      --bg: #000000;
      --card: rgba(2, 8, 14, 0.82);
      --card-border: rgba(0, 255, 156, 0.28);
      --text: #f8fbff;
      --muted: #8ca0b8;
      --accent: #00f5ff;
      --accent-2: #00ff9c;
      --warning: #b8ff3d;
      --code-bg: rgba(0, 0, 0, 0.64);
      --radius: 24px;
      --max-width: 1040px;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    html {
      scroll-behavior: smooth;
    }

    body {
      min-height: 100vh;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background:
        linear-gradient(rgba(0, 255, 156, 0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 245, 255, 0.04) 1px, transparent 1px),
        radial-gradient(circle at 20% 10%, rgba(0, 245, 255, 0.22), transparent 28%),
        radial-gradient(circle at 85% 20%, rgba(0, 255, 156, 0.16), transparent 26%),
        #000000;
      background-size: 42px 42px, 42px 42px, auto, auto, auto;
      line-height: 1.6;
      overflow-x: hidden;
    }

    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background: repeating-linear-gradient(
        to bottom,
        rgba(255, 255, 255, 0.035) 0,
        rgba(255, 255, 255, 0.035) 1px,
        transparent 1px,
        transparent 7px
      );
      mix-blend-mode: screen;
      opacity: 0.35;
      z-index: 0;
    }

    a {
      color: inherit;
      text-decoration: none;
    }

    .container {
      width: min(100% - 32px, var(--max-width));
      margin: 0 auto;
      position: relative;
      z-index: 1;
    }

    .site-header {
      position: sticky;
      top: 0;
      z-index: 10;
      backdrop-filter: blur(18px);
      background: rgba(0, 0, 0, 0.82);
      border-bottom: 1px solid rgba(0, 255, 156, 0.22);
      box-shadow: 0 0 26px rgba(0, 245, 255, 0.12);
    }

    .nav {
      min-height: 72px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 24px;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      font-weight: 800;
      letter-spacing: -0.03em;
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
    }

    .brand-mark {
      width: 40px;
      height: 40px;
      display: grid;
      place-items: center;
      border-radius: 14px;
      color: #06101d;
      font-weight: 900;
      background: linear-gradient(135deg, var(--accent), var(--accent-2));
      box-shadow: 0 0 24px rgba(0, 245, 255, 0.35), 0 0 44px rgba(0, 255, 156, 0.18);
    }

    .nav-links {
      display: flex;
      align-items: center;
      gap: 18px;
      color: var(--muted);
      font-size: 0.95rem;
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
    }

    .nav-links a {
      color: #8ca0b8;
      transition: color 180ms ease, text-shadow 180ms ease;
    }

    .nav-links a:hover {
      color: var(--text);
      text-shadow: 0 0 16px rgba(0, 245, 255, 0.75);
    }

    main {
      padding: 76px 0 80px;
    }

    .post-layout {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 280px;
      gap: clamp(36px, 6vw, 72px);
      align-items: start;
    }

    .post {
      min-width: 0;
    }

    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border: 1px solid rgba(0, 245, 255, 0.28);
      border-radius: 999px;
      color: #c8f6ff;
      background: rgba(0, 245, 255, 0.1);
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      font-size: 0.9rem;
      margin-bottom: 24px;
    }

    .eyebrow-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--accent-2);
      box-shadow: 0 0 18px var(--accent-2);
    }

    h1 {
      max-width: 820px;
      font-size: clamp(3rem, 8vw, 6.6rem);
      line-height: 0.92;
      letter-spacing: -0.08em;
      margin-bottom: 24px;
      text-transform: uppercase;
      text-shadow: 0 0 28px rgba(0, 245, 255, 0.18);
      overflow-wrap: anywhere;
    }

    .gradient-text {
      color: transparent;
      background: linear-gradient(90deg, #00f5ff, #00ff9c, #eaffb8);
      background-clip: text;
      -webkit-background-clip: text;
    }

    .post-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 34px;
      color: var(--muted);
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      font-size: 0.92rem;
    }

    .pill {
      padding: 8px 12px;
      border: 1px solid rgba(0, 255, 156, 0.24);
      border-radius: 999px;
      background: rgba(0, 255, 156, 0.05);
    }

    .lead {
      max-width: 760px;
      color: var(--muted);
      font-size: clamp(1.08rem, 2vw, 1.26rem);
      margin-bottom: 32px;
    }

    .content-card,
    .code-card,
    .side-card {
      background: linear-gradient(180deg, rgba(0, 12, 20, 0.92), rgba(0, 0, 0, 0.86));
      border: 1px solid rgba(0, 255, 156, 0.24);
      border-radius: var(--radius);
      box-shadow: 0 0 0 1px rgba(0, 245, 255, 0.08), 0 0 42px rgba(0, 245, 255, 0.12);
    }

    .content-card {
      padding: clamp(22px, 4vw, 34px);
      margin-bottom: 24px;
    }

    .content-card h2 {
      font-size: clamp(1.5rem, 3vw, 2.2rem);
      letter-spacing: -0.05em;
      text-transform: uppercase;
      margin-bottom: 14px;
    }

    .content-card p {
      color: var(--muted);
      margin-bottom: 16px;
    }

    .content-card ul {
      color: var(--muted);
      padding-left: 1.2rem;
      display: grid;
      gap: 10px;
    }

    .content-card strong {
      color: var(--text);
    }

    .code-card {
      overflow: hidden;
      margin-bottom: 28px;
    }

    .code-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 14px 18px;
      border-bottom: 1px solid rgba(0, 245, 255, 0.16);
      background: rgba(0, 245, 255, 0.06);
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      color: var(--muted);
      font-size: 0.88rem;
    }

    .dots {
      display: inline-flex;
      gap: 7px;
      align-items: center;
    }

    .dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--accent-2);
      box-shadow: 0 0 12px rgba(0, 255, 156, 0.65);
    }

    pre {
      margin: 0;
      padding: clamp(18px, 3vw, 26px);
      overflow-x: auto;
      background: var(--code-bg);
    }

    code {
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      font-size: 0.92rem;
      line-height: 1.65;
      color: #e8fbff;
      tab-size: 4;
    }

    .side-card {
      position: sticky;
      top: 104px;
      padding: 22px;
    }

    .side-card h2 {
      color: var(--accent-2);
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      text-transform: uppercase;
      font-size: 0.85rem;
      letter-spacing: 0.14em;
      margin-bottom: 16px;
    }

    .side-list {
      display: grid;
      gap: 12px;
      color: var(--muted);
      font-size: 0.95rem;
    }

    .side-list div {
      display: flex;
      justify-content: space-between;
      gap: 18px;
      padding: 12px 0;
      border-bottom: 1px solid rgba(0, 245, 255, 0.12);
    }

    .side-list strong {
      color: var(--text);
      text-align: right;
    }

    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 14px;
      align-items: center;
      margin-top: 32px;
    }

    .button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 48px;
      padding: 0 20px;
      border-radius: 999px;
      font-weight: 800;
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      transition: transform 180ms ease, box-shadow 180ms ease;
    }

    .button:hover {
      transform: translateY(-2px);
    }

    .button-primary {
      color: #06101d;
      background: linear-gradient(135deg, var(--accent), var(--accent-2));
      box-shadow: 0 0 24px rgba(0, 245, 255, 0.35), 0 0 44px rgba(0, 255, 156, 0.18);
    }

    .button-secondary {
      color: var(--text);
      border: 1px solid rgba(0, 245, 255, 0.28);
      background: rgba(0, 245, 255, 0.06);
    }

    footer {
      padding: 36px 0;
      color: var(--muted);
      border-top: 1px solid rgba(0, 245, 255, 0.12);
    }

    @media (max-width: 900px) {
      .post-layout {
        grid-template-columns: 1fr;
      }

      .side-card {
        position: relative;
        top: auto;
      }

      .nav {
        align-items: flex-start;
        flex-direction: column;
        padding: 18px 0;
      }

      .nav-links {
        width: 100%;
        overflow-x: auto;
        padding-bottom: 4px;
      }

      main {
        padding-top: 54px;
      }
    }
  </style>
</head>

<body>
  <header class="site-header">
    <div class="container nav">
      <a href="{{ '/' | relative_url }}" class="brand" aria-label="Homepage">
        <span class="brand-mark">eH</span>
        <span>B. Fabio Mejías Fernández</span>
      </a>

      <nav class="nav-links" aria-label="Main navigation">
        <a href="{{ '/' | relative_url }}">Home</a>
        <a href="{{ '/' | relative_url }}#about">About</a>
        <a href="{{ '/' | relative_url }}#focus">Focus</a>
        <a href="{{ '/' | relative_url }}#progress">Progress</a>
        <a href="{{ '/' | relative_url }}#blog">Blog</a>
        <a href="{{ '/' | relative_url }}#contact">Contact</a>
      </nav>
    </div>
  </header>

  <main>
    <div class="container post-layout">
      <article class="post">
        <div class="eyebrow">
          <span class="eyebrow-dot"></span>
          <span>Python // User validation</span>
        </div>

        <h1>
          <span class="gradient-text">user</span>validation
        </h1>

        <div class="post-meta">
          <span class="pill">Published // <time datetime="2026-05-28">2026-05-28</time></span>
          <span class="pill">Category // Python basics</span>
          <span class="pill">Status // learning log</span>
        </div>

        <p class="lead">
          A small Python exercise focused on validating user input before registration. The function checks a name,
          an email address and a password by delegating each validation rule to smaller helper functions.
        </p>

        <section class="content-card">
          <h2>What this function does</h2>
          <p>
            The goal is deliberately simple: keep the registration flow clean by separating validation from user creation.
            First, <strong>validate_user()</strong> checks the three input fields. Then, <strong>register_user()</strong>
            returns a user dictionary only if every validation step succeeds.
          </p>

          <ul>
            <li><strong>Name:</strong> must pass <code>validate_name(name)</code>.</li>
            <li><strong>Email:</strong> must pass <code>validate_email(email)</code>.</li>
            <li><strong>Password:</strong> must pass <code>validate_password(password)</code>.</li>
            <li><strong>Failure behavior:</strong> validation errors are converted into <code>False</code> during registration.</li>
          </ul>
        </section>

        <section class="code-card" aria-label="Python source code">
          <div class="code-header">
            <span class="dots">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </span>
            <span>small_user_validation_function.py</span>
          </div>

          <pre><code>from python_functions import validate_name, validate_email, validate_password

def validate_user(name, email, password):
    &quot;&quot;&quot;Validate the user name, email and password.

    Args:
        name (string): Name that we&#x27;re attempting to validate.
        email (string): Email address that we&#x27;re attempting to validate.
        password (string): Password that we&#x27;re attempting to validate.

    Returns:
        bool: Returns True if all validation checks pass.

    Raises:
        ValueError: If any validation check fails.
    &quot;&quot;&quot;
    if validate_name(name) == False:
        raise ValueError(&quot;Please make sure your name is greater than 2 characters!&quot;)

    if validate_email(email) == False:
        raise ValueError(&quot;Your email address is in the incorrect format, please enter a valid email.&quot;)

    if validate_password(password) == False:
        raise ValueError(&quot;Your password is too weak, ensure that your password is greater than 8 characters, &quot;
                         &quot;contains a capital letter and a number.&quot;)

    return True

def register_user(name, email, password):
    &quot;&quot;&quot;Attempt to register the user if they pass validation.

    Args:
        name (string): Name of the user.
        email (string): Email address of the user.
        password (string): Password of the user.

    Returns:
        dict or bool: Returns a dictionary with the user details if validation is successful,
        or False if the validation fails.
    &quot;&quot;&quot;
    try:
        validate_user(name, email, password)
    except:
        return False

    user = {
        &quot;name&quot;: name,
        &quot;email&quot;: email,
        &quot;password&quot;: password
    }

    return user</code></pre>
        </section>

        <section class="content-card">
          <h2>Development notes</h2>
          <p>
            This is a useful first pattern because it introduces a common backend idea:
            validation should happen before persistence or account creation. In a larger application,
            the same structure could be extended with typed exceptions, password hashing and database storage.
          </p>
          <p>
            One future improvement would be replacing the broad <code>except:</code> block with
            <code>except ValueError:</code>, so unexpected errors are not silently swallowed.
          </p>
        </section>

        <div class="actions">
          <a class="button button-primary" href="{{ '/' | relative_url }}#blog">Back to blog</a>
          <a class="button button-secondary" href="{{ '/' | relative_url }}">Home</a>
        </div>
      </article>

      <aside class="side-card" aria-label="Post metadata">
        <h2>Post metadata</h2>
        <div class="side-list">
          <div>
            <span>Title</span>
            <strong>uservalidation</strong>
          </div>
          <div>
            <span>Date</span>
            <strong>2026-05-28</strong>
          </div>
          <div>
            <span>Language</span>
            <strong>Python</strong>
          </div>
          <div>
            <span>Topic</span>
            <strong>Validation</strong>
          </div>
        </div>
      </aside>
    </div>
  </main>

  <footer>
    <div class="container">
      <p>© 2026 B. Fabio Mejías Fernández. eHealth Developer Portfolio.</p>
    </div>
  </footer>
</body>
</html>
