
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
    # Demo users
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                    ("Demo Student","student@studentease.demo","1234","student"))
        cur.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                    ("Demo Owner","owner@studentease.demo","1234","owner"))
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

st.markdown("""
<style>
.main-title {font-size:42px;font-weight:800;margin-bottom:0}
.sub {font-size:18px;color:#667085}
.card {padding:18px;border:1px solid #e5e7eb;border-radius:16px;margin:8px 0;background:#fff}
.price {font-size:25px;font-weight:800}
.small {color:#667085;font-size:14px}
</style>
""", unsafe_allow_html=True)

def login():
    st.markdown('<div class="main-title">🏠 Student Ease</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub">Find a student-friendly PG, hostel or mess near your college.</div>', unsafe_allow_html=True)
    st.divider()
    tab1, tab2 = st.tabs(["Login", "Create account"])
    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", type="primary", use_container_width=True):
            row = query("SELECT name,email,role FROM users WHERE email=? AND password=?", (email,password))
            if row:
                st.session_state.user = {"name":row[0][0],"email":row[0][1],"role":row[0][2]}
                st.rerun()
            else:
                st.error("Invalid email or password.")
        st.info("Demo Student: student@studentease.demo / 1234\n\nDemo Owner: owner@studentease.demo / 1234")
    with tab2:
        name = st.text_input("Name", key="reg_name")
        email = st.text_input("Email", key="reg_email")
        password = st.text_input("Password", type="password", key="reg_password")
        role = st.selectbox("Account type", ["student","owner"])
        if st.button("Create account", use_container_width=True):
            if not name or not email or not password:
                st.warning("Please fill all fields.")
            else:
                try:
                    query("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",(name,email,password,role),False)
                    st.success("Account created. Please login.")
                except sqlite3.IntegrityError:
                    st.error("Email already registered.")

def student_dashboard():
    st.sidebar.success(f"Logged in as {st.session_state.user['name']}")
    if st.sidebar.button("Logout"):
        st.session_state.user=None
        st.rerun()

    st.markdown('<div class="main-title">Find your stay & food</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub">Compare options by college, category, sharing, distance and rent.</div>', unsafe_allow_html=True)
    st.divider()

    listings = query("SELECT * FROM listings")
    colleges = ["All"] + sorted({r[5] for r in listings})
    kinds = ["All","PG","Hostel","Mess"]
    audiences = ["All","11th/12th","CET/JEE","College Student"]
    genders = ["Any","Male","Female"]

    c1,c2,c3,c4 = st.columns(4)
    college = c1.selectbox("College", colleges)
    kind = c2.selectbox("Type", kinds)
    audience = c3.selectbox("For", audiences)
    gender = c4.selectbox("Gender preference", genders)

    c5,c6,c7 = st.columns(3)
    max_rent = c5.slider("Maximum rent (₹/month)", 1000, 15000, 10000, 500)
    max_distance = c6.slider("Maximum distance (km)", 0.1, 5.0, 3.0, 0.1)
    sort = c7.selectbox("Sort", ["Lowest rent","Nearest college"])

    results = []
    for r in listings:
        # indexes: 0 id,1 owner,2 title,3 kind,4 audience,5 college,6 area,7 room,8 rent,9 food,10 distance,11 gender,12 contact,13 desc
        if college!="All" and r[5]!=college: continue
        if kind!="All" and r[3]!=kind: continue
        if audience!="All" and r[4]!=audience: continue
        if gender!="Any" and r[11] not in ("Any",gender): continue
        if r[8] > max_rent or r[10] > max_distance: continue
        results.append(r)

    if sort=="Lowest rent":
        results.sort(key=lambda x:x[8])
    else:
        results.sort(key=lambda x:x[10])

    st.caption(f"{len(results)} matching option(s)")
    if not results:
        st.warning("No listing matches these filters. Try increasing rent/distance.")
    for r in results:
        st.markdown(f"""
        <div class="card">
        <h3>{r[2]} <span class="small">• {r[3]}</span></h3>
        <b>{r[5]}</b> • {r[6]} • {r[10]} km away<br>
        <span class="price">₹{r[8]:,}/month</span> &nbsp; {r[7]} &nbsp; | &nbsp; Food: ₹{r[9]:,}/month<br>
        <span class="small">For: {r[4]} • {r[11]} • {r[13]}</span>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("View details / contact"):
            st.write("**Description:**", r[13])
            st.write("**Contact owner:**", r[12])
            st.button("Save listing", key=f"save{r[0]}")

def owner_dashboard():
    st.sidebar.success(f"Owner: {st.session_state.user['name']}")
    if st.sidebar.button("Logout"):
        st.session_state.user=None
        st.rerun()
    st.header("🏢 Owner Dashboard")
    st.write("Add and manage your PG, hostel or mess listing.")

    with st.form("add_listing"):
        title=st.text_input("Listing name")
        kind=st.selectbox("Type",["PG","Hostel","Mess"])
        audience=st.selectbox("Target students",["11th/12th","CET/JEE","College Student","All"])
        college=st.text_input("Nearby college")
        area=st.text_input("Area / locality")
        room=st.selectbox("Room / plan",["Single","Double Sharing","Triple Sharing","Monthly"])
        rent=st.number_input("Rent per month (₹)",min_value=0,value=3000,step=500)
        food=st.number_input("Food / mess cost per month (₹)",min_value=0,value=0,step=100)
        distance=st.number_input("Distance from college (km)",min_value=0.0,value=1.0,step=0.1)
        gender=st.selectbox("Gender",["Any","Male","Female"])
        contact=st.text_input("Contact number")
        desc=st.text_area("Description")
        submit=st.form_submit_button("Publish listing", type="primary")
        if submit:
            if not title or not college or not area or not contact:
                st.error("Please fill listing name, college, area and contact.")
            else:
                query("""INSERT INTO listings(owner_email,title,kind,audience,college,area,room_type,rent,food,distance,gender,contact,description)
                         VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                      (st.session_state.user["email"],title,kind,audience,college,area,room,rent,food,distance,gender,contact,desc),False)
                st.success("Listing published.")
                st.rerun()

    st.subheader("Your listings")
    mine=query("SELECT title,kind,college,area,rent FROM listings WHERE owner_email=?",(st.session_state.user["email"],))
    if mine:
        st.dataframe(mine, use_container_width=True, hide_index=True)
    else:
        st.info("No listings yet.")

if st.session_state.user is None:
    login()
elif st.session_state.user["role"]=="student":
    student_dashboard()
else:
    owner_dashboard()
