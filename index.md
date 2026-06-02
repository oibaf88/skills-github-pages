from pathlib import Path
import re

candidates = [
    Path("/mnt/data/Pegado text(1).txt"),
    Path("/mnt/data/Pegado text.txt"),
    Path("/mnt/data/index_fixed_no_overlap.html"),
]

input_path = next((p for p in candidates if p.exists()), None)
if input_path is None:
    raise FileNotFoundError("No he encontrado el archivo index/index.md adjunto en /mnt/data.")

text = input_path.read_text(encoding="utf-8", errors="replace")

old_patterns = [
    r'href="skills-github-pages/_posts/2026-05-28/small_user_validation_function\.md"',
    r'href="_posts/2026-05-28/small_user_validation_function\.md"',
    r'href="/skills-github-pages/_posts/2026-05-28/small_user_validation_function\.md"',
    r'href="skills-github-pages/_posts/2026-06-02-uservalidation\.md"',
    r'href="_posts/2026-06-02-uservalidation\.md"',
    r'href="/skills-github-pages/_posts/2026-06-02-uservalidation\.md"',
]

replacement = 'href="{{ \'/blog/uservalidation/\' | relative_url }}"'

updated = text
replacements = 0

for pattern in old_patterns:
    updated, n = re.subn(pattern, replacement, updated)
    replacements += n

# Fallback: replace any anchor href containing the old markdown filename.
if replacements == 0:
    updated, n = re.subn(
        r'<a\s+href="[^"]*small_user_validation_function\.md"\s*>',
        '<a href="{{ \'/blog/uservalidation/\' | relative_url }}">',
        updated,
        flags=re.IGNORECASE
    )
    replacements += n

# Fallback: replace any anchor href containing uservalidation in _posts.
if replacements == 0:
    updated, n = re.subn(
        r'<a\s+href="[^"]*_posts/[^"]*uservalidation[^"]*"\s*>',
        '<a href="{{ \'/blog/uservalidation/\' | relative_url }}">',
        updated,
        flags=re.IGNORECASE
    )
    replacements += n

output_path = Path("/mnt/data/index_updated_blog_link.md")
updated = updated.replace("\r\n", "\n")
output_path.write_text(updated, encoding="utf-8")

print(f"Archivo de entrada: {input_path}")
print(f"Archivo actualizado: {output_path}")
print(f"Reemplazos realizados: {replacements}")
print("Enlace correcto:")
print("{{ '/blog/uservalidation/' | relative_url }}")
