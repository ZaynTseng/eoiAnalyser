import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from dateutil.relativedelta import relativedelta
import time


def show_temporary_message(container, message, type="success", duration=0.5):
    """Show a temporary message that disappears after specified duration."""
    if type == "success":
        container.success(message)
    elif type == "warning":
        container.warning(message)
    elif type == "error":
        container.error(message)

    # Clear the message after duration
    time.sleep(duration)
    container.empty()


def get_state_folders(visa_type):
    """Get available state folders for 190 visa type."""
    if visa_type != "190":
        return []

    visa_dir = os.path.join(os.getcwd(), "data", "190")
    if not os.path.exists(visa_dir):
        return []

    return [d for d in os.listdir(visa_dir) if os.path.isdir(os.path.join(visa_dir, d))]


def load_data(visa_type, state=None):
    """
    Load data based on visa type and state (for 190 visa).
    """
    dfs = []
    base_dir = os.path.join(os.getcwd(), "data")

    if visa_type == "189":
        data_dir = os.path.join(base_dir, "189")
    else:
        if not state:
            return pd.DataFrame()
        data_dir = os.path.join(base_dir, "190", state)

    if not os.path.exists(data_dir):
        return pd.DataFrame()

    for filename in os.listdir(data_dir):
        if filename.endswith(".csv"):
            file_path = os.path.join(data_dir, filename)
            df = pd.read_csv(file_path)
            df["As At Month"] = pd.to_datetime(df["As At Month"], format="%m/%Y")
            dfs.append(df)

    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def format_date(date):
    """Format datetime to YYYY-MM string."""
    return date.strftime("%Y-%m")


def get_date_range_options():
    """Get predefined date range options."""
    return {
        "Last 3 months": 3,
        "Last 6 months": 6,
        "Last 12 months": 12,
        "All time": None,
        "Custom": "custom",
    }


def month_selector(data):
    # Get all available months and sort them
    all_months = sorted(data["As At Month"].unique())

    if not all_months:
        return []

    # Calculate data points for each month
    monthly_counts = data.groupby("As At Month").size()

    # Get date range options
    date_ranges = get_date_range_options()
    selected_range = st.sidebar.selectbox(
        "Select Time Period",
        options=list(date_ranges.keys()),
        index=1,  # Default to "Last 6 months"
    )

    if selected_range == "Custom":
        # Custom date range selector
        col1, col2 = st.sidebar.columns(2)

        # Calculate min and max dates
        min_date = min(all_months)
        max_date = max(all_months)

        # Date inputs for custom range
        with col1:
            start_date = st.date_input(
                "Start Date", value=min_date, min_value=min_date, max_value=max_date
            )
        with col2:
            end_date = st.date_input(
                "End Date", value=max_date, min_value=min_date, max_value=max_date
            )

        # Convert to datetime for comparison
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        selected_months = [d for d in all_months if start_date <= d <= end_date]

    else:
        # Predefined range
        months_back = date_ranges[selected_range]
        if months_back is None:  # All time
            selected_months = all_months
        else:
            latest_month = max(all_months)
            cutoff_date = latest_month - relativedelta(months=months_back - 1)
            selected_months = [d for d in all_months if d >= cutoff_date]

    return [format_date(m) for m in selected_months]


