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
  <meta name="description" content="Blog post about a small object-oriented Python email system simulation." />
  <title>Python Email System | B. Fabio Mejías Fernández</title>
  <link rel="stylesheet" href="{{ '/styles.css' | relative_url }}" />
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
          <span>Python // Object-oriented programming</span>
        </div>

        <h1>
          <span class="gradient-text">Python</span> Email System
        </h1>

        <div class="post-meta">
          <span class="pill">Published // <time datetime="2026-06-19">2026-06-19</time></span>
          <span class="pill">Category // Python OOP</span>
          <span class="pill">Status // learning log</span>
        </div>

        <p class="lead">
          A small console-based Python email simulation built with three cooperating classes:
          <strong>Email</strong>, <strong>User</strong> and <strong>Inbox</strong>. The exercise models how users can send,
          list and read messages while keeping the message state inside the objects.
        </p>

        <div class="actions">
          <a class="button button-primary" href="https://email-client.onrender.com" target="_blank" rel="noopener noreferrer">Open live demo</a>
          <a class="button button-secondary" href="https://github.com/oibaf88/email-client" target="_blank" rel="noopener noreferrer">View repository</a>
        </div>

        <section class="content-card">
          <h2>What this program does</h2>
          <p>
            The program creates two users dynamically, gives each user an inbox and lets them exchange messages through
            a terminal menu. Each email stores sender, receiver, subject, body, timestamp and read/unread status.
          </p>

          <ul>
            <li><strong>Email:</strong> stores message data, marks messages as read and formats email output.</li>
            <li><strong>User:</strong> owns an inbox and exposes high-level actions such as sending and reading email.</li>
            <li><strong>Inbox:</strong> stores received emails, lists them, validates indexes and handles deletion.</li>
            <li><strong>Main loop:</strong> offers a simple interactive menu for the two-user simulation.</li>
          </ul>
        </section>

        <section class="code-card" aria-label="Python source code">
          <div class="code-header">
            <span class="dots">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </span>
            <span>python_email_system.py</span>
          </div>

          <pre><code>import datetime

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
        print(&#x27;\n--- Email ---&#x27;)
        print(f&#x27;From: {self.sender.name}&#x27;)
        print(f&#x27;To: {self.receiver.name}&#x27;)
        print(f&#x27;Subject: {self.subject}&#x27;)
        print(f&quot;Received: {self.timestamp.strftime(&#x27;%Y-%m-%d %H:%M&#x27;)}&quot;)
        print(f&#x27;Body: {self.body}&#x27;)
        print(&#x27;------------\n&#x27;)

    def __str__(self):
        status = &#x27;Read&#x27; if self.read else &#x27;Unread&#x27;
        return f&quot;[{status}] From: {self.sender.name} | Subject: {self.subject} | Time: {self.timestamp.strftime(&#x27;%Y-%m-%d %H:%M&#x27;)}&quot;

class User:
    def __init__(self, name):
        self.name = name
        self.inbox = Inbox()

    def send_email(self, receiver, subject, body):
        email = Email(sender=self, receiver=receiver, subject=subject, body=body)
        receiver.inbox.receive_email(email)
        print(f&#x27;\nEmail sent from {self.name} to {receiver.name}!\n&#x27;)

    def check_inbox(self):
        print(f&quot;\n======== {self.name}&#x27;s Inbox ========&quot;)
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
            print(&#x27;Your inbox is empty.\n&#x27;)
            return
        for i, email in enumerate(self.emails, start=1):
            print(f&#x27;{i}. {email}&#x27;)
        print(&quot;==================================\n&quot;)

    def read_email(self, index):
        if not self.emails:
            print(&#x27;Inbox is empty.\n&#x27;)
            return
        actual_index = index - 1
        if actual_index &lt; 0 or actual_index &gt;= len(self.emails):
            print(&#x27;Invalid email number.\n&#x27;)
            return
        self.emails[actual_index].display_full_email()

    def delete_email(self, index):
        if not self.emails:
            print(&#x27;Inbox is empty.\n&#x27;)
            return
        actual_index = index - 1
        if actual_index &lt; 0 or actual_index &gt;= len(self.emails):
            print(&#x27;Invalid email number.\n&#x27;)
            return
        del self.emails[actual_index]
        print(&#x27;Email deleted.\n&#x27;)


def main():
    print(&quot;--- Welcome to the Python Email System ---&quot;)
    
    # Registro dinámico de los dos usuarios de la simulación
    name1 = input(&quot;Enter name for User 1: &quot;).strip()
    name2 = input(&quot;Enter name for User 2: &quot;).strip()
    
    # Si el usuario presiona Enter sin escribir, asignamos nombres por defecto
    user1 = User(name1 if name1 else &quot;User1&quot;)
    user2 = User(name2 if name2 else &quot;User2&quot;)
    
    while True:
        print(f&quot;\n--- MAIN MENU ---&quot;)
        print(f&quot;1. {user1.name} sends an email to {user2.name}&quot;)
        print(f&quot;2. {user2.name} sends an email to {user1.name}&quot;)
        print(f&quot;3. Check {user1.name}&#x27;s Inbox&quot;)
        print(f&quot;4. Check {user2.name}&#x27;s Inbox&quot;)
        print(f&quot;5. Read an email&quot;)
        print(f&quot;6. Exit&quot;)
        
        choice = input(&quot;Select an option (1-6): &quot;).strip()
        
        if choice == &#x27;1&#x27;:
            print(f&quot;\n--- Composing email from {user1.name} to {user2.name} ---&quot;)
            subject = input(&quot;Subject: &quot;)
            body = input(&quot;Body: &quot;)
            user1.send_email(user2, subject, body)
            
        elif choice == &#x27;2&#x27;:
            print(f&quot;\n--- Composing email from {user2.name} to {user1.name} ---&quot;)
            subject = input(&quot;Subject: &quot;)
            body = input(&quot;Body: &quot;)
            user2.send_email(user1, subject, body)
            
        elif choice == &#x27;3&#x27;:
            user1.check_inbox()
            
        elif choice == &#x27;4&#x27;:
            user2.check_inbox()
            
        elif choice == &#x27;5&#x27;:
            print(&quot;\nWhose inbox do you want to read?&quot;)
            print(f&quot;1. {user1.name}&quot;)
            print(f&quot;2. {user2.name}&quot;)
            user_choice = input(&quot;Select user (1-2): &quot;).strip()
            
            target_user = user1 if user_choice == &#x27;1&#x27; else user2 if user_choice == &#x27;2&#x27; else None
            
            if target_user:
                target_user.check_inbox()
                if target_user.inbox.emails: # Solo pide número si hay correos
                    try:
                        idx = int(input(&quot;Enter the email number to read: &quot;))
                        target_user.read_email(idx)
                    except ValueError:
                        print(&quot;Please enter a valid number.\n&quot;)
            else:
                print(&quot;Invalid user selection.\n&quot;)
                
        elif choice == &#x27;6&#x27;:
            print(&quot;\nGoodbye!&quot;)
            break
        else:
            print(&quot;Invalid option. Please try again.\n&quot;)

if __name__ == &#x27;__main__&#x27;:
    main()</code></pre>
        </section>

        <section class="content-card">
          <h2>Development notes</h2>
          <p>
            This is a useful object-oriented programming exercise because the responsibilities are separated clearly:
            <code>Email</code> represents the message, <code>Inbox</code> manages a collection of messages and
            <code>User</code> acts as the interface used by the rest of the program.
          </p>
          <p>
            The console exercise now also has a deployed browser demo, built as a small Flask application and connected
            to Supabase so the prototype can preserve the state of the two-user email simulation during a browser session.
          </p>
          <p>
            A natural future improvement would be exposing <code>delete_email()</code> directly in the main menu,
            because the deletion method already exists in the classes but is not yet reachable from the interactive flow.
            Other possible extensions would include persistence with JSON, search by sender or subject, and unit tests for
            inbox index validation.
          </p>
        </section>

        <div class="actions">
          <a class="button button-primary" href="https://email-client.onrender.com" target="_blank" rel="noopener noreferrer">Open live demo</a>
          <a class="button button-secondary" href="{{ '/' | relative_url }}#blog">Back to blog</a>
          <a class="button button-secondary" href="{{ '/' | relative_url }}">Home</a>
        </div>
      </article>

      <aside class="side-card" aria-label="Post metadata">
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