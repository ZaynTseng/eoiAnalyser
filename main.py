import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os


def get_state_folders(visa_type):
    """Get available state folders for 190 visa type."""
    if visa_type != "190":
        return []

    visa_dir = os.path.join(os.getcwd(), 'data', '190')
    if not os.path.exists(visa_dir):
        return []

    return [d for d in os.listdir(visa_dir) if os.path.isdir(os.path.join(visa_dir, d))]


def load_data(visa_type, state=None):
    """
    Load data based on visa type and state (for 190 visa).

    Args:
        visa_type: str, either "189" or "190"
        state: str, optional, required for 190 visa type
    """
    dfs = []
    base_dir = os.path.join(os.getcwd(), 'data')

    if visa_type == "189":
        data_dir = os.path.join(base_dir, '189')
    else:  # 190 visa
        if not state:
            return pd.DataFrame()  # Return empty DataFrame if no state selected
        data_dir = os.path.join(base_dir, '190', state)

    if not os.path.exists(data_dir):
        return pd.DataFrame()

    for filename in os.listdir(data_dir):
        if filename.endswith('.csv'):
            file_path = os.path.join(data_dir, filename)
            df = pd.read_csv(file_path)
            df["As At Month"] = pd.to_datetime(df["As At Month"], format="%m/%Y")
            dfs.append(df)

    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def main():
    st.set_page_config(layout="wide")
    st.sidebar.title("EOI Analysis App")

    # Add visa type selection
    visa_type = st.sidebar.radio("Select Visa Type", ["189 Visa", "190 Visa"])
    visa_type = visa_type.split()[0]  # Get just the number

    # Add state selection for 190 visa
    selected_state = None
    if visa_type == "190":
        states = get_state_folders(visa_type)
        if not states:
            st.warning("No state data found for 190 visa.")
            return
        selected_state = st.sidebar.radio("Select State", states)

    # Initialize session state
    if "data" not in st.session_state:
        st.session_state["data"] = None
    if "selected_points" not in st.session_state:
        st.session_state["selected_points"] = []
    if "selected_months" not in st.session_state:
        st.session_state["selected_months"] = []
    if "current_visa_type" not in st.session_state:
        st.session_state["current_visa_type"] = None
    if "current_state" not in st.session_state:
        st.session_state["current_state"] = None

    # Reload data if visa type or state changes
    if (st.session_state["current_visa_type"] != visa_type or
            st.session_state["current_state"] != selected_state):
        st.session_state["data"] = None
        st.session_state["current_visa_type"] = visa_type
        st.session_state["current_state"] = selected_state
        st.session_state["selected_points"] = []
        st.session_state["selected_months"] = []

    # Load data
    if st.session_state["data"] is None:
        st.session_state["data"] = load_data(visa_type, selected_state)
        if st.session_state["data"].empty:
            st.warning(f"No CSV files found for the selected {'state' if visa_type == '190' else 'visa type'}.")
            return
        st.sidebar.success("Data loaded successfully!")

    data = st.session_state["data"]

    occupations = data["Occupation"].unique()
    selected_occupation = st.sidebar.selectbox("Select Occupation", occupations)

    eoi_statuses = data["EOI Status"].unique()
    selected_eoi_status = st.sidebar.selectbox("Select EOI Status", eoi_statuses)

    # Points filter
    all_points = sorted(data["Points"].unique(), reverse=True)
    selected_points = st.sidebar.multiselect("Select Points (Optional)",
                                             all_points,
                                             default=st.session_state["selected_points"])

    # Reset points button
    if st.sidebar.button("Reset Points"):
        st.session_state["selected_points"] = []
        st.rerun()

    # Month filter
    all_months = sorted(data["As At Month"].dt.strftime("%Y-%m").unique(), reverse=True)
    selected_months = st.sidebar.multiselect("Select Months (Optional)",
                                             all_months,
                                             default=st.session_state["selected_months"] or all_months)

    # Reset months button
    if st.sidebar.button("Reset Months"):
        st.session_state["selected_months"] = []
        st.rerun()

    # Update session state
    if (selected_points != st.session_state["selected_points"] or
            selected_months != st.session_state["selected_months"]):
        st.session_state["selected_points"] = selected_points
        st.session_state["selected_months"] = selected_months
        st.rerun()

    # Ensure at least one month is selected
    if not selected_months:
        st.warning("Please select at least one month.")
        return

    filtered_data = data[(data["Occupation"] == selected_occupation) &
                         (data["EOI Status"] == selected_eoi_status)]

    if selected_points:
        filtered_data = filtered_data[filtered_data["Points"].isin(selected_points)]

    if selected_months:
        filtered_data = filtered_data[
            filtered_data["As At Month"].dt.strftime("%Y-%m").isin(selected_months)]

    filtered_data["Count EOIs"] = filtered_data["Count EOIs"].replace("<20", "5")
    filtered_data["Count EOIs"] = pd.to_numeric(filtered_data["Count EOIs"])

    # Get unique points that actually have data
    points_with_data = sorted(filtered_data["Points"].unique(), reverse=True)

    # Create traces for each month
    traces = []
    for month in selected_months:
        month_data = filtered_data[
            filtered_data["As At Month"].dt.strftime("%Y-%m") == month]
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
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.99, traceorder="reversed")
    )

    # Create the figure and plot
    fig = go.Figure(data=traces, layout=layout)
    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()