# eHealth Developer Portfolio

A personal portfolio website for **B. Fabio Mejías Fernández**, showcasing digital health development work, clinical software, and eHealth projects.

## 📋 Quick Navigation

- **🏠 [Homepage](index.html)** – Main portfolio landing page with hero section and overview
- **📧 [Newsletter Signup](signup.html)** – Subscribe to updates about eHealth development and digital health tools
- **❌ [404 Error Page](404.md)** – Custom error page for missing content

## ✨ Key Features

### Main Portfolio (`index.html`)
- **Professional hero section** with gradient text effects
- **About section** – Overview of the portfolio and learning path
- **Focus areas** – Three pillars of work:
  - Clinical software development
  - Health data management and APIs
  - AI-assisted tools for eHealth
- **Development progress timeline** – Roadmap for portfolio evolution
- **Blog section** – Technical notes and development logs
- **Contact section** – Direct contact information and call-to-action

### Newsletter Signup (`signup.html`)
- **Validation** – Client-side form validation for name and email
- **Backend integration** – Sends subscriptions to Python API endpoint
- **Privacy notice** – Clear data collection and usage policies
- **Responsive design** – Works on all device sizes

### Error Page (`404.md`)
- **Custom 404 design** – Styled error page with decorative cat illustration
- **Navigation helpers** – Links back to homepage and blog sections
- **Multilingual support** – Spanish and English content

## 🎯 Color Scheme & Design System

All pages use a **consistent techno/cyberpunk aesthetic** with these CSS variables:

| Variable | Value | Purpose |
|----------|-------|---------|
| `--accent` | `#00f5ff` | Primary cyan color, glows and highlights |
| `--accent-2` | `#00ff9c` | Secondary green, accents and borders |
| `--warning` | `#b8ff3d` | Yellow-green for alerts and labels |
| `--danger` | `#ff173d` | Red for errors and warning states |
| `--text` | `#f8fbff` | Main text color |
| `--muted` | `#8ca0b8` | Secondary text color |
| `--bg` | `#000000` | Pure black background |
| `--card` | `rgba(2, 8, 14, 0.82)` | Card and section backgrounds |

## 📱 Responsive Breakpoints

- **Tablet** – `@media (max-width: 980px)` – Single column layout
- **Mobile** – `@media (max-width: 720px)` – Adjusted navigation
- **Small Mobile** – `@media (max-width: 520px)` – Minimal padding and sizing

## 🔗 Cross-References

### From Homepage (`index.html`):
- Link to newsletter signup: `<a href="/signup.html">` or `<a href="signup.html">`
- Link to blog posts: See `#blog` section and internal links
- Navigation menu anchors: `#about`, `#focus`, `#progress`, `#blog`, `#contact`

### From Newsletter (`signup.html`):
- Back to homepage: `<a href="/">Home</a>`
- Homepage sections: `href="/#about"`, `href="/#focus"`, etc.
- Blog section: `href="/#blog"`

### From 404 Page (`404.md`):
- Back to homepage: `{{ '/' | relative_url }}`
- Blog section: `{{ '/' | relative_url }}#blog`
- **Note:** Uses Jekyll template syntax for GitHub Pages compatibility

## ⚙️ Configuration

### `_config.yml`
The site uses Jekyll for GitHub Pages. Key settings:
- **Theme**: Minimal with custom styling
- **Markdown processor**: kramdown
- **Output directory**: `_site/`

### `CNAME`
Custom domain configuration for GitHub Pages.

## 📝 API Integration

The newsletter signup form connects to:
```javascript
const NEWSLETTER_API_ENDPOINT = "https://skills-github-pages-2.onrender.com/subscribe";
```

**To configure:**
1. Replace the endpoint URL with your deployed Python API
2. Ensure CORS is properly configured on your backend
3. Verify the API accepts POST requests with:
   ```json
   {
     "name": "string",
     "email": "string",
     "consent": boolean,
     "source": "bfab.io/signup"
   }
   ```

## 🧪 Form Validation Rules

The newsletter form validates:
- ✅ **Name**: Must be greater than 2 characters
- ✅ **Email**: Must match valid email format (`^[^\s@]+@[^\s@]+\.[^\s@]+$`)
- ✅ **Consent**: Must be explicitly accepted
- ❌ **No passwords**: Never requested or stored

## 📄 Page Structure

```
/
├── index.html           # Main portfolio (HTML)
├── signup.html          # Newsletter form (HTML)
├── 404.md              # Error page (Markdown + HTML)
├── README.md           # This file
├── _config.yml         # Jekyll configuration
├── CNAME               # Custom domain
├── LICENSE             # MIT License
└── _posts/             # Blog posts (future)
```

## 🚀 Development Progress

| Date | Milestone | Status |
|------|-----------|--------|
| 2026-05-18 | Portfolio initialized | ✅ Complete |
| TBD | Project gallery | 🚧 In progress |
| TBD | Technical notes | 📋 Planned |
| TBD | Blog posts | 📋 Planned |

## 📧 Contact & Support

- **Email**: [mejias@bfab.io](mailto:mejias@bfab.io)
- **Newsletter**: [Subscribe via signup page](signup.html)
- **GitHub**: [oibaf88](https://github.com/oibaf88)

## 📜 License

This project is licensed under the **MIT License** – see [LICENSE](LICENSE) file for details.

---

**© 2026 B. Fabio Mejías Fernández** | Built with ❤️ as a work in progress
