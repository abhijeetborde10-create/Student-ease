import streamlit as st
import sqlite3
from pathlib import Path

DB = Path("student_ease.db")

def get_conn():
    return sqlite3.connect(DB)

def init_db():
    con = get_conn()
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS listings(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_email TEXT NOT NULL,
        title TEXT NOT NULL,
        kind TEXT NOT NULL,
        audience TEXT NOT NULL,
        college TEXT NOT NULL,
        area TEXT NOT NULL,
        room_type TEXT,
        rent INTEGER NOT NULL,
        food INTEGER DEFAULT 0,
        distance REAL DEFAULT 0,
        gender TEXT DEFAULT 'Any',
        contact TEXT,
        description TEXT
    )""")
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
    con.commit()
    con.close()

def query(sql, params=(), fetch=True):
    con = get_conn()
    cur = con.cursor()
    cur.execute(sql, params)
    data = cur.fetchall() if fetch else None
    con.commit()
    con.close()
    return data

init_db()

st.set_page_config(page_title="Student Ease", page_icon="🏠", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = None
if "editing_id" not in st.session_state:
    st.session_state.editing_id = None

# ---------------------------------------------------------------------------
# THEME — maroon & white, systematic and card-driven
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap');

:root{
    --maroon-900:#4A0E18;
    --maroon-700:#6E1423;
    --maroon-600:#84172B;
    --maroon-100:#F7E9EB;
    --gold:#C7972C;
    --ink:#2A1418;
    --muted:#8B6A6E;
    --line:#EADCDD;
}

html, body, [class*="css"]{ font-family:'Inter', sans-serif; color:var(--ink); }
.stApp{ background:#FFFDFB; }
h1,h2,h3{ font-family:'Playfair Display', serif; }

/* Hide default chrome clutter */
#MainMenu, footer{ visibility:hidden; }

/* Brand header */
.se-brand{ display:flex; align-items:center; gap:14px; margin-bottom:2px; }
.se-brand .logo{
    width:46px; height:46px; border-radius:12px;
    background:linear-gradient(135deg,var(--maroon-700),var(--maroon-900));
    display:flex; align-items:center; justify-content:center;
    font-size:22px; color:#fff; flex-shrink:0;
}
.se-title{ font-family:'Playfair Display',serif; font-weight:800; font-size:32px; color:var(--maroon-900); margin:0; }
.se-sub{ color:var(--muted); font-size:15px; margin-top:2px; }

/* Role pill */
.role-pill{
    display:inline-block; padding:4px 14px; border-radius:999px;
    font-size:12px; font-weight:700; letter-spacing:.3px;
    background:var(--maroon-100); color:var(--maroon-900); border:1px solid var(--line);
}
.role-pill.owner{ background:var(--maroon-900); color:#fff; }

/* Listing card */
.se-card{
    border:1px solid var(--line); border-radius:18px; padding:20px 22px;
    margin:12px 0; background:#fff; box-shadow:0 1px 2px rgba(74,14,24,0.04);
    border-left:5px solid var(--maroon-700);
}
.se-card h3{ margin:0 0 6px 0; font-size:20px; color:var(--ink); }
.se-tag{ font-size:12px; color:var(--maroon-700); font-weight:700; }
.se-loc{ color:var(--muted); font-size:14px; margin:2px 0 10px 0; }
.se-price{ font-family:'Playfair Display',serif; font-size:26px; font-weight:800; color:var(--maroon-900); }
.se-meta{ color:var(--muted); font-size:13px; margin-top:8px; }
.se-badge{
    display:inline-block; background:var(--maroon-100); color:var(--maroon-900);
    border-radius:8px; padding:2px 10px; font-size:12px; font-weight:600; margin-right:6px;
}

/* Stat tiles for owner */
.stat-tile{
    background:var(--maroon-900); color:#fff; border-radius:16px; padding:18px 20px;
}
.stat-tile .num{ font-family:'Playfair Display',serif; font-size:30px; font-weight:800; }
.stat-tile .lbl{ font-size:12px; opacity:.8; text-transform:uppercase; letter-spacing:.5px; }

/* Buttons */
.stButton>button{
    border-radius:10px; font-weight:600; border:1px solid var(--maroon-700);
}
.stButton>button[kind="primary"]{
    background:var(--maroon-700); border-color:var(--maroon-700);
}
.stButton>button[kind="primary"]:hover{ background:var(--maroon-900); border-color:var(--maroon-900); }

hr{ border-color:var(--line) !important; }
</style>
""", unsafe_allow_html=True)


