---
layout: null
title: "python-email-system"
date: 2026-06-19 18:00:00 +0200
permalink: /blog/python-email-system/
categories: python oop
---

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="description" content="Blog post about a small object-oriented Python email system simulation with a live Flask and Supabase demo." />
  <title>Python Email System | B. Fabio Mejías Fernández</title>
  <link rel="stylesheet" href="{{ '/styles.css' | relative_url }}" />
  <link rel="stylesheet" href="{{ '/blog-posts.css' | relative_url }}" />
  <script defer src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-core.min.js"></script>
  <script defer src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>
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
          <span>Python // Object-oriented programming // Flask demo</span>
        </div>

        <h1>
          <span class="gradient-text">Python</span> Email System
        </h1>

        <div class="post-meta post-meta-panel" aria-label="Post metadata summary">
          <span class="pill">Published // <time datetime="2026-06-19">2026-06-19</time></span>
          <span class="pill">Category // Python OOP</span>
          <span class="pill">Status // deployed demo</span>
          <span class="pill">Stack // Flask + Supabase</span>
        </div>

        <p class="lead">
          A small object-oriented Python email simulation built with three cooperating classes:
          <strong>Email</strong>, <strong>User</strong> and <strong>Inbox</strong>. The original exercise models how two users can
          send, list and read messages while keeping the message state inside the objects. It now also has a browser demo
          deployed as a small Flask application.
        </p>

        <div class="actions">
          <a class="button button-primary" href="https://email-client-1gs6.onrender.com" target="_blank" rel="noopener noreferrer">Open live demo</a>
          <a class="button button-secondary" href="https://github.com/oibaf88/email-client" target="_blank" rel="noopener noreferrer">View repository</a>
        </div>

        <section class="content-card">
          <h2>What this program does</h2>
          <p>
            The program creates two users dynamically, gives each user an inbox and lets them exchange messages. Each
            email stores sender, receiver, subject, body, timestamp and read/unread status.
          </p>

          <ul>
            <li><strong>Email:</strong> stores message data, marks messages as read and formats email output.</li>
            <li><strong>User:</strong> owns an inbox and exposes high-level actions such as sending and reading email.</li>
            <li><strong>Inbox:</strong> stores received emails, lists them, validates indexes and handles deletion.</li>
            <li><strong>Web demo:</strong> exposes the same learning idea through a browser interface deployed on Render.</li>
          </ul>
        </section>

        <section class="code-card" aria-label="Python source code">
          <div class="code-header">
            <span class="dots" aria-hidden="true">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </span>
            <span>python_email_system.py</span>
          </div>

          <pre class="code-canvas"><code class="language-python">import datetime

class Email:
    def __init__(self, sender, receiver, subject, body):
        self.sender = sender
        self.receiver = receiver
        self.subject = subject
        self.body = body
        self.timestamp = datetime.datetime.now()
        self.read = False

    def mark_as_read(self):
        self.read = True

    def display_full_email(self):
        self.mark_as_read()
        print(&quot;\n--- Email ---&quot;)
        print(f&quot;From: {self.sender.name}&quot;)
        print(f&quot;To: {self.receiver.name}&quot;)
        print(f&quot;Subject: {self.subject}&quot;)
        print(f&quot;Received: {self.timestamp.strftime('%Y-%m-%d %H:%M')}&quot;)
        print(f&quot;Body: {self.body}&quot;)
        print(&quot;------------\n&quot;)

    def __str__(self):
        status = &quot;Read&quot; if self.read else &quot;Unread&quot;
        return (
            f&quot;[{status}] From: {self.sender.name} | &quot;
            f&quot;Subject: {self.subject} | &quot;
            f&quot;Time: {self.timestamp.strftime('%Y-%m-%d %H:%M')}&quot;
        )

class User:
    def __init__(self, name):
        self.name = name
        self.inbox = Inbox()

    def send_email(self, receiver, subject, body):
        email = Email(sender=self, receiver=receiver, subject=subject, body=body)
        receiver.inbox.receive_email(email)
        print(f&quot;\nEmail sent from {self.name} to {receiver.name}!\n&quot;)

    def check_inbox(self):
        print(f&quot;\n======== {self.name}'s Inbox ========&quot;)
        self.inbox.list_emails()

    def read_email(self, index):
        self.inbox.read_email(index)

    def delete_email(self, index):
        self.inbox.delete_email(index)

class Inbox:
    def __init__(self):
        self.emails = []

    def receive_email(self, email):
        self.emails.append(email)

    def list_emails(self):
        if not self.emails:
            print(&quot;Your inbox is empty.\n&quot;)
            return
        for i, email in enumerate(self.emails, start=1):
            print(f&quot;{i}. {email}&quot;)
        print(&quot;==================================\n&quot;)

    def read_email(self, index):
        if not self.emails:
            print(&quot;Inbox is empty.\n&quot;)
            return
        actual_index = index - 1
        if actual_index &lt; 0 or actual_index &gt;= len(self.emails):
            print(&quot;Invalid email number.\n&quot;)
            return
        self.emails[actual_index].display_full_email()

    def delete_email(self, index):
        if not self.emails:
            print(&quot;Inbox is empty.\n&quot;)
            return
        actual_index = index - 1
        if actual_index &lt; 0 or actual_index &gt;= len(self.emails):
            print(&quot;Invalid email number.\n&quot;)
            return
        del self.emails[actual_index]
        print(&quot;Email deleted.\n&quot;)</code></pre>
        </section>

        <section class="content-card">
          <h2>Development notes</h2>
          <p>
            This exercise is useful because the responsibilities are separated clearly: <code>Email</code> represents the
            message, <code>Inbox</code> manages a collection of messages and <code>User</code> acts as the interface used by
            the rest of the program.
          </p>
          <p>
            The browser demo extends the console exercise into a small deployed prototype. It keeps the learning scope
            simple while introducing a more realistic application boundary: frontend interaction, backend routes and
            persistence through Supabase.
          </p>
        </section>

        <div class="actions">
          <a class="button button-primary" href="https://email-client-1gs6.onrender.com" target="_blank" rel="noopener noreferrer">Open live demo</a>
          <a class="button button-secondary" href="{{ '/' | relative_url }}#blog">Back to blog</a>
          <a class="button button-secondary" href="{{ '/' | relative_url }}">Home</a>
        </div>
      </article>

      <aside class="side-card side-card-featured" aria-label="Post metadata">
        <h2>Post metadata</h2>
        <div class="side-list">
          <div>
            <span>Title</span>
            <strong>Python Email System</strong>
          </div>
          <div>
            <span>Date</span>
            <strong>2026-06-19</strong>
          </div>
          <div>
            <span>Language</span>
            <strong>Python</strong>
          </div>
          <div>
            <span>Topic</span>
            <strong>OOP simulation</strong>
          </div>
          <div>
            <span>Demo</span>
            <strong>Render deployment</strong>
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
