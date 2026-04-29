import streamlit as st
import pandas as pd
import re
import io
import os

# ==============================
# APP DESIGN
# ==============================
st.set_page_config(
    page_title="BFT Customer Service Review Tool",
    page_icon="🚌",
    layout="wide"
)

# ==============================
# OPTIONAL LOGO
# ==============================
logo_path = "bft_logo.png"

with st.sidebar:
    if os.path.exists(logo_path):
        st.image(logo_path, width=180)

    st.title("🚌 BFT Review Tool")
    st.write("Designed for Ben Franklin Transit")
    st.write("Data source: Track-It customer service reports")
    st.info("Upload a CSV or Excel file to begin.")

st.title("🚌 Customer Service Review Tool")
st.write(
    "Upload a Customer Service report file to review complaint type matches, "
    "urgent priority cases, and possible Title VI-related comments."
)

# ==============================
# FILE UPLOAD
# ==============================
uploaded_file = st.file_uploader(
    "Upload your CS_Report file",
    type=["csv", "xlsx", "xls"]
)

# ==============================
# HELPER FUNCTIONS
# ==============================
def read_file(uploaded_file):
    file_name = uploaded_file.name.lower()
    file_bytes = uploaded_file.read()

    if file_name.endswith(".xlsx"):
        return pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
    elif file_name.endswith(".xls"):
        try:
            return pd.read_excel(io.BytesIO(file_bytes), engine="xlrd")
        except:
            return pd.read_html(io.BytesIO(file_bytes))[0]
    elif file_name.endswith(".csv"):
        return pd.read_csv(io.BytesIO(file_bytes), encoding="latin1")
    else:
        return pd.read_html(io.BytesIO(file_bytes))[0]


