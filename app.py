#Importing libraries  to run the environment pandas, plotply and sreamlit
import pandas as pd
import plotly.express as px
import streamlit as st



DATA_FILE = "KEIR8CFL_data.csv"

st.set_page_config(
    page_title="KENYA MODERN CONTRACEPTIVE UPTAKE DASHBORAD",
    layout="wide",
)


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    KEIR8CFL_data1 = pd.read_csv(path)

    # Preserve the notebook's column-cleaning logic.
    KEIR8CFL_data1.columns = (
        KEIR8CFL_data1.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace(r"[^\w]", "", regex=True)
    )

    #creating the age groups for the for the age variable to assess the modern contraceptive uptake 
    bins = [15, 20, 25, 30, 35, 40, 45, 50]
    labels = ["15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49"]

    KEIR8CFL_data1["age_group"] = pd.cut(
        KEIR8CFL_data1["age"],
        bins=bins,
        labels=labels,
        right=False,
    )

    return KEIR8CFL_data1


def filter_data(
    df: pd.DataFrame,
    education,
    marital,
    residence,
    region,
) -> pd.DataFrame:
    mydata = df.copy()

    if education:
        mydata = mydata[mydata["education_level"].isin(education)]

    if marital:
        mydata = mydata[mydata["marital_status"].isin(marital)]

    if residence:
        mydata = mydata[mydata["residence2"].isin(residence)]

    if region:
        mydata = mydata[mydata["region2"].isin(region)]

    return mydata


def required_columns_present(df: pd.DataFrame) -> bool:
    required = {
        "age",
        "education_level",
        "marital_status",
        "residence2",
        "region2",
        "modern_contraceptive_use",
        "wealth_index",
        "parity",
    }

    missing = sorted(required.difference(df.columns))

    if missing:
        st.error(
            "The dataset is missing required columns: "
            + ", ".join(missing)
        )
        return False

    return True


st.title("Kenya Modern Contraceptive Dashboard")

try:
    data = load_data(DATA_FILE)
except FileNotFoundError:
    st.error(
        f"`{DATA_FILE}` was not found. Put the CSV file in the same "
        "GitHub repository folder as `app.py`, then redeploy."
    )
    st.stop()
except Exception as exc:
    st.error(f"Could not load the dataset: {exc}")
    st.stop()

if not required_columns_present(data):
    st.stop()


#Creating filters to the dashboard to enable interactive aspect
filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

with filter_col1:
    education_filter = st.multiselect(
        "Education",
        options=sorted(data["education_level"].dropna().unique().tolist()),
        placeholder="Select Education",
    )

with filter_col2:
    marital_filter = st.multiselect(
        "Marital Status",
        options=sorted(data["marital_status"].dropna().unique().tolist()),
        placeholder="Select Marital Status",
    )

with filter_col3:
    residence_filter = st.multiselect(
        "Residence",
        options=sorted(data["residence2"].dropna().unique().tolist()),
        placeholder="Select Residence",
    )

with filter_col4:
    region_filter = st.multiselect(
        "Region",
        options=sorted(data["region2"].dropna().unique().tolist()),
        placeholder="Select Region",
    )


mydata = filter_data(
    data,
    education_filter,
    marital_filter,
    residence_filter,
    region_filter,
)


#Key performance indicators  (KPIs)
total = len(mydata)
modern = (
    mydata["modern_contraceptive_use"] == "Modern method"
).sum()

rate = (modern / total * 100) if total else 0
avg_age = mydata["age"].mean()

kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

kpi_col1.metric("Total Women", f"{total:,}")
kpi_col2.metric("Modern Users", f"{modern:,}")
kpi_col3.metric("Uptake Rate", f"{rate:.2f}%")
kpi_col4.metric(
    "Avg Age",
    f"{avg_age:.1f}" if pd.notna(avg_age) else "N/A",
)


if mydata.empty:
    st.warning("No records match the selected filters.")
    st.stop()


# Preserve the notebook's binary modern-use variable.
mydata = mydata.copy()
mydata["Modern Contraceptive Use"] = (
    mydata["modern_contraceptive_use"] == "Modern method"
).astype(int)


# 1. Uptake rate by age group
age_summary = (mydata.groupby("age_group", observed=True)
    .agg(
        users=("Modern Contraceptive Use", "sum"),
        total=("Modern Contraceptive Use", "count"),)
    .reset_index()
)

age_summary["rate"] = (age_summary["users"] / age_summary["total"]) * 100

fig_age = px.line(age_summary,
    x="age_group",
    y="rate",
    markers=True,
    title="Uptake Rate by Age Group",
)


# 2. Uptake rate by education level
edu = (
    mydata
    .groupby("education_level")["Modern Contraceptive Use"]
    .mean()
    .reset_index()
)

fig_edu = px.bar(
    edu,
    x="education_level",
    y="Modern Contraceptive Use",
    title="Uptake rate by Education Level",
)


# 3. Uptake by marital status
mar = (
    mydata
    .groupby("marital_status")["Modern Contraceptive Use"]
    .mean()
    .reset_index()
)

fig_mar = px.bar(
    mar,
    x="marital_status",
    y="Modern Contraceptive Use",
    title="Modern contraceptive Uptake by Marital Status",
)


# 4. Uptake by wealth index
wealth = (
    mydata
    .groupby("wealth_index")["Modern Contraceptive Use"]
    .mean()
    .reset_index()
)

fig_wealth = px.bar(
    wealth,
    x="wealth_index",
    y="Modern Contraceptive Use",
    title="Uptake by Wealth Index",
)


# 5. Contraceptive method distribution
method = (
    mydata["modern_contraceptive_use"]
    .value_counts()
    .reset_index()
)

method.columns = ["method", "count"]

fig_method = px.pie(
    method,
    names="method",
    values="count",
    title="Contraceptive Method Distribution",
)


# 6. Parity by modern contraceptive uptake
parity = (
    mydata
    .groupby("parity")["Modern Contraceptive Use"]
    .mean()
    .reset_index()
)

fig_parity = px.line(
    parity,
    x="parity",
    y="Modern Contraceptive Use",
    title="Gender Parity by Modern Contraceptive Uptake",
)


# 7. Uptake by region
region_df = (
    mydata
    .groupby("region2")["Modern Contraceptive Use"]
    .mean()
    .reset_index()
)

fig_region = px.bar(
    region_df,
    x="region2",
    y="Modern Contraceptive Use",
    title="Moder Contraceptive Uptake by Region",
)


# 8. Probability of contraceptive use by age
age_trend = (
    mydata
    .groupby("age", as_index=False)["Modern Contraceptive Use"]
    .mean()
)

fig_scatter = px.line(
    age_trend,
    x="age",
    y="Modern Contraceptive Use",
    title="Probability of Contraceptive Use by Age",
)

fig_scatter.update_yaxes(title="Probability of Use")


# Dashboard layout
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.plotly_chart(fig_age, use_container_width=True)

with row1_col2:
    st.plotly_chart(fig_edu, use_container_width=True)


row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.plotly_chart(fig_mar, use_container_width=True)

with row2_col2:
    st.plotly_chart(fig_wealth, use_container_width=True)


row3_col1, row3_col2 = st.columns(2)

with row3_col1:
    st.plotly_chart(fig_method, use_container_width=True)

with row3_col2:
    st.plotly_chart(fig_parity, use_container_width=True)


row4_col1, row4_col2 = st.columns(2)

with row4_col1:
    st.plotly_chart(fig_region, use_container_width=True)

with row4_col2:
    st.plotly_chart(fig_scatter, use_container_width=True)
