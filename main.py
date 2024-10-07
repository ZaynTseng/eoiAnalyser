import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os


def load_data():
    dfs = []
    data_dir = os.path.join(os.getcwd(), 'data')
    for filename in os.listdir(data_dir):
        if filename.endswith('.csv'):
            file_path = os.path.join(data_dir, filename)
            df = pd.read_csv(file_path)
            df["As At Month"] = pd.to_datetime(df["As At Month"],
                                               format="%m/%Y")
            dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


def main():
    st.set_page_config(layout="wide")
    st.sidebar.title("EOI Analysis App")

    # Initialize session state
    if "data" not in st.session_state:
        st.session_state["data"] = None
    if "selected_points" not in st.session_state:
        st.session_state["selected_points"] = []
    if "selected_months" not in st.session_state:
        st.session_state["selected_months"] = []

    # Load data from local directory
    if st.session_state["data"] is None:
        st.session_state["data"] = load_data()
        if st.session_state["data"].empty:
            st.warning("No CSV files found in the /data/ directory.")
            return
        st.sidebar.success("Data loaded successfully!")

    data = st.session_state["data"]

    occupations = data["Occupation"].unique()
    selected_occupation = st.sidebar.selectbox("Select Occupation",
                                               occupations)

    eoi_statuses = data["EOI Status"].unique()
    selected_eoi_status = st.sidebar.selectbox("Select EOI Status",
                                               eoi_statuses)

    # Points filter
    all_points = sorted(data["Points"].unique(), reverse=True)
    selected_points = st.sidebar.multiselect("Select Points (Optional)",
                                             all_points,
                                             default=st.session_state[
                                                 "selected_points"])

    # Reset points button
    if st.sidebar.button("Reset Points"):
        st.session_state["selected_points"] = []
        st.rerun()

    # Month filter
    all_months = sorted(data["As At Month"].dt.strftime("%Y-%m").unique(),
                        reverse=True)
    selected_months = st.sidebar.multiselect("Select Months (Optional)",
                                             all_months,
                                             default=st.session_state[
                                                         "selected_months"] or all_months)

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
        filtered_data = filtered_data[
            filtered_data["Points"].isin(selected_points)]

    if selected_months:
        filtered_data = filtered_data[
            filtered_data["As At Month"].dt.strftime("%Y-%m").isin(
                selected_months)]

    filtered_data["Count EOIs"] = filtered_data["Count EOIs"].replace("<20",
                                                                      "5")
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
    layout = go.Layout(
        barmode="group",
        title=f"EOI Analysis for {selected_occupation} - {selected_eoi_status}",
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
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.99,
                    traceorder="reversed")
    )

    # Create the figure and plot
    fig = go.Figure(data=traces, layout=layout)
    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
