# app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from pathlib import Path

# -----------------------
# Helpers for flexible column mapping
# -----------------------
def find_first_col(df, candidates):
    """Return actual column name from df for first candidate present, or None."""
    cols_lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in cols_lower:
            return cols_lower[cand.lower()]
    return None

def ensure_data_folder():
    Path("data").mkdir(parents=True, exist_ok=True)

# -----------------------
# App config & CSS
# -----------------------
st.set_page_config(page_title="Tech Event Tracker", layout="wide")
st.markdown(
    """
    <style>
      /* Gradient dark shaded background */
      .stApp {
        background: linear-gradient(120deg, #0b1226 0%, #0f2a44 40%, #18304e 60%, #0d2636 100%);
        color: #E6EEF3;
      }
      .header-title { font-size: 32px; font-weight:700; color:#E7F6F8; text-align:center; padding-top:6px; }
      .header-sub { font-size:14px; color:#bfcfd6; text-align:center; margin-bottom:20px; }
      .card {
        background: rgba(255,255,255,0.03);
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 12px;
      }
      .small { color:#bfcfd6; font-size:13px; }
      /* style for small buttons */
      .stButton>button {
        border-radius:8px;
        padding:6px 10px;
        font-weight:600;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------
# Ensure data folder
# -----------------------
ensure_data_folder()
DATA_PATH = Path("events.csv")
BOOKMARK_PATH = Path("bookmarks.csv")

# -----------------------
# Load events or show sample creator
# -----------------------
if not DATA_PATH.exists():
    st.warning("No events.csv found. You can create a sample dataset now.")
    if st.button("Create sample events.csv"):
        sample = [
            {"event_name":"Google Cloud Summit","date":"2025-09-20","location":"Online","type":"Conference","category":"Cloud","price":"Free","link":"https://cloud.google.com"},
            {"event_name":"AI Hackathon","date":"2025-09-30","location":"Bangalore","type":"Hackathon","category":"AI","price":"Paid","link":"https://devpost.com"},
            {"event_name":"Web Dev Meetup","date":"2025-10-05","location":"Delhi","type":"Meetup","category":"Web","price":"Free","link":"https://meetup.com"},
            {"event_name":"Frontend Workshop","date":"2025-10-10","location":"Online","type":"Workshop","category":"Web","price":"Paid","link":"https://example.com"},
        ]
        pd.DataFrame(sample).to_csv(DATA_PATH, index=False)
        st.success("Sample events.csv created. Re-run the app.")
    st.stop()

try:
    df = pd.read_csv(DATA_PATH, dtype=str)
except Exception as e:
    st.error(f"Could not read {DATA_PATH}: {e}")
    st.stop()

# Normalize whitespace in column names
df.columns = [c.strip() for c in df.columns]

# Flexible mapping for common column names
col_map = {}
col_map['event_name'] = find_first_col(df, ["event_name", "title", "name"])
col_map['date']       = find_first_col(df, ["date", "event_date", "start_date"])
col_map['location']   = find_first_col(df, ["location", "city", "venue"])
col_map['type']       = find_first_col(df, ["type", "event_type", "mode"])
col_map['category']   = find_first_col(df, ["category", "tags", "topic"])
col_map['price']      = find_first_col(df, ["price", "cost", "fee"])
col_map['link']       = find_first_col(df, ["link", "url"])

required = ['event_name','date','location']
missing_required = [k for k in required if col_map.get(k) is None]

if missing_required:
    st.error("Your CSV is missing required columns: " + ", ".join(missing_required))
    st.info("Detected columns in CSV: " + ", ".join(df.columns))
    st.stop()

# Setup bookmarks (keep unique key column)
if BOOKMARK_PATH.exists():
    bookmarks = pd.read_csv(BOOKMARK_PATH, dtype=str)
else:
    bookmarks = pd.DataFrame(columns=df.columns.tolist() + ["__unique_key__"])

# Add header (logo optional)
logo_path = Path("assets/logo.png")
if logo_path.exists():
    cols = st.columns([1,8,1])
    with cols[1]:
        st.image(str(logo_path), width=110)
        st.markdown('<div class="header-title">Tech Event Tracker</div>', unsafe_allow_html=True)
        st.markdown('<div class="header-sub">Professional event discovery & bookmarking for developers</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="header-title">Tech Event Tracker</div>', unsafe_allow_html=True)
    st.markdown('<div class="header-sub">Professional event discovery & bookmarking for developers</div>', unsafe_allow_html=True)

# -----------------------
# Navigation + Search (top)
# -----------------------
nav = st.radio("", ["Home", "Analytics", "Bookmarks"], horizontal=True)
search = st.text_input("Search events (by name)", placeholder="Search e.g. 'cloud', 'hackathon'")

# Filters inline
fcol1, fcol2, fcol3, fcol4 = st.columns([3,3,2,1])
with fcol1:
    # category choices if available
    if col_map['category']:
        categories = sorted(df[col_map['category']].dropna().unique().tolist())
        sel_category = st.multiselect("Category", ["All"] + categories, default=["All"])
    else:
        sel_category = ["All"]
with fcol2:
    if col_map['type']:
        types = sorted(df[col_map['type']].dropna().unique().tolist())
        sel_type = st.multiselect("Type", ["All"] + types, default=["All"])
    else:
        sel_type = ["All"]
with fcol3:
    sel_price = st.selectbox("Price", ["All", "Free", "Paid"])
with fcol4:
    if st.button("Clear filters"):
        search = ""
        # To fully clear session inputs, just reload page
        st.experimental_rerun()

# -----------------------
# Filter logic
# -----------------------
filtered = df.copy()

# search
if search:
    filtered = filtered[filtered[col_map['event_name']].str.contains(search, case=False, na=False)]

# category
if col_map['category'] and sel_category and "All" not in sel_category:
    filtered = filtered[filtered[col_map['category']].isin(sel_category)]

# type
if col_map['type'] and sel_type and "All" not in sel_type:
    filtered = filtered[filtered[col_map['type']].isin(sel_type)]

# price filter
if col_map.get('price') and sel_price != "All":
    if sel_price == "Free":
        filtered = filtered[filtered[col_map['price']].str.lower() == "free"]
    else:
        filtered = filtered[filtered[col_map['price']].str.lower() != "free"]

# -----------------------
# HOME: show events in card-like layout
# -----------------------
if nav == "Home":
    st.markdown("### Browse events")
    if filtered.empty:
        st.info("No events match your filters/search.")
    else:
        for idx, row in filtered.reset_index(drop=True).iterrows():
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                c1, c2 = st.columns([5,1])
                with c1:
                    title = row[col_map['event_name']]
                    date = row[col_map['date']] if col_map['date'] else ""
                    loc  = row[col_map['location']] if col_map['location'] else ""
                    cat  = row[col_map['category']] if col_map['category'] else ""
                    typ  = row[col_map['type']] if col_map['type'] else ""
                    price_val = row[col_map['price']] if col_map['price'] else ""
                    link = row[col_map['link']] if col_map['link'] else ""
                    st.markdown(f"**{title}**  \n<small class='small'>{date}  •  {loc}  •  {typ}  •  {cat}</small>", unsafe_allow_html=True)
                    if link:
                        st.markdown(f"[Visit event]({link})")
                with c2:
                    unique_key = f"{title}__{date}"
                    # ensure bookmarks has __unique_key__ column
                    if "__unique_key__" not in bookmarks.columns:
                      bookmarks["__unique_key__"] = bookmarks.apply(
        lambda r: f"{r.get(col_map.get('event_name'), '')}__{r.get(col_map.get('date'), '')}",
        axis=1
    )

                    already = (bookmarks["__unique_key__"] == unique_key).any()
                    if already:
                        st.button("Bookmarked", disabled=True, key=f"bm_{idx}_done")
                    else:
                        if st.button("Bookmark", key=f"bm_{idx}"):
                            # append and save
                            new_row = row.to_dict()
                            new_row["__unique_key__"] = unique_key
                            bookmarks = pd.concat([bookmarks, pd.DataFrame([new_row])], ignore_index=True, sort=False)
                            bookmarks.to_csv(BOOKMARK_PATH, index=False)
                            st.success("Saved to bookmarks")
                            st.experimental_rerun()
                st.markdown('</div>', unsafe_allow_html=True)

# -----------------------
# ANALYTICS: Free vs Paid and top locations
# -----------------------
elif nav == "Analytics":
    st.markdown("### Analytics")
    # price analysis
    if col_map.get('price'):
        price_series = df[col_map['price']].fillna("Unknown").apply(lambda x: "Free" if str(x).strip().lower()=="free" else "Paid")
        price_counts = price_series.value_counts()
        fig, ax = plt.subplots(figsize=(4,3))
        ax.bar(price_counts.index, price_counts.values, color=["#2ecc71","#e74c3c"][:len(price_counts)])
        ax.set_title("Free vs Paid")
        ax.set_ylabel("Count")
        st.pyplot(fig)
    else:
        st.info("No price column found; skipping Free vs Paid chart.")

    # location distribution
    loc_col = col_map.get('location')
    if loc_col:
        loc_counts = df[loc_col].fillna("Unknown").value_counts().head(10)
        fig2, ax2 = plt.subplots(figsize=(7,3))
        ax2.barh(loc_counts.index[::-1], loc_counts.values[::-1], color="#3498db")
        ax2.set_title("Top locations (top 10)")
        ax2.set_xlabel("Number of events")
        st.pyplot(fig2)
    else:
        st.info("No location column found; skipping location chart.")

# -----------------------
# BOOKMARKS: view & delete
# -----------------------
elif nav == "Bookmarks":
    st.markdown("### Bookmarked events")
    if bookmarks.empty:
        st.info("No bookmarks yet.")
    else:
        # show limited columns for clarity
        display_cols = [c for c in [col_map.get('event_name'), col_map.get('date'), col_map.get('location'), col_map.get('price')] if c in bookmarks.columns]
        st.dataframe(bookmarks[display_cols].rename(columns={col_map.get('event_name'):'Event', col_map.get('date'):'Date', col_map.get('location'):'Location', col_map.get('price'):'Price'}))
        # delete option
        if "__unique_key__" in bookmarks.columns:
         options = bookmarks["__unique_key__"].tolist()
        else:
         options = []

        to_delete = st.multiselect("Select bookmarks to remove", options=options)

        if st.button("Delete selected"):
            if to_delete:
                bookmarks = bookmarks[~bookmarks["__unique_key__"].isin(to_delete)]
                bookmarks.to_csv(BOOKMARK_PATH, index=False)
                st.success("Deleted selected bookmarks")
                st.experimental_rerun()
            else:
                st.info("No bookmarks selected for deletion.")
