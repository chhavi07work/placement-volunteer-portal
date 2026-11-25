
import streamlit as st

st.set_page_config(
    page_title="Placement Volunteer Portal",
    page_icon="🎓",
    layout="centered"
)

st.title("🎓 Placement Volunteer Portal")
st.write("Manage Placement Drives and Student Volunteers.")

admin_tab, student_tab = st.tabs(
    ["Admin Panel", "Student Registration"]
)

# -------- ADMIN PANEL --------

with admin_tab:

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:

        st.header("Admin Login")

        password = st.text_input(
            "Enter Admin Password",
            type="password"
        )

        if st.button("Login"):

            correct_password = st.secrets["auth"]["admin_password"]

            if password == correct_password:
                st.session_state.admin_logged_in = True
                st.success("Login Successful!")
                st.rerun()

            else:
                st.error("Incorrect Password!")

    else:

        st.header("Admin Dashboard")

        if st.button("Logout"):
            st.session_state.admin_logged_in = False
            st.rerun()

        st.subheader("Create Placement Drive")

        drive_date = st.date_input("Select Drive Date")

        st.divider()

        st.subheader("Morning Slot")

        morning_enabled = st.checkbox(
            "Enable Morning Slot",
            value=True
        )

        if morning_enabled:

            morning_company = st.text_input(
                "Morning Company Name"
            )

            morning_time = st.time_input(
                "Morning Opening Time"
            )

            morning_capacity = st.number_input(
                "Morning Volunteer Capacity",
                min_value=1,
                value=50
            )

        st.divider()

        st.subheader("Evening Slot")

        evening_enabled = st.checkbox(
            "Enable Evening Slot"
        )

        if evening_enabled:

            evening_company = st.text_input(
                "Evening Company Name"
            )

            evening_time = st.time_input(
                "Evening Opening Time"
            )

            evening_capacity = st.number_input(
                "Evening Volunteer Capacity",
                min_value=1,
                value=50
            )

        if st.button("Publish Drive"):

            errors = []

            if not morning_enabled and not evening_enabled:
                errors.append("Enable at least one slot.")

            if morning_enabled and not morning_company.strip():
                errors.append("Enter Morning Company Name.")

            if evening_enabled and not evening_company.strip():
                errors.append("Enter Evening Company Name.")

            if (morning_enabled and evening_enabled
                    and morning_company.strip().lower()
                    == evening_company.strip().lower()):
                errors.append("Enter different companies for both slots.")

            if errors:
                for error in errors:
                    st.error(error)

            else:

                drive = {
                    "date": str(drive_date),
                    "morning": morning_enabled,
                    "evening": evening_enabled
                }

                if morning_enabled:
                    drive["morning_company"] = morning_company.strip()
                    drive["morning_time"] = morning_time.strftime("%I:%M %p")
                    drive["morning_capacity"] = morning_capacity

                if evening_enabled:
                    drive["evening_company"] = evening_company.strip()
                    drive["evening_time"] = evening_time.strftime("%I:%M %p")
                    drive["evening_capacity"] = evening_capacity

                st.session_state["published_drive"] = drive

                st.success("Placement Drive Published Successfully!")

        if "published_drive" in st.session_state:

            drive = st.session_state["published_drive"]

            st.divider()
            st.subheader("Published Drive Details")

            st.write("Date:", drive["date"])

            if drive["morning"]:
                st.write("Morning Company:", drive["morning_company"])
                st.write("Opening Time:", drive["morning_time"])
                st.write("Capacity:", drive["morning_capacity"])

            if drive["evening"]:
                st.write("Evening Company:", drive["evening_company"])
                st.write("Opening Time:", drive["evening_time"])
                st.write("Capacity:", drive["evening_capacity"])

# -------- STUDENT REGISTRATION --------

with student_tab:

    st.header("Student Registration")

    if "published_drive" not in st.session_state:
        st.info("No placement drive has been published yet.")

    else:

        drive = st.session_state["published_drive"]

        st.write("Drive Date:", drive["date"])

        name = st.text_input("Enter Your Name")

        student_date = st.date_input(
            "Select Drive Date",
            key="student_date"
        )

        available_slots = []

        if drive["morning"]:
            available_slots.append("Morning")

        if drive["evening"]:
            available_slots.append("Evening")

        slot = st.selectbox(
            "Select Your Available Slot",
            available_slots
        )

        if slot == "Morning":
            st.write("Company:", drive["morning_company"])
            st.write("Opening Time:", drive["morning_time"])

        elif slot == "Evening":
            st.write("Company:", drive["evening_company"])
            st.write("Opening Time:", drive["evening_time"])

        if st.button("Confirm Availability"):

            if not name.strip():
                st.error("Please enter your name.")

            elif student_date != drive["date"]:
                st.error("Please select the published drive date.")

            else:
                st.success(
                    f"Thank you {name}! "
                    f"You selected {slot} on {student_date}."
                )
