# ☁️ CloudVault — File Upload System

> Day 5 of building one project per day until I land a FAANG-level job.

A cloud-style personal file storage system with drag & drop uploads, file management, and JWT authentication.

🔗 **Live Demo:** [Coming soon on Render]  
📁 **GitHub:** github.com/Haru-bit-code/file-upload-system

---

## ✨ Features

- **Drag & Drop Uploads** — Drop files or click to browse
- **JWT Authentication** — Secure login, data isolated per user
- **File Manager** — View, search, download, and delete your files
- **Upload Progress** — Real-time progress bar per file
- **Storage Stats** — Visual storage usage bar across all files
- **File Type Icons** — Auto-detected emoji icons for 20+ file types
- **Search** — Filter files by name instantly
- **Secure Storage** — UUID-renamed files on disk, original names in DB
- **16 MB limit** — Per-file size validation (server + client)
- **MIME Validation** — Only whitelisted file types accepted

---

## 🛠️ Tech Stack

| Layer       | Tech                        |
|-------------|----------------------------|
| Backend     | Python, Flask               |
| Database    | SQLite + SQLAlchemy ORM     |
| Auth        | JWT (PyJWT) + bcrypt        |
| File I/O    | Werkzeug, Python `os`       |
| Frontend    | Vanilla JS, HTML/CSS        |
| Design      | Dark glassmorphism          |
| Deployment  | Render (free tier)          |

---

## 🧠 Key Concepts (Interview-Ready)

### File Handling
- `werkzeug.utils.secure_filename` sanitizes uploads (prevents path traversal)
- Files stored with `uuid4()` names to avoid collisions and hide original names
- Original name stored in DB; served back via `Content-Disposition` header

### Security
- JWT token required for every API route via `@token_required` decorator
- `user_id` filter on every DB query — users can only see their own files
- File type whitelist — MIME types alone aren't trusted
- `MAX_CONTENT_LENGTH` enforced at Flask level (returns 413 automatically)

### Download Flow
- Server sends `send_file(..., as_attachment=True, download_name=original_name)`
- Frontend fetches with `Authorization: Bearer <token>` header, creates blob URL

---

## 📁 File Structure

```
file-upload-system/
├── app.py              # Flask backend (all routes + models)
├── requirements.txt
├── README.md
├── .gitignore
├── uploads/            # Created automatically (gitignored)
└── templates/
    └── index.html      # Full frontend SPA
```

---

## 🚀 Run Locally

```bash
git clone https://github.com/Haru-bit-code/file-upload-system
cd file-upload-system
pip install -r requirements.txt
python app.py
# Open http://localhost:5000
```

---

## ☁️ Deploy on Render

1. Push to GitHub
2. New Web Service → connect repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `python app.py`
5. Add env var: `SECRET_KEY=your-secure-random-string`

---

## 📡 API Reference

| Method | Endpoint                        | Auth | Description              |
|--------|---------------------------------|------|--------------------------|
| POST   | `/api/register`                 | No   | Create account           |
| POST   | `/api/login`                    | No   | Get JWT token            |
| POST   | `/api/upload`                   | Yes  | Upload a file            |
| GET    | `/api/files`                    | Yes  | List all your files      |
| GET    | `/api/files/<id>/download`      | Yes  | Download a file          |
| DELETE | `/api/files/<id>`               | Yes  | Delete a file            |
| GET    | `/api/stats`                    | Yes  | Storage stats            |

---

## 👤 Author

**Ansar Kamal** — Building in public, one project per day  
GitHub: [@Haru-bit-code](https://github.com/Haru-bit-code)  
#100DaysOfCode #BuildInPublic #OpenToWork
