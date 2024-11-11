import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from typing import List, Optional, Dict
from dataclasses import dataclass


@dataclass
class VisaConfig:
    """Configuration class for visa types and related data."""

    VISA_TYPES = ["189 Visa", "190 Visa"]
    BASE_DIR = os.path.join(os.getcwd(), "data")


class DataLoader:
    """Handle all data loading operations."""

    @staticmethod
    def get_state_folders(visa_type: str) -> List[str]:
        """Get available state folders for 190 visa type."""
        if visa_type != "190":
            return []

        visa_dir = os.path.join(VisaConfig.BASE_DIR, "190")
        if not os.path.exists(visa_dir):
            return []

        return [
            d for d in os.listdir(visa_dir) if os.path.isdir(os.path.join(visa_dir, d))
        ]

    @staticmethod
    def load_data(visa_type: str, state: Optional[str] = None) -> pd.DataFrame:
        """Load data based on visa type and state."""
        dfs = []

        data_dir = DataLoader._get_data_directory(visa_type, state)
        if not os.path.exists(data_dir):
            return pd.DataFrame()

        for filename in os.listdir(data_dir):
            if filename.endswith(".csv"):
                df = DataLoader._process_csv_file(os.path.join(data_dir, filename))
                dfs.append(df)

        return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

    @staticmethod
    def _get_data_directory(visa_type: str, state: Optional[str]) -> str:
        """Get the appropriate data directory based on visa type and state."""
        if visa_type == "189":
            return os.path.join(VisaConfig.BASE_DIR, "189")
        return os.path.join(VisaConfig.BASE_DIR, "190", state) if state else ""

    @staticmethod
    def _process_csv_file(file_path: str) -> pd.DataFrame:
        """Process a single CSV file and return the DataFrame."""
        df = pd.read_csv(file_path)
        df["As At Month"] = pd.to_datetime(df["As At Month"], format="%m/%Y")
        return df


class SessionStateManager:
    """Manage Streamlit session state."""

    @staticmethod
    def initialize_session_state():
        """Initialize all required session state variables."""
        session_vars = {
            "data": None,
            "selected_points": [],
            "selected_months": [],
            "current_visa_type": None,
            "current_state": None,
        }

        for var, default_value in session_vars.items():
            if var not in st.session_state:
                st.session_state[var] = default_value

    @staticmethod
    def should_reload_data(visa_type: str, selected_state: Optional[str]) -> bool:
        """Check if data should be reloaded based on current state."""
        return (
            st.session_state["current_visa_type"] != visa_type
            or st.session_state["current_state"] != selected_state
        )

    @staticmethod
    def reset_session_state(visa_type: str, selected_state: Optional[str]):
        """Reset session state for new visa type or state."""
        st.session_state.update(
            {
                "data": None,
                "current_visa_type": visa_type,
                "current_state": selected_state,
                "selected_points": [],
                "selected_months": [],
            }
        )


class DataFilterManager:
    """Handle data filtering operations."""

    @staticmethod
    def get_filtered_data(data: pd.DataFrame, filters: Dict) -> pd.DataFrame:
        """Apply all filters to the data."""
        filtered_data = data[
            (data["Occupation"] == filters["occupation"])
            & (data["EOI Status"] == filters["eoi_status"])
        ]

        if filters["points"]:
            filtered_data = filtered_data[
                filtered_data["Points"].isin(filters["points"])
            ]

        if filters["months"]:
            filtered_data = filtered_data[
                filtered_data["As At Month"]
                .dt.strftime("%Y-%m")
                .isin(filters["months"])
            ]

        filtered_data = DataFilterManager._process_eoi_counts(filtered_data)
        return filtered_data

    @staticmethod
    def _process_eoi_counts(data: pd.DataFrame) -> pd.DataFrame:
        """Process EOI counts, converting '<20' to numeric values."""
        data = data.copy()
        data["Count EOIs"] = data["Count EOIs"].replace("<20", "5")
        data["Count EOIs"] = pd.to_numeric(data["Count EOIs"])
        return data