def normalize_text(text):
    text = str(text).lower()

    replacements = {
        "didn't": "did not",
        "doesn't": "does not",
        "can't": "cannot",
        "couldn't": "could not",
        "wouldn't": "would not",
        "rt": "route",
        "tc": "transit center",
        "p/u": "pick up"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


redundant_words = set("""
the a an and or to of in on at for with from by is are was were be been being
i me my mine you your yours he him his she her hers they them their theirs
we us our ours it its this that these those there here where when why how
just very really quite too also still even
customer rider passenger caller person someone
called said stated reported mentioned explained asked wanted wants
bus route driver transit service trip
regarding about issue concern complaint problem request question inquiry
today yesterday tomorrow morning afternoon evening night time date
please thank thanks appreciate hello hi
thing something anything everything nothing
regular
""".split())

important_words = set("""
passed waved refused denied rude late early lost found accident injury hurt fell
fare ticket pass payment charged app website shelter stop garbage trash
wheelchair securement ramp lift transfer connection no show
speeding brake distracted phone text
""".split())


def clean_keyword(kw):
    kw = normalize_text(kw)

    if not kw:
        return ""

    words = kw.split()

    if len(words) >= 2:
        meaningful = [
            w for w in words
            if (w not in redundant_words or w in important_words) and len(w) >= 3
        ]
        return kw if meaningful else ""

    if kw in redundant_words and kw not in important_words:
        return ""

    if len(kw) < 4 and kw not in important_words:
        return ""

    return kw


keyword_groups = {
    "passed up": [
        "passed up", "drove past", "drove by", "bus passed",
        "driver passed", "went by", "kept going", "did not stop",
        "failed to stop", "would not stop", "never stopped",
        "skipped stop", "missed stop", "not picked up",
        "left behind", "waved", "flagged", "waiting at stop"
    ],
    "refused service": [
        "refused service", "refused", "denied service", "denied boarding",
        "denied", "would not let", "not allowed", "would not take",
        "get off", "kicked off", "asked to leave", "made me leave"
    ],
    "rude not friendly": [
        "rude", "not friendly", "unfriendly", "attitude",
        "bad attitude", "mean", "disrespectful", "unprofessional",
        "impolite", "yelled", "shouted", "argued", "angry",
        "treated poorly"
    ],
    "poor service": [
        "poor service", "bad service", "terrible service",
        "awful service", "unacceptable", "not helpful",
        "bad experience", "upset", "frustrated", "unhappy"
    ],
    "late service": [
        "late", "running late", "behind schedule", "delayed",
        "delay", "long wait", "not on time", "arrived late",
        "bus late", "late pickup", "pickup late"
    ],
    "early service": [
        "early", "left early", "arrived early", "too early",
        "ahead of schedule", "before scheduled time"
    ],
    "no show": [
        "no show", "never came", "did not come", "did not arrive",
        "never arrived", "not picked up", "missed pickup"
    ],
    "missed connection": [
        "missed connection", "missed transfer", "connection",
        "transfer", "bus left", "missed my bus", "could not connect"
    ],
    "lost found": [
        "lost", "found", "left on bus", "left my", "forgot",
        "wallet", "phone", "cell phone", "keys", "bag",
        "backpack", "purse", "item", "belongings"
    ],
    "accident": [
        "accident", "crash", "collision", "hit", "struck",
        "bumped", "damage", "damaged"
    ],
    "injury": [
        "injury", "injured", "hurt", "fell", "fall", "pain",
        "medical", "hospital", "ambulance"
    ],
    "speeding": [
        "speeding", "too fast", "driving fast", "unsafe speed",
        "reckless driving"
    ],
    "hard brake": [
        "hard brake", "braked hard", "sudden stop",
        "stopped suddenly", "jerked", "slammed brakes"
    ],
    "distracted": [
        "distracted", "on phone", "cell phone", "texting",
        "not paying attention", "using phone"
    ],
    "securement": [
        "securement", "wheelchair", "mobility device", "strap",
        "not secured", "tie down", "ramp", "lift", "walker", "scooter"
    ],
    "bike rack": ["bike rack", "bike", "bicycle", "rack"],
    "bus stop": [
        "bus stop", "stop sign", "stop location",
        "stop moved", "stop removed", "new stop"
    ],
    "shelter": [
        "shelter", "bench", "cover", "rain", "wind",
        "glass", "broken shelter", "waiting area"
    ],
    "garbage": ["garbage", "trash", "trash can", "garbage can", "litter"],
    "fare": [
        "fare", "payment", "pay", "paid", "price", "cost",
        "charge", "charged", "fare card", "reduced fare", "overcharged"
    ],
    "pass ticket": [
        "pass", "ticket", "fare card", "monthly pass",
        "day pass", "passes", "purchase", "buy", "card"
    ],
    "route information": [
        "route information", "schedule", "bus time",
        "what route", "map", "timetable"
    ],
    "trip plans": [
        "trip plan", "trip planning", "how to get",
        "which route", "directions", "travel", "planning trip"
    ],
    "app website": [
        "app", "mobile app", "application", "login", "website",
        "online", "tracker", "real time", "app not working"
    ],
    "social media": ["facebook", "instagram", "social media", "online post"],
    "commendation": [
        "thank you", "helpful", "great driver", "excellent",
        "kind", "nice", "appreciate", "good driver", "great service"
    ],
    "parking blocking": ["parking", "blocking", "blocked", "parked", "blocking stop"],
    "wrong information": [
        "wrong information", "incorrect information", "bad information",
        "misinformed", "wrong schedule", "wrong route"
    ],
    "reservation booking": [
        "reservation", "booking", "booked", "misbooked",
        "wrong booking", "scheduled ride", "cancelled ride"
    ]
}


def keywords_for_type(type_name):
    t = normalize_text(type_name)
    keywords = set()

    for group_name, group_keywords in keyword_groups.items():
        if group_name in t:
            keywords.update(group_keywords)

    if "rude" in t or "not friendly" in t:
        keywords.update(keyword_groups["rude not friendly"])

    if "lost" in t or "found" in t:
        keywords.update(keyword_groups["lost found"])

    if "securement" in t or "wheelchair" in t:
        keywords.update(keyword_groups["securement"])

    if "ticket" in t or "pass" in t:
        keywords.update(keyword_groups["pass ticket"])

    if "app" in t or "website" in t:
        keywords.update(keyword_groups["app website"])

    if "reservation" in t or "booking" in t:
        keywords.update(keyword_groups["reservation booking"])

    for word in t.split():
        cleaned = clean_keyword(word)
        if cleaned:
            keywords.add(cleaned)

    return sorted(set(clean_keyword(kw) for kw in keywords if clean_keyword(kw)))


def match_keywords(text, keywords):
    hits = []
    text_words = set(text.split())

    for kw in keywords:
        kw_clean = clean_keyword(kw)

        if not kw_clean:
            continue

        if kw_clean in text:
            hits.append(kw_clean)
            continue

        meaningful_words = [
            w for w in kw_clean.split()
            if clean_keyword(w) and (w not in redundant_words or w in important_words)
        ]

        if any(w in text_words for w in meaningful_words):
            hits.append(kw_clean)

    return sorted(set(hits))


def make_excel_download(dataframe, sheet_name):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        dataframe.to_excel(writer, index=False, sheet_name=sheet_name)
    return buffer.getvalue()


# ==============================
# MAIN APP
# ==============================
if uploaded_file is not None:

    try:
        df = read_file(uploaded_file)
        df.columns = [str(c).strip() for c in df.columns]

        required_columns = ["Description", "Customer Comments", "Type"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            st.error(f"Missing required columns: {missing_columns}")

        else:
            st.success("File uploaded successfully.")

            df["full_text"] = (
                df["Description"].fillna("").astype(str) + " " +
                df["Customer Comments"].fillna("").astype(str)
            )

            df["clean_text"] = df["full_text"].apply(normalize_text)
            df["comments_lower"] = df["full_text"].str.lower()
            df["Type"] = df["Type"].fillna("").astype(str).str.strip()

            tab1, tab2, tab3 = st.tabs([
                "Type Match Review",
                "Urgent Priority Review",
                "Title VI Review"
            ])

            # ==============================
            # TAB 1: TYPE MATCH REVIEW
            # ==============================
            with tab1:
                st.header("1. Type Match Review")

                all_types = sorted(df["Type"].unique())
                type_keywords = {t: keywords_for_type(t) for t in all_types}

                results = []

                for row_number, row in df.iterrows():
                    assigned_type = row["Type"]
                    text = row["clean_text"]

                    assigned_keywords = type_keywords.get(assigned_type, [])
                    assigned_hits = match_keywords(text, assigned_keywords)

                    all_scores = []

                    for t, kws in type_keywords.items():
                        hits = match_keywords(text, kws)
                        all_scores.append((t, len(hits), hits))

                    all_scores = sorted(all_scores, key=lambda x: x[1], reverse=True)
                    suggested_type, suggested_score, suggested_hits = all_scores[0]

                    if len(assigned_hits) >= 1:
                        match_status = "Match"
                        found_keywords = assigned_hits
                    else:
                        match_status = "Review suggested"
                        found_keywords = suggested_hits

                    results.append({
                        "Excel_Row_Number": row_number + 2,
                        "Assigned_Type": assigned_type,
                        "Suggested_Type": suggested_type,
                        "Found_Keywords": " | ".join(found_keywords[:30]),
                        "Match_Status": match_status,
                        "Customer Comment": row.get("Customer Comments", ""),
                        "Customer Name": row.get("Customer Name", ""),
                        "Assign to": row.get("Assign to", ""),
                        "Date Time": row.get("Date Time", "")
                    })

                output_df = pd.DataFrame(results)

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Total Records", len(output_df))

                with col2:
                    st.metric(
                        "Matched Records",
                        len(output_df[output_df["Match_Status"] == "Match"])
                    )

                with col3:
                    st.metric(
                        "Needs Review",
                        len(output_df[output_df["Match_Status"] == "Review suggested"])
                    )

                selected_status = st.selectbox(
                    "Filter by match status",
                    ["All", "Match", "Review suggested"]
                )

                if selected_status != "All":
                    filtered_df = output_df[output_df["Match_Status"] == selected_status]
                else:
                    filtered_df = output_df

                st.dataframe(filtered_df, use_container_width=True)

                st.download_button(
                    label="Download Type Match Result",
                    data=make_excel_download(output_df, "Type Match Result"),
                    file_name="CS_Type_Match_Result.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            # ==============================
            # TAB 2: URGENT PRIORITY REVIEW
            # ==============================
            with tab2:
                st.header("2. Urgent Priority Review")

                high_priority_keywords = [
                    "accident", "crash", "collision", "hit",
                    "injury", "injured", "hurt", "fell",
                    "ambulance", "hospital", "emergency",
                    "assault", "threat", "threatened", "police",
                    "unsafe", "dangerous", "reckless"
                ]

                medium_priority_keywords = [
                    "left behind", "stranded",
                    "refused service", "denied boarding",
                    "kicked off", "get off the bus",
                    "no show", "missed pickup",
                    "very upset", "supervisor"
                ]

                review_keywords = [
                    "discrimination", "racist", "bias", "unfair",
                    "treated differently",
                    "language", "spanish", "english",
                    "wheelchair", "disability", "ada"
                ]

                def classify_priority(text):
                    text = str(text).lower()

                    high_hits = [kw for kw in high_priority_keywords if kw in text]
                    medium_hits = [kw for kw in medium_priority_keywords if kw in text]
                    review_hits = [kw for kw in review_keywords if kw in text]

                    if high_hits:
                        return "High", high_hits
                    elif medium_hits:
                        return "Medium", medium_hits
                    elif review_hits:
                        return "Review", review_hits
                    else:
                        return None, []

                df["Priority"], df["Matched_Keywords"] = zip(
                    *df["comments_lower"].apply(classify_priority)
                )

                urgent_output = df[df["Priority"].notnull()].copy()
                urgent_output["Excel_Row_Number"] = urgent_output.index + 2

                urgent_output["Matched_Keywords"] = urgent_output["Matched_Keywords"].apply(
                    lambda x: " | ".join(x)
                )

                priority_order = {
                    "High": 1,
                    "Medium": 2,
                    "Review": 3
                }

                urgent_output["Priority_Order"] = urgent_output["Priority"].map(priority_order)
                urgent_output = urgent_output.sort_values(by="Priority_Order")

                urgent_output = urgent_output[[
                    "Excel_Row_Number",
                    "Priority",
                    "Matched_Keywords",
                    "Type",
                    "Customer Comments",
                    "Customer Name",
                    "Assign to",
                    "Date Time"
                ]]

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Total Priority Cases", len(urgent_output))

                with col2:
                    st.metric(
                        "High Priority",
                        len(urgent_output[urgent_output["Priority"] == "High"])
                    )

                with col3:
                    st.metric(
                        "Medium Priority",
                        len(urgent_output[urgent_output["Priority"] == "Medium"])
                    )

                with col4:
                    st.metric(
                        "Review Cases",
                        len(urgent_output[urgent_output["Priority"] == "Review"])
                    )

                selected_priority = st.selectbox(
                    "Filter by priority level",
                    ["All", "High", "Medium", "Review"]
                )

                if selected_priority != "All":
                    filtered_priority_df = urgent_output[
                        urgent_output["Priority"] == selected_priority
                    ]
                else:
                    filtered_priority_df = urgent_output

                st.dataframe(filtered_priority_df, use_container_width=True)

                st.download_button(
                    label="Download Urgent Priority Review",
                    data=make_excel_download(urgent_output, "Urgent Priority Review"),
                    file_name="Urgent_priority_review.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            # ==============================
            # TAB 3: TITLE VI REVIEW
            # ==============================
            with tab3:
                st.header("3. Title VI Review")

                st.write(
                    "This section flags comments that may relate to discrimination, "
                    "language access, or fairness concerns."
                )

                title_vi_keywords = [
                    "discrimination", "discriminated", "racist", "race", "color",
                    "national origin", "language", "english", "spanish",
                    "immigrant", "accent", "harassment", "bias",
                    "unfair", "treated differently"
                ]

                def find_title_vi_keywords(text):
                    text = str(text).lower()
                    return [kw for kw in title_vi_keywords if kw in text]

                df["Matched_Title_VI_Keywords"] = df["comments_lower"].apply(find_title_vi_keywords)
                df["Title_VI_Flag"] = df["Matched_Title_VI_Keywords"].apply(lambda x: len(x) > 0)

                title_vi_output = df[df["Title_VI_Flag"] == True].copy()
                title_vi_output["Excel_Row_Number"] = title_vi_output.index + 2

                title_vi_output["Matched_Keywords"] = title_vi_output[
                    "Matched_Title_VI_Keywords"
                ].apply(lambda x: " | ".join(x))

                title_vi_output = title_vi_output[[
                    "Excel_Row_Number",
                    "Type",
                    "Matched_Keywords",
                    "Customer Comments",
                    "Customer Name",
                    "Assign to",
                    "Date Time"
                ]]

                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Flagged Title VI Cases", len(title_vi_output))

                with col2:
                    st.metric("Total Records", len(df))

                show_only = st.checkbox("Show only flagged Title VI cases", value=True)

                if show_only:
                    display_df = title_vi_output
                else:
                    display_df = df

                st.dataframe(display_df, use_container_width=True)

                st.download_button(
                    label="Download Title VI Review",
                    data=make_excel_download(title_vi_output, "Title VI Review"),
                    file_name="Title_VI_review_comments.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    except Exception as e:
        st.error(f"Could not process the file: {e}")

else:
    st.info("Please upload a CSV or Excel file to begin.")
