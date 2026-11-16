import sqlite3
from datetime import date, datetime
import streamlit as st
import pandas as pd

DB_PATH = "planner.db"

st.set_page_config(
    page_title="Planer Instagram",
    page_icon="📅",
    layout="centered",
    initial_sidebar_state="collapsed",
)

def connect():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                publish_date TEXT NOT NULL,
                publish_time TEXT DEFAULT '',
                title TEXT NOT NULL,
                format TEXT DEFAULT 'Post',
                caption TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                done INTEGER DEFAULT 0
            )
        """)
        conn.commit()

def get_posts():
    with connect() as conn:
        return pd.read_sql_query(
            "SELECT * FROM posts ORDER BY publish_date, publish_time, id", conn
        )

def add_post(publish_date, publish_time, title, fmt, caption, notes):
    with connect() as conn:
        conn.execute(
            """INSERT INTO posts
               (publish_date, publish_time, title, format, caption, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (str(publish_date), publish_time, title, fmt, caption, notes),
        )
        conn.commit()

def set_done(post_id, done):
    with connect() as conn:
        conn.execute("UPDATE posts SET done = ? WHERE id = ?", (int(done), int(post_id)))
        conn.commit()

def delete_post(post_id):
    with connect() as conn:
        conn.execute("DELETE FROM posts WHERE id = ?", (int(post_id),))
        conn.commit()

init_db()
st.title("📅 Mój planer Instagram")
st.caption("Zaplanuj publikacje, śledź postępy i odhaczaj gotowe materiały.")

df = get_posts()
total = len(df)
completed = int(df["done"].sum()) if total else 0
planned = total - completed

m1, m2, m3 = st.columns(3)
m1.metric("Wszystkie", total)
m2.metric("Do zrobienia", planned)
m3.metric("Gotowe", completed)
if total:
    st.progress(completed / total, text=f"Postęp: {completed} z {total} materiałów")

st.divider()
st.subheader("➕ Dodaj nową publikację")
with st.form("add_post_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        publish_date = st.date_input("Data publikacji", value=date.today())
    with col2:
        publish_time = st.text_input("Godzina (opcjonalnie)", placeholder="np. 18:30")
    title = st.text_input("Nazwa / temat posta", placeholder="np. 3 pomysły na stylizację")
    fmt = st.selectbox("Format", ["Post", "Karuzela", "Reels", "Stories", "Live"])
    caption = st.text_area("Opis / podpis (opcjonalnie)", height=90)
    notes = st.text_area("Notatki (opcjonalnie)", placeholder="Pomysł na zdjęcie, hashtagi, materiały…", height=75)
    submitted = st.form_submit_button("Dodaj do harmonogramu", use_container_width=True)
    if submitted:
        if not title.strip():
            st.error("Wpisz temat publikacji.")
        else:
            add_post(publish_date, publish_time.strip(), title.strip(), fmt, caption.strip(), notes.strip())
            st.success("Dodano publikację!")
            st.rerun()

st.divider()
st.subheader("🗂️ Harmonogram")
df = get_posts()

if df.empty:
    st.info("Nie masz jeszcze zaplanowanych publikacji. Dodaj pierwszą powyżej.")
else:
    filter_choice = st.radio(
        "Pokaż", ["Wszystkie", "Do zrobienia", "Gotowe"],
        horizontal=True, label_visibility="collapsed"
    )
    if filter_choice == "Do zrobienia":
        shown = df[df["done"] == 0]
    elif filter_choice == "Gotowe":
        shown = df[df["done"] == 1]
    else:
        shown = df

    for _, post in shown.iterrows():
        is_done = bool(post["done"])
        heading = f"{'✅' if is_done else '⬜'} {post['publish_date']} · {post['title']}"
        with st.expander(heading, expanded=not is_done):
            st.write(f"**Format:** {post['format']}")
            if post["publish_time"]:
                st.write(f"**Godzina:** {post['publish_time']}")
            if post["caption"]:
                st.write("**Podpis:**")
                st.write(post["caption"])
            if post["notes"]:
                st.write("**Notatki:**")
                st.write(post["notes"])

            c1, c2 = st.columns(2)
            with c1:
                if st.button(
                    "Cofnij oznaczenie" if is_done else "Oznacz jako gotowe",
                    key=f"done_{post['id']}",
                    use_container_width=True,
                ):
                    set_done(post["id"], not is_done)
                    st.rerun()
            with c2:
                if st.button("Usuń", key=f"delete_{post['id']}", use_container_width=True):
                    delete_post(post["id"])
                    st.rerun()

st.divider()
st.caption("Wskazówka: dodaj tę stronę do ekranu głównego telefonu z menu przeglądarki.")
st.caption("Dane są zapisywane w pliku planner.db na serwerze, na którym działa aplikacja.")
