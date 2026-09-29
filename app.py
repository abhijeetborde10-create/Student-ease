import streamlit as st
import sqlite3
import base64
import json
import re
import pandas as pd
from urllib.parse import quote
from pathlib import Path

DB = Path("student_ease.db")

def get_conn():
    con = sqllite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = get_conn()
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL, role TEXT NOT NULL, photo TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS listings(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_email TEXT NOT NULL, title TEXT NOT NULL, kind TEXT NOT NULL,
        audience TEXT NOT NULL, college TEXT NOT NULL, area TEXT NOT NULL,
        room_type TEXT, rent INTEGER NOT NULL, food INTEGER DEFAULT 0,
        distance REAL DEFAULT 0, gender TEXT DEFAULT 'Any', contact TEXT,
        description TEXT, photo TEXT, available INTEGER DEFAULT 1,
        photos TEXT, map_link TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS saved(
        student_email TEXT, listing_id INTEGER, PRIMARY KEY(student_email, listing_id)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS reviews(
        listing_id INTEGER, student_email TEXT, rating INTEGER, comment TEXT,
        PRIMARY KEY(listing_id, student_email)
    )""")
    # safe migration for older DB files
    try: cur.execute("ALTER TABLE users ADD COLUMN photo TEXT")
    except sqlite3.OperationalError: pass
    for col, coltype in [("photo","TEXT"),("available","INTEGER DEFAULT 1"),("photos","TEXT"),("map_link","TEXT")]:
        try: cur.execute(f"ALTER TABLE listings ADD COLUMN {col} {coltype}")
        except sqlite3.OperationalError: pass

    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                    ("Demo Student", "student@studentease.demo", "1234", "student"))
        cur.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                    ("Demo Owner", "owner@studentease.demo", "1234", "owner"))
    cur.execute("SELECT COUNT(*) FROM listings")
    if cur.fetchone()[0] == 0:
        rows = [
            ("owner@studentease.demo","Shree Residency PG","PG","11th/12th","Deogiri College","Chhatrapati Sambhajinagar","Double Sharing",4500,2500,0.7,"Any","9876543210","Furnished PG near college with Wi-Fi."),
            ("owner@studentease.demo","Campus Home","PG","CET/JEE","Deogiri College","Chhatrapati Sambhajinagar","Triple Sharing",3500,2200,1.1,"Any","9876543211","Budget-friendly student PG."),
            ("owner@studentease.demo","Maa Annapurna Mess","Mess","11th/12th","Deogiri College","Chhatrapati Sambhajinagar","Monthly",1800,1800,0.4,"Any","9876543212","Breakfast and dinner available."),
            ("owner@studentease.demo","Scholar Stay","Hostel","College Student","CSMSS College","Chhatrapati Sambhajinagar","Single",6500,3000,0.9,"Any","9876543213","Single room with study table."),
            ("owner@studentease.demo","Sahyadri Boys PG","PG","CET/JEE","MIT College","Chhatrapati Sambhajinagar","Double Sharing",4200,2000,1.4,"Male","9876543214","Safe student accommodation."),
            ("owner@studentease.demo","Aarohi Girls PG","PG","College Student","Deogiri College","Chhatrapati Sambhajinagar","Double Sharing",5000,2300,0.6,"Female","9876543215","Girls-only PG with security."),
        ]
        cur.executemany("""INSERT INTO listings
            (owner_email,title,kind,audience,college,area,room_type,rent,food,distance,gender,contact,description)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""", rows)
    con.commit(); con.close()

def query(sql, params=(), fetch=True):
    con = get_conn(); cur = con.cursor(); cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()] if fetch else None
    con.commit(); con.close()
    return rows

init_db()
st.set_page_config(page_title="Student Ease", page_icon="🏠", layout="wide")

for key, default in [("user", None), ("editing_id", None)]:
    if key not in st.session_state:
        st.session_state[key] = default

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def to_data_uri(f):
    if f is None: return None
    b64 = base64.b64encode(f.getvalue()).decode()
    return f"data:{f.type or 'image/jpeg'};base64,{b64}"

def avatar_url(name, photo=None):
    if photo: return photo
    return f"https://api.dicebear.com/7.x/adventurer/svg?seed={quote(name or 'Student')}&backgroundColor=f2d1d6,f7e9eb,e8c4c9&radius=50"

def whatsapp_link(contact):
    digits = re.sub(r"\D", "", contact or "")
    if not digits: return None
    if len(digits) == 10: digits = "91" + digits
    return f"https://wa.me/{digits}"

def get_photos(r):
    raw = r.get("photos")
    if raw:
        try:
            lst = json.loads(raw)
            if lst: return lst
        except Exception: pass
    return [r["photo"]] if r.get("photo") else []

def cover_html(r):
    photos = get_photos(r)
    if photos:
        return f'<img src="{photos[0]}" style="width:100%;max-height:190px;object-fit:cover;border-radius:14px;margin-bottom:12px;">'
    emoji = {"PG":"🏠","Hostel":"🏢","Mess":"🍽️"}.get(r["kind"],"🏠")
    return f'<div style="width:100%;height:120px;border-radius:14px;background:var(--maroon-100);display:flex;align-items:center;justify-content:center;font-size:44px;margin-bottom:12px;">{emoji}</div>'

def rating_summary(listing_id):
    row = query("SELECT AVG(rating) a, COUNT(*) c FROM reviews WHERE listing_id=?", (listing_id,))[0]
    if not row["a"]: return "No ratings yet", 0
    avg = round(row["a"], 1); full = int(round(avg))
    return f"{'⭐'*full}{'☆'*(5-full)} {avg} ({row['c']})", avg

def owner_info(owner_email):
    row = query("SELECT name, photo FROM users WHERE email=?", (owner_email,))
    cnt = query("SELECT COUNT(*) c FROM listings WHERE owner_email=?", (owner_email,))[0]["c"]
    name = row[0]["name"] if row else "Owner"
    photo = row[0]["photo"] if row else None
    return name, photo, cnt >= 3

def listing_card_html(r):
    available = r.get("available") != 0
    status_html = '<span class="se-badge status-ok">Available</span>' if available else '<span class="se-badge status-full">Full</span>'
    rating_str, _ = rating_summary(r["id"])
    owner_name, owner_photo, trusted = owner_info(r["owner_email"])
    trust_html = ' <span class="se-badge status-ok">🛡 Trusted Owner</span>' if trusted else ''
    map_html = f'<a href="{r["map_link"]}" target="_blank" style="color:var(--maroon-700);font-weight:600;font-size:13px;">📍 View on Google Maps</a>' if r.get("map_link") else ''
    return f"""
    <div class="se-card">
        {cover_html(r)}
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
            <img class="avatar-sm" src="{avatar_url(owner_name, owner_photo)}">
            <span style="font-size:13px;color:var(--muted);">Listed by <b>{owner_name}</b></span>{trust_html}
        </div>
        <span class="se-tag">{r["kind"].upper()}</span>
        <h3>{r["title"]}</h3>
        <div class="se-loc">{r["college"]} • {r["area"]} • {r["distance"]} km from college</div>
        <div class="se-price">₹{r["rent"]:,}<span style="font-size:14px;color:var(--muted);font-weight:500;">/month</span></div>
        <div class="se-meta">
            <span class="se-badge">{r["room_type"]}</span>
            <span class="se-badge">Food ₹{r["food"]:,}/mo</span>
            <span class="se-badge">{r["gender"]}</span>
            {status_html}
        </div>
        <div class="se-meta" style="margin-top:8px;">📞 <b>{r["contact"]}</b> &nbsp;•&nbsp; {rating_str}</div>
        <div style="margin-top:6px;">{map_html}</div>
    </div>"""

# ---------------------------------------------------------------------------
# THEME
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap');
:root{ --maroon-900:#4A0E18; --maroon-700:#6E1423; --maroon-100:#F7E9EB; --gold:#C7972C; --ink:#2A1418; --muted:#6E5457; --line:#EADCDD; }
html, body, [class*="css"]{ font-family:'Inter', sans-serif; color:var(--ink) !important; }
.stApp{ background:#FFFDFB !important; }
h1,h2,h3{ font-family:'Playfair Display', serif; }
#MainMenu, footer{ visibility:hidden; }
[data-testid="stWidgetLabel"] p, label, .stMarkdown, .stCaption, p, span{ color:var(--ink) !important; }
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input, [data-testid="stTextArea"] textarea,
[data-baseweb="select"] div, [data-baseweb="input"] input{ background:#FFFFFF !important; color:var(--ink) !important; border-color:var(--line) !important; }
[data-baseweb="select"] svg{ fill:var(--ink) !important; }
[data-testid="stSidebar"]{ background:var(--maroon-100) !important; border-right:1px solid var(--line); }
.se-brand{ display:flex; align-items:center; gap:14px; margin-bottom:2px; }
.se-brand .logo{ width:46px; height:46px; border-radius:12px; background:linear-gradient(135deg,var(--maroon-700),var(--maroon-900)); display:flex; align-items:center; justify-content:center; font-size:22px; color:#fff; flex-shrink:0; }
.se-title{ font-family:'Playfair Display',serif; font-weight:800; font-size:32px; color:var(--maroon-900) !important; margin:0; }
.se-sub{ color:var(--muted) !important; font-size:15px; margin-top:2px; }
.role-pill{ display:inline-block; padding:4px 14px; border-radius:999px; font-size:12px; font-weight:700; letter-spacing:.3px; background:#fff; color:var(--maroon-900) !important; border:1px solid var(--line); }
.role-pill.owner{ background:var(--maroon-900); color:#fff !important; }
.avatar-lg{ width:76px; height:76px; border-radius:50%; object-fit:cover; border:3px solid var(--maroon-700); }
.avatar-sm{ width:26px; height:26px; border-radius:50%; object-fit:cover; border:1px solid var(--maroon-700); }
.se-card{ border:1px solid var(--line); border-radius:18px; padding:20px 22px; margin:12px 0; background:#fff; box-shadow:0 1px 2px rgba(74,14,24,0.04); border-left:5px solid var(--maroon-700); }
.se-card h3{ margin:0 0 6px 0; font-size:20px; color:var(--ink) !important; }
.se-tag{ font-size:12px; color:var(--maroon-700) !important; font-weight:700; }
.se-loc{ color:var(--muted) !important; font-size:14px; margin:2px 0 10px 0; }
.se-price{ font-family:'Playfair Display',serif; font-size:26px; font-weight:800; color:var(--maroon-900) !important; }
.se-meta{ color:var(--muted) !important; font-size:13px; margin-top:8px; }
.se-badge{ display:inline-block; background:var(--maroon-100); color:var(--maroon-900) !important; border-radius:8px; padding:2px 10px; font-size:12px; font-weight:600; margin-right:6px; }
.se-badge.status-ok{ background:#DFF3E4; color:#1B7A3A !important; }
.se-badge.status-full{ background:#EDEDED; color:#666 !important; }
.wa-btn{ display:inline-block; background:#25D366; color:#fff !important; text-decoration:none; padding:8px 16px; border-radius:10px; font-weight:700; font-size:14px; margin-top:6px; }
.stat-tile{ background:var(--maroon-900); color:#fff; border-radius:16px; padding:18px 20px; }
.stat-tile .num{ font-family:'Playfair Display',serif; font-size:26px; font-weight:800; color:#fff !important; }
.stat-tile .lbl{ font-size:11px; opacity:.8; text-transform:uppercase; letter-spacing:.5px; color:#fff !important; }
.stButton>button{ border-radius:10px; font-weight:600; border:1px solid var(--maroon-700); }
.stButton>button[kind="primary"]{ background:var(--maroon-700); border-color:var(--maroon-700); }
.stButton>button[kind="primary"]:hover{ background:var(--maroon-900); border-color:var(--maroon-900); }
hr{ border-color:var(--line) !important; }
</style>
""", unsafe_allow_html=True)

def brand(subtitle):
    st.markdown(f"""<div class="se-brand"><div class="logo">🏠</div><div>
        <p class="se-title">Student Ease</p><div class="se-sub">{subtitle}</div></div></div>""", unsafe_allow_html=True)

def profile_widget():
    user = st.session_state.user
    row = query("SELECT photo FROM users WHERE email=?", (user["email"],))
    current = row[0]["photo"] if row and row[0]["photo"] else None
    st.markdown(f'<img class="avatar-lg" src="{avatar_url(user["name"], current)}">', unsafe_allow_html=True)
    st.write(f"**{user['name']}**")
    st.caption(user["email"])
    with st.expander("Change profile photo"):
        up = st.file_uploader("Upload a photo", type=["png","jpg","jpeg"], key="profile_upload")
        if up is not None:
            query("UPDATE users SET photo=? WHERE email=?", (to_data_uri(up), user["email"]), False)
            st.success("Profile photo updated."); st.rerun()
        st.caption("No photo yet? A cartoon avatar based on your name is used automatically.")

def login():
    left, right = st.columns([1, 1.2], gap="large")
    with left:
        st.markdown("""<div style="background:linear-gradient(160deg,#6E1423,#2A0810); border-radius:24px;
                    padding:48px 36px; color:#fff; height:420px; display:flex; flex-direction:column; justify-content:center;">
            <div style="font-size:40px;">🏠</div><h1 style="color:#fff; margin:14px 0 8px 0;">Student Ease</h1>
            <p style="color:#EAD7D9; font-size:16px; line-height:1.6;">Find a trusted PG, hostel or mess near your
            college — or list your property for students to discover, in one systematic place.</p></div>""", unsafe_allow_html=True)
    with right:
        st.write("")
        tab1, tab2 = st.tabs(["Login", "Create account"])
        with tab1:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Login", type="primary", use_container_width=True):
                row = query("SELECT name,email,role FROM users WHERE email=? AND password=?", (email, password))
                if row:
                    st.session_state.user = {"name": row[0]["name"], "email": row[0]["email"], "role": row[0]["role"]}
                    st.rerun()
                else: st.error("Invalid email or password.")
            st.info("Demo Student: student@studentease.demo / 1234\n\nDemo Owner: owner@studentease.demo / 1234")
        with tab2:
            name = st.text_input("Name", key="reg_name")
            email = st.text_input("Email", key="reg_email")
            password = st.text_input("Password", type="password", key="reg_password")
            role = st.selectbox("Account type", ["student", "owner"])
            if st.button("Create account", use_container_width=True):
                if not name or not email or not password:
                    st.warning("Please fill all fields.")
                else:
                    try:
                        query("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)", (name, email, password, role), False)
                        st.success("Account created. Please login.")
                    except sqlite3.IntegrityError:
                        st.error("Email already registered.")

def toggle_save(email, lid):
    exists = query("SELECT 1 FROM saved WHERE student_email=? AND listing_id=?", (email, lid))
    if exists: query("DELETE FROM saved WHERE student_email=? AND listing_id=?", (email, lid), False)
    else: query("INSERT OR IGNORE INTO saved(student_email,listing_id) VALUES(?,?)", (email, lid), False)
    st.rerun()

def listing_detail_block(r, email):
    photos = get_photos(r)
    if len(photos) > 1:
        st.image(photos, width=110)
    st.write("**Description:**", r["description"] or "—")
    wa = whatsapp_link(r["contact"])
    if wa: st.markdown(f'<a class="wa-btn" href="{wa}" target="_blank">💬 Chat on WhatsApp</a>', unsafe_allow_html=True)
    is_saved = bool(query("SELECT 1 FROM saved WHERE student_email=? AND listing_id=?", (email, r["id"])))
    if st.button("💔 Remove from saved" if is_saved else "❤️ Save listing", key=f"save{r['id']}"):
        toggle_save(email, r["id"])
    with st.form(f"review_form_{r['id']}"):
        st.write("**Rate this listing**")
        rating = st.slider("Your rating", 1, 5, 5, key=f"rate{r['id']}")
        comment = st.text_input("Comment (optional)", key=f"cmt{r['id']}")
        if st.form_submit_button("Submit review"):
            query("""INSERT INTO reviews(listing_id,student_email,rating,comment) VALUES(?,?,?,?)
                     ON CONFLICT(listing_id,student_email) DO UPDATE SET rating=excluded.rating, comment=excluded.comment""",
                  (r["id"], email, rating, comment), False)
            st.success("Review saved."); st.rerun()

def student_dashboard():
    listings = query("SELECT * FROM listings")
    colleges = ["All"] + sorted({r["college"] for r in listings}) if listings else ["All"]

    with st.sidebar:
        st.markdown('<span class="role-pill">STUDENT</span>', unsafe_allow_html=True)
        profile_widget()
        st.divider()
        st.markdown("#### 🔍 Filters")
        college = st.selectbox("College", colleges)
        kind = st.radio("Type", ["All", "PG", "Hostel", "Mess"])
        audience = st.selectbox("For", ["All", "11th/12th", "CET/JEE", "College Student"])
        gender = st.selectbox("Gender preference", ["Any", "Male", "Female"])
        max_rent = st.slider("Max rent (₹/month)", 1000, 15000, 10000, 500)
        max_distance = st.slider("Max distance (km)", 0.1, 5.0, 3.0, 0.1)
        only_available = st.checkbox("Only available", value=True)
        sort = st.selectbox("Sort by", ["Lowest rent", "Nearest college", "Top rated"])
        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state.user = None; st.rerun()

    brand("Compare verified PG, hostel and mess options published by owners near your college.")
    st.divider()
    email = st.session_state.user["email"]
    tab_browse, tab_saved = st.tabs(["🔍 Browse", "❤️ Saved"])

    with tab_browse:
        if not listings:
            st.info("No listings published yet. Check back soon.")
        else:
            search = st.text_input("Search by name, area or college", "")
            q = search.strip().lower()
            results = []
            for r in listings:
                if college != "All" and r["college"] != college: continue
                if kind != "All" and r["kind"] != kind: continue
                if audience != "All" and r["audience"] != audience: continue
                if gender != "Any" and r["gender"] not in ("Any", gender): continue
                if r["rent"] > max_rent or r["distance"] > max_distance: continue
                if only_available and r.get("available") == 0: continue
                if q and q not in r["title"].lower() and q not in r["area"].lower() and q not in r["college"].lower(): continue
                results.append(r)
            if sort == "Lowest rent": results.sort(key=lambda x: x["rent"])
            elif sort == "Nearest college": results.sort(key=lambda x: x["distance"])
            else: results.sort(key=lambda x: rating_summary(x["id"])[1], reverse=True)

            st.caption(f"{len(results)} matching option(s)")
            if not results:
                st.warning("No listing matches these filters. Try relaxing rent, distance, or 'Only available'.")
            for r in results:
                st.markdown(listing_card_html(r), unsafe_allow_html=True)
                with st.expander("View details, photos & contact owner"):
                    listing_detail_block(r, email)

    with tab_saved:
        saved_ids = [s["listing_id"] for s in query("SELECT listing_id FROM saved WHERE student_email=?", (email,))]
        mine = [r for r in listings if r["id"] in saved_ids]
        if not mine:
            st.info("Nothing saved yet — tap ❤️ Save listing on any option in Browse.")
        for r in mine:
            st.markdown(listing_card_html(r), unsafe_allow_html=True)
            with st.expander("View details, photos & contact owner"):
                listing_detail_block(r, email)

def render_listing_form(defaults=None, submit_label="Publish listing", form_key="add_listing"):
    d = defaults or {}
    with st.form(form_key):
        photos = get_photos(d)
        if photos: st.image(photos, width=110, caption=["Current"]*len(photos))
        photo_files = st.file_uploader("Listing photos (optional, multiple allowed)", type=["png","jpg","jpeg"],
                                        accept_multiple_files=True, key=form_key+"_photos")
        title = st.text_input("Listing name", value=d.get("title", ""))
        kind = st.selectbox("Type", ["PG","Hostel","Mess"], index=["PG","Hostel","Mess"].index(d.get("kind","PG")))
        audience = st.selectbox("Target students", ["11th/12th","CET/JEE","College Student","All"],
                                 index=["11th/12th","CET/JEE","College Student","All"].index(d.get("audience","11th/12th")))
        college = st.text_input("Nearby college", value=d.get("college", ""))
        area = st.text_input("Area / locality", value=d.get("area", ""))
        room = st.selectbox("Room / plan", ["Single","Double Sharing","Triple Sharing","Monthly"],
                             index=["Single","Double Sharing","Triple Sharing","Monthly"].index(d.get("room_type","Single")))
        rent = st.number_input("Rent per month (₹)", min_value=0, value=int(d.get("rent", 3000)), step=500)
        food = st.number_input("Food / mess cost per month (₹)", min_value=0, value=int(d.get("food", 0)), step=100)
        distance = st.number_input("Distance from college (km)", min_value=0.0, value=float(d.get("distance", 1.0)), step=0.1)
        gender = st.selectbox("Gender", ["Any","Male","Female"], index=["Any","Male","Female"].index(d.get("gender","Any")))
        contact = st.text_input("Contact number", value=d.get("contact", ""))
        map_link = st.text_input("Google Maps link (optional)", value=d.get("map_link", "") or "")
        desc = st.text_area("Description", value=d.get("description", ""))
        available = st.checkbox("Currently available", value=d.get("available", 1) != 0)
        submitted = st.form_submit_button(submit_label, type="primary")
        if submitted:
            if not title or not college or not area or not contact:
                st.error("Please fill listing name, college, area and contact.")
                return None
            photos_json = json.dumps([to_data_uri(f) for f in photo_files]) if photo_files else d.get("photos")
            return dict(title=title, kind=kind, audience=audience, college=college, area=area,
                        room_type=room, rent=rent, food=food, distance=distance, gender=gender,
                        contact=contact, description=desc, available=1 if available else 0,
                        photos=photos_json, map_link=map_link)
    return None

def owner_dashboard():
    with st.sidebar:
        st.markdown('<span class="role-pill owner">OWNER</span>', unsafe_allow_html=True)
        profile_widget()
        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state.user = None; st.rerun()

    brand("Publish and manage your PG, hostel or mess listings.")
    st.divider()
    email = st.session_state.user["email"]
    mine = query("SELECT * FROM listings WHERE owner_email=?", (email,))

    s1, s2, s3 = st.columns(3)
    total = len(mine)
    avg_rent = int(sum(m["rent"] for m in mine) / total) if total else 0
    colleges_covered = len({m["college"] for m in mine})
    for col, num, lbl in [(s1, total, "Published listings"), (s2, f"₹{avg_rent:,}", "Average rent"), (s3, colleges_covered, "Colleges covered")]:
        col.markdown(f'<div class="stat-tile"><div class="num">{num}</div><div class="lbl">{lbl}</div></div>', unsafe_allow_html=True)

    st.write("")
    tab_add, tab_manage, tab_economy = st.tabs(["➕ Publish new listing", "📋 Your published work", "📊 Economy overview"])

    with tab_add:
        data = render_listing_form()
        if data:
            query("""INSERT INTO listings(owner_email,title,kind,audience,college,area,room_type,rent,food,distance,gender,contact,description,available,photos,map_link)
                     VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (email, data["title"], data["kind"], data["audience"], data["college"], data["area"],
                   data["room_type"], data["rent"], data["food"], data["distance"], data["gender"],
                   data["contact"], data["description"], data["available"], data["photos"], data["map_link"]), False)
            st.success("Listing published."); st.rerun()

    with tab_manage:
        if not mine:
            st.info("You haven't published anything yet — use the 'Publish new listing' tab.")
        for m in mine:
            mid = m["id"]
            st.markdown(listing_card_html(m), unsafe_allow_html=True)
            b1, b2 = st.columns([1, 1])
            edit_clicked = b1.button("Edit", key=f"edit{mid}", use_container_width=True)
            delete_clicked = b2.button("Delete", key=f"del{mid}", use_container_width=True)
            if edit_clicked:
                st.session_state.editing_id = mid if st.session_state.editing_id != mid else None
            if delete_clicked:
                query("DELETE FROM listings WHERE id=?", (mid,), False)
                st.success("Listing deleted."); st.rerun()
            if st.session_state.editing_id == mid:
                updated = render_listing_form(defaults=m, submit_label="Save changes", form_key=f"edit_form_{mid}")
                if updated:
                    query("""UPDATE listings SET title=?,kind=?,audience=?,college=?,area=?,room_type=?,
                             rent=?,food=?,distance=?,gender=?,contact=?,description=?,available=?,photos=?,map_link=? WHERE id=?""",
                          (updated["title"], updated["kind"], updated["audience"], updated["college"], updated["area"],
                           updated["room_type"], updated["rent"], updated["food"], updated["distance"],
                           updated["gender"], updated["contact"], updated["description"], updated["available"],
                           updated["photos"], updated["map_link"], mid), False)
                    st.session_state.editing_id = None
                    st.success("Listing updated."); st.rerun()

    with tab_economy:
        st.caption("Visible only to you — this is not shown to students.")
        if not mine:
            st.info("Publish a listing to see your economy overview.")
        else:
            occupied = [m for m in mine if m.get("available") == 0]
            vacant = [m for m in mine if m.get("available") != 0]
            current_revenue = sum(m["rent"] for m in occupied)
            potential_revenue = sum(m["rent"] for m in vacant)
            occupancy = round(len(occupied) / len(mine) * 100)
            ids = [m["id"] for m in mine]
            interest = query(f"SELECT COUNT(*) c FROM saved WHERE listing_id IN ({','.join('?'*len(ids))})", ids)[0]["c"]
            ratings = [rating_summary(m["id"])[1] for m in mine if rating_summary(m["id"])[1] > 0]
            avg_rating = round(sum(ratings)/len(ratings), 1) if ratings else None

            e1, e2, e3, e4 = st.columns(4)
            for col, num, lbl in [
                (e1, f"₹{current_revenue:,}", "Current monthly income (occupied)"),
                (e2, f"₹{potential_revenue:,}", "Potential extra income (vacant)"),
                (e3, f"{occupancy}%", "Occupancy rate"),
                (e4, interest, "Students who saved your listings"),
            ]:
                col.markdown(f'<div class="stat-tile"><div class="num">{num}</div><div class="lbl">{lbl}</div></div>', unsafe_allow_html=True)

            if avg_rating:
                st.metric("Average rating across your listings", f"{avg_rating} / 5")

            kind_counts = {}
            for m in mine: kind_counts[m["kind"]] = kind_counts.get(m["kind"], 0) + 1
            df = pd.DataFrame({"Type": list(kind_counts.keys()), "Listings": list(kind_counts.values())}).set_index("Type")
            st.bar_chart(df)

if st.session_state.user is None:
    login()
elif st.session_state.user["role"] == "student":
    student_dashboard()
else:
    owner_dashboard()
