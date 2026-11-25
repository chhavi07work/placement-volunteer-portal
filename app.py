
import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date
from io import BytesIO
from streamlit_autorefresh import st_autorefresh

# PAGE SETTINGS
st.set_page_config(
    page_title="Placement Volunteer Portal",
    page_icon="🎓",
    layout="centered"
)

st.title("🎓 Placement Volunteer Portal")
st.write("Manage Placement Drives and Student Volunteers.")

# DATABASE CONNECTION
@st.cache_resource
def connect_supabase():
    return create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"]
    )

try:
    db = connect_supabase()
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.stop()


def get_drives():
    return (
        db.table("placement_drives")
        .select("*")
        .order("drive_date")
        .execute()
    ).data or []


def get_registrations():
    return (
        db.table("student_registrations")
        .select("*")
        .order("registered_at", desc=True)
        .execute()
    ).data or []


# TABS
admin_tab, student_tab = st.tabs(
    ["Admin Panel", "Student Registration"]
)

# ==================================================
# ADMIN PANEL
# ==================================================

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

            try:
                correct_password = st.secrets["auth"]["admin_password"]

                if password == correct_password:
                    st.session_state.admin_logged_in = True
                    st.success("Login Successful!")
                    st.rerun()
                else:
                    st.error("Incorrect Password!")

            except Exception:
                st.error("Admin password missing in Streamlit Secrets.")

    else:

        st.header("Admin Dashboard")

        if st.button("Logout"):
            st.session_state.admin_logged_in = False
            st.rerun()

        # CREATE DRIVE
        st.subheader("Create Placement Drive")

        with st.form("drive_form"):

            drive_date = st.date_input(
                "Select Drive Date",
                min_value=date.today()
            )

            st.divider()
            st.subheader("Morning Slot")

            morning_enabled = st.checkbox(
                "Enable Morning Slot",
                value=True
            )

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

            publish = st.form_submit_button("Publish Drive")

        if publish:

            errors = []

            if not morning_enabled and not evening_enabled:
                errors.append("Enable at least one slot.")

            if morning_enabled and not morning_company.strip():
                errors.append("Enter Morning Company Name.")

            if evening_enabled and not evening_company.strip():
                errors.append("Enter Evening Company Name.")

            if (
                morning_enabled
                and evening_enabled
                and morning_company.strip().lower()
                == evening_company.strip().lower()
            ):
                errors.append("Enter different companies for both slots.")

            if errors:
                for error in errors:
                    st.error(error)

            else:

                drive_data = {
                    "drive_date": drive_date.isoformat(),

                    "morning_company": (
                        morning_company.strip()
                        if morning_enabled else None
                    ),

                    "morning_opening_time": (
                        morning_time.strftime("%H:%M:%S")
                        if morning_enabled else None
                    ),

                    "morning_capacity": (
                        int(morning_capacity)
                        if morning_enabled else 0
                    ),

                    "evening_company": (
                        evening_company.strip()
                        if evening_enabled else None
                    ),

                    "evening_opening_time": (
                        evening_time.strftime("%H:%M:%S")
                        if evening_enabled else None
                    ),

                    "evening_capacity": (
                        int(evening_capacity)
                        if evening_enabled else 0
                    )
                }

                try:
                    db.table("placement_drives").upsert(
                        drive_data,
                        on_conflict="drive_date"
                    ).execute()

                    st.success("Placement Drive Published Successfully!")

                except Exception as e:
                    st.error(f"Could not publish drive: {e}")

        # PUBLISHED DRIVES
        st.divider()
        st.subheader("Published Placement Drives")

        if st.button("Refresh Published Drives"):
            st.rerun()

        try:
            drives = get_drives()

            if drives:

                for drive in drives:

                    with st.expander(
                        f"Drive Date: {str(drive['drive_date'])[:10]}"
                    ):

                        st.write(
                            "Morning Company:",
                            drive.get("morning_company") or "Not available"
                        )

                        st.write(
                            "Morning Opening Time:",
                            drive.get("morning_opening_time") or "-"
                        )

                        st.write(
                            "Morning Capacity:",
                            drive.get("morning_capacity", 0)
                        )

                        st.divider()

                        st.write(
                            "Evening Company:",
                            drive.get("evening_company") or "Not available"
                        )

                        st.write(
                            "Evening Opening Time:",
                            drive.get("evening_opening_time") or "-"
                        )

                        st.write(
                            "Evening Capacity:",
                            drive.get("evening_capacity", 0)
                        )

            else:
                st.info("No placement drives published yet.")

        except Exception as e:
            st.error(f"Could not load drives: {e}")

        # STUDENT REGISTRATIONS
        st.divider()
        st.subheader("Student Registrations")

        st_autorefresh(
            interval=15000,
            key="registration_refresh"
        )

        if st.button("Refresh Registrations"):
            st.rerun()

        try:

            registrations = get_registrations()
            drives = get_drives()

            drive_map = {
                drive["id"]: drive for drive in drives
            }

            if registrations:

                rows = []

                for registration in registrations:

                    drive = drive_map.get(
                        registration["drive_id"], {}
                    )

                    slot = registration["slot"]

                    rows.append({
                        "Student Name": registration["student_name"],
                        "Drive Date": drive.get("drive_date"),
                        "Company": drive.get(
                            f"{slot.lower()}_company"
                        ),
                        "Selected Slot": slot,
                        "Registered At": registration["registered_at"]
                    })

                df = pd.DataFrame(rows)

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )

                excel_file = BytesIO()

                with pd.ExcelWriter(
                    excel_file,
                    engine="openpyxl"
                ) as writer:

                    df.to_excel(
                        writer,
                        index=False,
                        sheet_name="Registrations"
                    )

                st.download_button(
                    "Download Excel Report",
                    data=excel_file.getvalue(),
                    file_name="placement_registrations.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            else:
                st.info("No student registrations yet.")

        except Exception as e:
            st.error(f"Could not load registrations: {e}")


# ==================================================
# STUDENT REGISTRATION
# ==================================================

with student_tab:

    st.header("Student Registration")

    try:

        drives = get_drives()

        if not drives:

            st.info("No placement drive has been published yet.")

        else:

            # NORMALIZE DRIVE DATES
            drive_options = {}

            for drive_item in drives:

                date_value = str(
                    drive_item["drive_date"]
                )[:10]

                drive_options[date_value] = drive_item

            if not drive_options:

                st.warning("No valid published drive dates found.")

            else:

                selected_date = st.selectbox(
                    "Select Placement Drive Date",
                    options=list(drive_options.keys()),
                    format_func=lambda x: date.fromisoformat(
                        x
                    ).strftime("%d %B %Y")
                )

                drive = drive_options[selected_date]

                st.write(
                    "Drive Date:",
                    date.fromisoformat(selected_date).strftime(
                        "%d %B %Y"
                    )
                )

                available_slots = []

                if (
                    drive.get("morning_company")
                    and int(drive.get("morning_capacity") or 0) > 0
                ):
                    available_slots.append("Morning")

                if (
                    drive.get("evening_company")
                    and int(drive.get("evening_capacity") or 0) > 0
                ):
                    available_slots.append("Evening")

                if not available_slots:

                    st.info("No slots are currently available.")

                else:

                    st.divider()

                    name = st.text_input("Enter Your Full Name")

                    slot = st.selectbox(
                        "Select Your Available Slot",
                        available_slots
                    )

                    if slot == "Morning":

                        st.write("Company:", drive["morning_company"])

                        st.write(
                            "Opening Time:",
                            drive["morning_opening_time"]
                        )

                        capacity = drive["morning_capacity"]

                    else:

                        st.write("Company:", drive["evening_company"])

                        st.write(
                            "Opening Time:",
                            drive["evening_opening_time"]
                        )

                        capacity = drive["evening_capacity"]

                    st.write("Volunteer Capacity:", capacity)

                    if st.button("Confirm Availability"):

                        if not name.strip():

                            st.error("Please enter your full name.")

                        else:

                            registration_data = {
                                "drive_id": drive["id"],
                                "student_name": name.strip(),
                                "slot": slot
                            }

                            try:

                                db.table(
                                    "student_registrations"
                                ).insert(
                                    registration_data
                                ).execute()

                                st.success(
                                    f"Thank you {name}! "
                                    f"Your {slot} slot registration is confirmed."
                                )

                            except Exception as e:

                                error_message = str(e).lower()

                                if "unique_student_per_drive" in error_message:
                                    st.error(
                                        "You have already registered for this drive."
                                    )

                                elif "slot is full" in error_message:
                                    st.error("Sorry, this slot is full.")

                                elif "not available" in error_message:
                                    st.error("This slot is not available.")

                                else:
                                    st.error(f"Registration failed: {e}")

    except Exception as e:

        st.error(f"Could not load student registration: {e}")
