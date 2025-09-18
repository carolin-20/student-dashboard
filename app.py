import pandas as pd
import streamlit as st
import plotly.express as px
import datetime

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Student Dashboard",
    page_icon="📊",
    layout="wide"
)

# ---------------- LOAD DATA ----------------
attendance_df = pd.read_csv("attendance_dataset.csv")  # Student, Subject, Date, Status
marks_df = pd.read_csv("marks_dataset.csv")            # Student, Subject, Marks
events_df = pd.read_csv("events.csv")                  # Event, Date, Subject

# Convert dates
attendance_df["Date"] = pd.to_datetime(attendance_df["Date"])
events_df["Date"] = pd.to_datetime(events_df["Date"])
today = datetime.date.today()

# ---------------- CONSTANTS ----------------
LOW_ATTENDANCE_THRESHOLD = 75
FAILING_MARK_THRESHOLD = 40

# ---------------- PAGE TITLE ----------------
st.title("📊 Student Dashboard")

# =====================================================
# SIDEBAR FILTERS
# =====================================================
st.sidebar.header("🔍 Filters")

# Attendance filters
students = attendance_df["Student"].unique()
subjects = attendance_df["Subject"].unique()

selected_students_attendance = st.sidebar.multiselect(
    "Select Students (Attendance)",
    ["All Students"] + list(students),
    default=["All Students"],
    key="attendance_students"
)
selected_subjects_attendance = st.sidebar.multiselect(
    "Select Subjects (Attendance)",
    ["All Subjects"] + list(subjects),
    default=["All Subjects"],
    key="attendance_subjects"
)

# Marks filters
students_marks = marks_df["Student"].unique()
subjects_marks = marks_df["Subject"].unique()

selected_students_marks = st.sidebar.multiselect(
    "Select Students (Marks)",
    ["All Students"] + list(students_marks),
    default=["All Students"],
    key="marks_students"
)
selected_subjects_marks = st.sidebar.multiselect(
    "Select Subjects (Marks)",
    ["All Subjects"] + list(subjects_marks),
    default=["All Subjects"],
    key="marks_subjects"
)

# =====================================================
# TABS
# =====================================================
tab1, tab2, tab3 = st.tabs(["📘 Attendance", "📝 Marks", "📅 Events & Reminders"])

# =====================================================
# TAB 1 - Attendance
# =====================================================
with tab1:
    st.header("📘 Attendance Overview")

    # Apply filters
    filtered_df = attendance_df.copy()
    if "All Students" not in selected_students_attendance:
        filtered_df = filtered_df[filtered_df["Student"].isin(selected_students_attendance)]
    if "All Subjects" not in selected_subjects_attendance:
        filtered_df = filtered_df[filtered_df["Subject"].isin(selected_subjects_attendance)]

    st.subheader("Filtered Attendance Data")
    st.dataframe(filtered_df, use_container_width=True)

    # Attendance summary
    attendance_summary = (
        filtered_df.groupby(["Student", "Subject"])["Status"]
        .apply(lambda x: (x == "Present").mean() * 100)
        .reset_index(name="Attendance %")
    )

    st.subheader("Attendance % by Student and Subject")
    fig_bar = px.bar(
        attendance_summary,
        x="Student",
        y="Attendance %",
        color="Subject",
        barmode="group",
        title="Attendance % Overview"
    )
    fig_bar.update_layout(plot_bgcolor="black", paper_bgcolor="black", font=dict(color="white"))
    st.plotly_chart(fig_bar, use_container_width=True)

    # Pie chart (Present vs Absent count)
    st.subheader("Overall Attendance Distribution")
    present_ratio = (filtered_df["Status"] == "Present").mean() * 100
    pie_data = pd.DataFrame({
        "Status": ["Present", "Absent"],
        "Count": [present_ratio, 100 - present_ratio]
    })
    fig_pie = px.pie(pie_data, values="Count", names="Status", title="Present vs Absent %")
    st.plotly_chart(fig_pie, use_container_width=True)

    # Low attendance alerts
    low_attendance = attendance_summary[attendance_summary["Attendance %"] < LOW_ATTENDANCE_THRESHOLD]
    if not low_attendance.empty:
        st.warning(f"⚠️ Students with attendance below {LOW_ATTENDANCE_THRESHOLD}%:")
        st.dataframe(low_attendance)

# =====================================================
# TAB 2 - Marks
# =====================================================
with tab2:
    st.header("📝 Marks Overview")

    # Apply filters
    filtered_marks_df = marks_df.copy()
    if "All Students" not in selected_students_marks:
        filtered_marks_df = filtered_marks_df[filtered_marks_df["Student"].isin(selected_students_marks)]
    if "All Subjects" not in selected_subjects_marks:
        filtered_marks_df = filtered_marks_df[filtered_marks_df["Subject"].isin(selected_subjects_marks)]

    st.subheader("Marks Data")
    st.dataframe(filtered_marks_df, use_container_width=True)

    # Alerts for failing marks
    failing_students = filtered_marks_df[filtered_marks_df["Marks"] < FAILING_MARK_THRESHOLD]
    if not failing_students.empty:
        st.warning(f"⚠️ Students scoring below {FAILING_MARK_THRESHOLD}:")
        st.dataframe(failing_students)

    # Average marks per student
    avg_marks = filtered_marks_df.groupby("Student")["Marks"].mean().reset_index()
    st.subheader("Average Marks per Student")
    fig_bar_marks = px.bar(
        avg_marks,
        x="Student",
        y="Marks",
        color="Marks",
        color_continuous_scale="plasma",
        title="Average Marks per Student"
    )
    st.plotly_chart(fig_bar_marks, use_container_width=True)

    # Subject-wise distribution
    st.subheader("Subject-wise Marks Distribution")
    fig_box = px.box(
        filtered_marks_df,
        x="Subject",
        y="Marks",
        color="Subject",
        title="Marks Distribution by Subject"
    )
    st.plotly_chart(fig_box, use_container_width=True)

    # =====================================================
    # Special Attention Section
    # =====================================================
    st.subheader("🚨 Students Needing Special Attention")

    # Recalculate attendance %
    attendance_summary = (
        attendance_df.groupby(["Student", "Subject"])["Status"]
        .apply(lambda x: (x == "Present").mean() * 100)
        .reset_index(name="Attendance %")
    )

    # Merge with marks
    merged_df = pd.merge(filtered_marks_df, attendance_summary,
                         on=["Student", "Subject"], how="left")

    special_attention = merged_df[
        (merged_df["Marks"] < FAILING_MARK_THRESHOLD) &
        (merged_df["Attendance %"] < LOW_ATTENDANCE_THRESHOLD)
    ]

    if not special_attention.empty:
        st.warning("⚠️ These students need special attention (low marks & low attendance):")
        st.dataframe(special_attention, use_container_width=True)

        # Scatter plot
        fig_scatter = px.scatter(
            merged_df,
            x="Attendance %",
            y="Marks",
            color="Student",
            hover_data=["Subject"],
            title="Marks vs Attendance %"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.success("✅ No students currently flagged for special attention.")

# =====================================================
# TAB 3 - Events & Reminders
# =====================================================
with tab3:
    st.header("📅 Upcoming Exams & Assignments")

    upcoming = events_df[events_df["Date"].dt.date >= today].sort_values("Date")
    st.dataframe(upcoming, use_container_width=True)

    # Highlight near deadlines
    near_deadline = upcoming[upcoming["Date"].dt.date <= today + datetime.timedelta(days=7)]
    if not near_deadline.empty:
        st.warning("⚠️ Deadlines within 7 days:")
        st.dataframe(near_deadline)