def main():
    st.set_page_config(layout="wide")
    st.sidebar.title("EOI Analysis App")

    # 创建一个空容器用于显示临时消息
    message_container = st.sidebar.empty()

    # Add visa type selection
    visa_type = st.sidebar.radio(
        "Select Visa Type", ["189 Visa", "190 Visa"], horizontal=True
    )
    visa_type = visa_type.split()[0]

    # Add state selection for 190 visa
    selected_state = None
    if visa_type == "190":
        states = get_state_folders(visa_type)
        if not states:
            show_temporary_message(
                message_container, "No state data found for 190 visa.", "warning"
            )
            return
        selected_state = st.sidebar.radio("Select State", states, horizontal=True)

    # Initialize session state
    if "data" not in st.session_state:
        st.session_state["data"] = None
    if "selected_points" not in st.session_state:
        st.session_state["selected_points"] = []
    if "current_visa_type" not in st.session_state:
        st.session_state["current_visa_type"] = None
    if "current_state" not in st.session_state:
        st.session_state["current_state"] = None

    # Reload data if visa type or state changes
    if (
        st.session_state["current_visa_type"] != visa_type
        or st.session_state["current_state"] != selected_state
    ):
        st.session_state["data"] = None
        st.session_state["current_visa_type"] = visa_type
        st.session_state["current_state"] = selected_state
        st.session_state["selected_points"] = []

    # Load data
    if st.session_state["data"] is None:
        st.session_state["data"] = load_data(visa_type, selected_state)
        if st.session_state["data"].empty:
            show_temporary_message(
                message_container,
                f"No CSV files found for the selected {'state' if visa_type == '190' else 'visa type'}.",
                "warning",
            )
            return
        show_temporary_message(message_container, "Data loaded successfully!")

    data = st.session_state["data"]

    occupations = data["Occupation"].unique()
    selected_occupation = st.sidebar.selectbox("Select Occupation", occupations)

    eoi_statuses = data["EOI Status"].unique()
    selected_eoi_status = st.sidebar.selectbox("Select EOI Status", eoi_statuses)

    # Points filter
    all_points = sorted(data["Points"].unique(), reverse=True)
    selected_points = st.sidebar.multiselect(
        "Select Points (Optional)",
        all_points,
        default=st.session_state["selected_points"],
    )

    # Reset points button
    if st.sidebar.button("Reset Points"):
        st.session_state["selected_points"] = []
        st.rerun()

    # Enhanced month selection
    selected_months = month_selector(data)

    # Update session state for points
    if selected_points != st.session_state["selected_points"]:
        st.session_state["selected_points"] = selected_points
        st.rerun()

    # Ensure at least one month is selected
    if not selected_months:
        show_temporary_message(
            message_container, "Please select at least one month.", "warning"
        )
        return

    filtered_data = data[
        (data["Occupation"] == selected_occupation)
        & (data["EOI Status"] == selected_eoi_status)
    ]

    if selected_points:
        filtered_data = filtered_data[filtered_data["Points"].isin(selected_points)]

    if selected_months:
        filtered_data = filtered_data[
            filtered_data["As At Month"].dt.strftime("%Y-%m").isin(selected_months)
        ]

    filtered_data["Count EOIs"] = filtered_data["Count EOIs"].replace("<20", "5")
    filtered_data["Count EOIs"] = pd.to_numeric(filtered_data["Count EOIs"])

    # Get unique points that actually have data
    points_with_data = sorted(filtered_data["Points"].unique(), reverse=True)

    # Create traces for each month
    traces = []
    for month in selected_months:
        month_data = filtered_data[
            filtered_data["As At Month"].dt.strftime("%Y-%m") == month
        ]
        # Only include points that have data for this month
        month_data = month_data[month_data["Count EOIs"] > 0]
        trace = go.Bar(
            y=month_data["Points"],
            x=month_data["Count EOIs"],
            name=month,
            orientation="h",
            text=month_data["Count EOIs"],
            textposition="outside",
            textfont=dict(size=10),
        )
        traces.append(trace)

    # Calculate dynamic height based on number of points with data and months
    height = max(600, len(points_with_data) * len(selected_months) * 30)

    # Create the layout
    title_suffix = f" - {selected_state}" if visa_type == "190" else ""
    layout = go.Layout(
        barmode="group",
        title=f"{visa_type} Visa EOI Analysis for {selected_occupation} - {selected_eoi_status}{title_suffix}",
        xaxis_title=dict(text="Count of EOIs"),
        yaxis_title=dict(text="Points"),
        yaxis={
            "categoryorder": "array",
            "categoryarray": points_with_data[::-1],
            "tickmode": "array",
            "tickvals": points_with_data,
            "ticktext": [str(int(p)) for p in points_with_data],
        },
        height=height,
        legend=dict(
            yanchor="top", y=0.99, xanchor="left", x=0.99, traceorder="reversed"
        ),
    )

    # Create the figure and plot
    fig = go.Figure(data=traces, layout=layout)
    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