class PlotManager:
    """Handle all plotting operations."""

    @staticmethod
    def create_plot(
        filtered_data: pd.DataFrame,
        selected_months: List[str],
        visa_type: str,
        occupation: str,
        eoi_status: str,
        selected_state: Optional[str] = None,
    ) -> go.Figure:
        """Create the plotly figure for visualization."""
        points_with_data = sorted(filtered_data["Points"].unique(), reverse=True)
        traces = PlotManager._create_traces(filtered_data, selected_months)
        layout = PlotManager._create_layout(
            points_with_data,
            selected_months,
            visa_type,
            occupation,
            eoi_status,
            selected_state,
        )
        return go.Figure(data=traces, layout=layout)

    @staticmethod
    def _create_traces(
        filtered_data: pd.DataFrame, selected_months: List[str]
    ) -> List[go.Bar]:
        """Create bar traces for each month."""
        traces = []
        for month in selected_months:
            month_data = filtered_data[
                filtered_data["As At Month"].dt.strftime("%Y-%m") == month
            ]
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
        return traces

    @staticmethod
    def _create_layout(
        points_with_data: List[float],
        selected_months: List[str],
        visa_type: str,
        occupation: str,
        eoi_status: str,
        selected_state: Optional[str],
    ) -> go.Layout:
        """Create the plot layout."""
        height = max(600, len(points_with_data) * len(selected_months) * 30)
        title_suffix = f" - {selected_state}" if visa_type == "190" else ""

        return go.Layout(
            barmode="group",
            title=f"{visa_type} Visa EOI Analysis for {occupation} - {eoi_status}{title_suffix}",
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


class EOIAnalysisApp:
    """Main application class."""

    def __init__(self):
        st.set_page_config(layout="wide")
        SessionStateManager.initialize_session_state()

    def run(self):
        """Run the main application."""
        self._setup_sidebar()

        if not self._validate_data():
            return

        self._handle_filters()
        self._create_visualization()

    def _setup_sidebar(self):
        """Set up the sidebar with all necessary inputs."""
        st.sidebar.title("EOI Analysis App")

        # Visa type selection
        visa_type = st.sidebar.radio(
            "Select Visa Type", VisaConfig.VISA_TYPES, horizontal=True
        )
        self.visa_type = visa_type.split()[0]

        # State selection for 190 visa
        self.selected_state = None
        if self.visa_type == "190":
            states = DataLoader.get_state_folders(self.visa_type)
            if not states:
                st.warning("No state data found for 190 visa.")
                return
            self.selected_state = st.sidebar.radio(
                "Select State", states, horizontal=True
            )

    def _validate_data(self) -> bool:
        """Validate and load data if necessary."""
        if SessionStateManager.should_reload_data(self.visa_type, self.selected_state):
            SessionStateManager.reset_session_state(self.visa_type, self.selected_state)

        if st.session_state["data"] is None:
            st.session_state["data"] = DataLoader.load_data(
                self.visa_type, self.selected_state
            )
            if st.session_state["data"].empty:
                st.warning(
                    f"No CSV files found for the selected {'state' if self.visa_type == '190' else 'visa type'}."
                )
                return False
            st.sidebar.success("Data loaded successfully!")

        return True

    def _handle_filters(self):
        """Handle all filter selections."""
        data = st.session_state["data"]

        # Occupation and EOI Status
        self.occupation = st.sidebar.selectbox(
            "Select Occupation", data["Occupation"].unique()
        )
        self.eoi_status = st.sidebar.selectbox(
            "Select EOI Status", data["EOI Status"].unique()
        )

        # Points filter
        all_points = sorted(data["Points"].unique(), reverse=True)
        self.selected_points = st.sidebar.multiselect(
            "Select Points (Optional)",
            all_points,
            default=st.session_state["selected_points"],
        )

        if st.sidebar.button("Reset Points"):
            st.session_state["selected_points"] = []
            st.rerun()

        # Month filter
        all_months = sorted(
            data["As At Month"].dt.strftime("%Y-%m").unique(), reverse=True
        )
        self.selected_months = st.sidebar.multiselect(
            "Select Months (Optional)",
            all_months,
            default=st.session_state["selected_months"] or all_months,
        )

        if st.sidebar.button("Reset Months"):
            st.session_state["selected_months"] = []
            st.rerun()

        # Update session state if necessary
        if (
            self.selected_points != st.session_state["selected_points"]
            or self.selected_months != st.session_state["selected_months"]
        ):
            st.session_state["selected_points"] = self.selected_points
            st.session_state["selected_months"] = self.selected_months
            st.rerun()

        # Validate month selection
        if not self.selected_months:
            st.warning("Please select at least one month.")
            st.stop()

    def _create_visualization(self):
        """Create and display the visualization."""
        filters = {
            "occupation": self.occupation,
            "eoi_status": self.eoi_status,
            "points": self.selected_points,
            "months": self.selected_months,
        }

        filtered_data = DataFilterManager.get_filtered_data(
            st.session_state["data"], filters
        )
        fig = PlotManager.create_plot(
            filtered_data,
            self.selected_months,
            self.visa_type,
            self.occupation,
            self.eoi_status,
            self.selected_state,
        )

        st.plotly_chart(fig, use_container_width=True)


def main():
    app = EOIAnalysisApp()
    app.run()


if __name__ == "__main__":
    main()