def brand(subtitle):
    st.markdown(f"""
    <div class="se-brand">
        <div class="logo">🏠</div>
        <div>
            <p class="se-title">Student Ease</p>
            <div class="se-sub">{subtitle}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def login():
    left, right = st.columns([1, 1.2], gap="large")
    with left:
        st.markdown("""
        <div style="background:linear-gradient(160deg,#6E1423,#2A0810); border-radius:24px;
                    padding:48px 36px; color:#fff; height:420px; display:flex;
                    flex-direction:column; justify-content:center;">
            <div style="font-size:40px;">🏠</div>
            <h1 style="color:#fff; margin:14px 0 8px 0;">Student Ease</h1>
            <p style="color:#EAD7D9; font-size:16px; line-height:1.6;">
            Find a trusted PG, hostel or mess near your college — or list your
            property for students to discover, in one systematic place.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with right:
        st.write("")
        tab1, tab2 = st.tabs(["Login", "Create account"])
        with tab1:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Login", type="primary", use_container_width=True):
                row = query("SELECT name,email,role FROM users WHERE email=? AND password=?", (email, password))
                if row:
                    st.session_state.user = {"name": row[0][0], "email": row[0][1], "role": row[0][2]}
                    st.rerun()
                else:
                    st.error("Invalid email or password.")
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


def student_dashboard():
    with st.sidebar:
        st.markdown(f'<span class="role-pill">STUDENT</span>', unsafe_allow_html=True)
        st.write(f"**{st.session_state.user['name']}**")
        st.caption(st.session_state.user['email'])
        if st.button("Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    brand("Compare verified PG, hostel and mess options published by owners near your college.")
    st.divider()

    listings = query("SELECT * FROM listings")
    if not listings:
        st.info("No listings published yet. Check back soon.")
        return

    colleges = ["All"] + sorted({r[5] for r in listings})
    kinds = ["All", "PG", "Hostel", "Mess"]
    audiences = ["All", "11th/12th", "CET/JEE", "College Student"]
    genders = ["Any", "Male", "Female"]

    c1, c2, c3, c4 = st.columns(4)
    college = c1.selectbox("College", colleges)
    kind = c2.selectbox("Type", kinds)
    audience = c3.selectbox("For", audiences)
    gender = c4.selectbox("Gender preference", genders)

    c5, c6, c7 = st.columns(3)
    max_rent = c5.slider("Maximum rent (₹/month)", 1000, 15000, 10000, 500)
    max_distance = c6.slider("Maximum distance (km)", 0.1, 5.0, 3.0, 0.1)
    sort = c7.selectbox("Sort", ["Lowest rent", "Nearest college"])

    results = []
    for r in listings:
        # 0 id,1 owner,2 title,3 kind,4 audience,5 college,6 area,7 room,8 rent,9 food,10 distance,11 gender,12 contact,13 desc
        if college != "All" and r[5] != college: continue
        if kind != "All" and r[3] != kind: continue
        if audience != "All" and r[4] != audience: continue
        if gender != "Any" and r[11] not in ("Any", gender): continue
        if r[8] > max_rent or r[10] > max_distance: continue
        results.append(r)

    results.sort(key=lambda x: x[8] if sort == "Lowest rent" else x[10])

    st.caption(f"{len(results)} matching option(s)")
    if not results:
        st.warning("No listing matches these filters. Try increasing rent or distance.")

    for r in results:
        st.markdown(f"""
        <div class="se-card">
            <span class="se-tag">{r[3].upper()}</span>
            <h3>{r[2]}</h3>
            <div class="se-loc">{r[5]} • {r[6]} • {r[10]} km from college</div>
            <div class="se-price">₹{r[8]:,}<span style="font-size:14px;color:var(--muted);font-weight:500;">/month</span></div>
            <div class="se-meta">
                <span class="se-badge">{r[7]}</span>
                <span class="se-badge">Food ₹{r[9]:,}/mo</span>
                <span class="se-badge">{r[11]}</span>
            </div>
            <div class="se-meta" style="margin-top:8px;">For: {r[4]}</div>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("View details & contact owner"):
            st.write("**Description:**", r[13] or "—")
            st.write("**Contact number:**", r[12])
            st.button("Save listing", key=f"save{r[0]}")


def render_listing_form(defaults=None, submit_label="Publish listing", form_key="add_listing"):
    d = defaults or {}
    with st.form(form_key):
        title = st.text_input("Listing name", value=d.get("title", ""))
        kind = st.selectbox("Type", ["PG", "Hostel", "Mess"], index=["PG","Hostel","Mess"].index(d.get("kind","PG")))
        audience = st.selectbox("Target students", ["11th/12th", "CET/JEE", "College Student", "All"],
                                 index=["11th/12th","CET/JEE","College Student","All"].index(d.get("audience","11th/12th")))
        college = st.text_input("Nearby college", value=d.get("college", ""))
        area = st.text_input("Area / locality", value=d.get("area", ""))
        room = st.selectbox("Room / plan", ["Single", "Double Sharing", "Triple Sharing", "Monthly"],
                             index=["Single","Double Sharing","Triple Sharing","Monthly"].index(d.get("room_type","Single")))
        rent = st.number_input("Rent per month (₹)", min_value=0, value=d.get("rent", 3000), step=500)
        food = st.number_input("Food / mess cost per month (₹)", min_value=0, value=d.get("food", 0), step=100)
        distance = st.number_input("Distance from college (km)", min_value=0.0, value=float(d.get("distance", 1.0)), step=0.1)
        gender = st.selectbox("Gender", ["Any", "Male", "Female"], index=["Any","Male","Female"].index(d.get("gender","Any")))
        contact = st.text_input("Contact number", value=d.get("contact", ""))
        desc = st.text_area("Description", value=d.get("description", ""))
        submitted = st.form_submit_button(submit_label, type="primary")
        if submitted:
            if not title or not college or not area or not contact:
                st.error("Please fill listing name, college, area and contact.")
                return None
            return dict(title=title, kind=kind, audience=audience, college=college, area=area,
                        room_type=room, rent=rent, food=food, distance=distance, gender=gender,
                        contact=contact, description=desc)
    return None


def owner_dashboard():
    with st.sidebar:
        st.markdown(f'<span class="role-pill owner">OWNER</span>', unsafe_allow_html=True)
        st.write(f"**{st.session_state.user['name']}**")
        st.caption(st.session_state.user['email'])
        if st.button("Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    brand("Publish and manage your PG, hostel or mess listings.")
    st.divider()

    mine = query("SELECT id,title,kind,college,area,rent,food,distance,room_type,audience,gender,contact,description FROM listings WHERE owner_email=?",
                 (st.session_state.user["email"],))

    s1, s2, s3 = st.columns(3)
    total = len(mine)
    avg_rent = int(sum(m[5] for m in mine) / total) if total else 0
    colleges_covered = len({m[3] for m in mine})
    for col, num, lbl in [(s1, total, "Published listings"), (s2, f"₹{avg_rent:,}", "Average rent"), (s3, colleges_covered, "Colleges covered")]:
        col.markdown(f'<div class="stat-tile"><div class="num">{num}</div><div class="lbl">{lbl}</div></div>', unsafe_allow_html=True)

    st.write("")
    tab_add, tab_manage = st.tabs(["➕ Publish new listing", "📋 Your published work"])

    with tab_add:
        data = render_listing_form()
        if data:
            query("""INSERT INTO listings(owner_email,title,kind,audience,college,area,room_type,rent,food,distance,gender,contact,description)
                     VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (st.session_state.user["email"], data["title"], data["kind"], data["audience"], data["college"],
                   data["area"], data["room_type"], data["rent"], data["food"], data["distance"], data["gender"],
                   data["contact"], data["description"]), False)
            st.success("Listing published.")
            st.rerun()

    with tab_manage:
        if not mine:
            st.info("You haven't published anything yet — use the 'Publish new listing' tab.")
        for m in mine:
            mid, mtitle, mkind, mcollege, marea, mrent, mfood, mdist, mroom, maudience, mgender, mcontact, mdesc = m
            st.markdown(f"""
            <div class="se-card">
                <span class="se-tag">{mkind.upper()}</span>
                <h3>{mtitle}</h3>
                <div class="se-loc">{mcollege} • {marea} • {mdist} km from college</div>
                <div class="se-price">₹{mrent:,}<span style="font-size:14px;color:var(--muted);font-weight:500;">/month</span></div>
            </div>
            """, unsafe_allow_html=True)
            b1, b2 = st.columns([1, 1])
            edit_clicked = b1.button("Edit", key=f"edit{mid}", use_container_width=True)
            delete_clicked = b2.button("Delete", key=f"del{mid}", use_container_width=True)
            if edit_clicked:
                st.session_state.editing_id = mid if st.session_state.editing_id != mid else None
            if delete_clicked:
                query("DELETE FROM listings WHERE id=?", (mid,), False)
                st.success("Listing deleted.")
                st.rerun()
            if st.session_state.editing_id == mid:
                defaults = dict(title=mtitle, kind=mkind, audience=maudience, college=mcollege, area=marea,
                                 room_type=mroom, rent=mrent, food=mfood, distance=mdist, gender=mgender,
                                 contact=mcontact, description=mdesc)
                updated = render_listing_form(defaults=defaults, submit_label="Save changes", form_key=f"edit_form_{mid}")
                if updated:
                    query("""UPDATE listings SET title=?,kind=?,audience=?,college=?,area=?,room_type=?,
                             rent=?,food=?,distance=?,gender=?,contact=?,description=? WHERE id=?""",
                          (updated["title"], updated["kind"], updated["audience"], updated["college"], updated["area"],
                           updated["room_type"], updated["rent"], updated["food"], updated["distance"],
                           updated["gender"], updated["contact"], updated["description"], mid), False)
                    st.session_state.editing_id = None
                    st.success("Listing updated.")
                    st.rerun()


if st.session_state.user is None:
    login()
elif st.session_state.user["role"] == "student":
    student_dashboard()
else:
    owner_dashboard()
