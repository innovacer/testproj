# retirement_planner_improved.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io

# -----------------------------------------------------------------------------
#                              Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Retirement Planning Service",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
#                             Caching and Setup
# -----------------------------------------------------------------------------
@st.cache_data
def load_life_expectancy_data():
    """Load life expectancy data from CSV string."""
    data = """
Gender,Current Age,Average Life Expectancy Age,1 In 4 Chance Age,1 in 10 Chance Age
Male,54,84,93,97
Male,55,84,92,97
Male,56,84,92,97
Male,57,84,92,97
Male,58,84,92,97
Male,59,84,92,97
Male,60,85,92,97
Male,61,85,92,97
Male,62,85,92,97
Male,63,85,92,96
Male,64,85,92,96
Male,65,85,92,96
Male,66,85,92,96
Male,67,85,92,96
Male,68,86,92,96
Male,69,86,92,96
Male,70,86,92,96
Male,71,86,92,96
Male,72,86,92,96
Male,73,87,92,96
Male,74,87,92,96
Male,75,87,92,96
Male,76,87,92,96
Male,77,88,92,96
Male,78,88,92,96
Male,79,88,93,96
Male,80,89,93,96
Male,81,89,93,97
Male,82,90,93,97
Male,83,90,93,97
Male,84,91,94,97
Male,85,91,94,97
Male,86,92,94,98
Male,87,92,95,98
Male,88,93,95,98
Male,89,94,96,98
Male,90,94,96,99
Male,91,95,97,99
Male,92,96,97,100
Male,93,96,98,100
Male,94,97,98,101
Male,95,98,99,101
Male,96,99,100,102
Male,97,99,100,102
Male,98,100,101,103
Male,99,101,102,104
Male,100,102,103,104
Female,54,87,95,99
Female,55,87,95,99
Female,56,87,95,99
Female,57,87,94,99
Female,58,87,94,99
Female,59,87,94,99
Female,60,87,94,98
Female,61,87,94,98
Female,62,87,94,98
Female,63,87,94,98
Female,64,87,94,98
Female,65,87,94,98
Female,66,87,94,98
Female,67,88,94,98
Female,68,88,94,98
Female,69,88,94,98
Female,70,88,94,98
Female,71,88,94,98
Female,72,88,94,98
Female,73,88,94,98
Female,74,89,94,98
Female,75,89,94,98
Female,76,89,94,98
Female,77,89,94,98
Female,78,90,94,98
Female,79,90,94,98
Female,80,90,94,98
Female,81,90,94,98
Female,82,91,95,98
Female,83,91,95,98
Female,84,92,95,98
Female,85,92,95,99
Female,86,93,95,99
Female,87,93,96,99
Female,88,94,96,99
Female,89,94,97,99
Female,90,95,97,100
Female,91,95,97,100
Female,92,96,98,100
Female,93,97,98,101
Female,94,97,99,101
Female,95,98,100,102
Female,96,99,100,102
Female,97,100,101,103
Female,98,100,102,103
Female,99,101,102,104
Female,100,102,103,105
"""
    return pd.read_csv(io.StringIO(data))

@st.cache_data
def load_plsa_standards():
    """Load PLSA retirement living standards data."""
    return {
        "Minimum": {"Single": 14400, "Single_London": 15700, "Couple": 22400, "Couple_London": 24500},
        "Moderate": {"Single": 31300, "Single_London": 32800, "Couple": 43100, "Couple_London": 44900},
        "Comfortable": {"Single": 47000, "Single_London": 53000, "Couple": 54000, "Couple_London": 60000}
    }

# -----------------------------------------------------------------------------
#                            Global Assumptions
# -----------------------------------------------------------------------------
assumptions = {
    "inflation_rate": 0.02,  # Annual inflation rate
    "salary_indexation_rate": 0.035,  # Annual salary indexation rate
    "investment_growth_rate": 0.05,   # Annual investment growth rate
    "amc": 0.01,                     # Annual AMC (Annual Management Charge)
    "income_escalation_rate": 0.02,  # Annual income escalation rate
    "state_pension_age": 65,         # Age when state pension starts
    "state_pension_income_now": 10600.20,  # Current annual state pension
    "tax_free_withdrawal_component": 0.25,  # 25% of the fund can be taken as tax-free lump sum
    "annual_allowance_contributions": 60000,
    "money_purchase_annual_allowance": 10000,
    "annual_allowance_high_income_threshold": 200000,
    "annual_allowance_high_income_threshold_adjusted": 260000,
    "personal_allowance_threshold": 100000,
    "no_personal_allowance_threshold": 125000,
    "personal_allowance_taper_rate": 0.5,
    "tax_bands_england": [
        (12570, 0.0),     # Personal Allowance
        (50270, 0.20),    # Basic Rate
        (125140, 0.40),   # Higher Rate
        (np.inf, 0.45)    # Additional Rate
    ],
    # Scottish Tax Bands
    "tax_bands_scotland": [
        (12570, 0.0),    # Personal Allowance
        (14667, 0.19),   # Starter Rate
        (25296, 0.20),   # Basic Rate
        (43662, 0.21),   # Intermediate Rate
        (150000, 0.41),  # Higher Rate
        (np.inf, 0.46)   # Top Rate
    ]
}

# -----------------------------------------------------------------------------
#                          Helper Functions
# -----------------------------------------------------------------------------
def get_life_expectancy(gender, current_age, df_life_exp):
    """
    Returns life expectancy (1 in 4 chance) from the loaded DataFrame.
    If not found, defaults to 90.
    """
    df = df_life_exp[(df_life_exp['Gender'] == gender) & (df_life_exp['Current Age'] == current_age)]
    if not df.empty:
        return int(df['1 In 4 Chance Age'].values[0])
    return 90

def calculate_taxes(income, tax_bands):
    """
    Calculate income tax based on the given tax bands.
    """
    tax = 0
    previous_threshold = 0
    for threshold, rate in tax_bands:
        if income > previous_threshold:
            taxable_income = min(income, threshold) - previous_threshold
            tax += taxable_income * rate
            previous_threshold = threshold
        else:
            break
    return tax

def calculate_state_pension_income(current_age):
    """
    Calculates the projected state pension income at the state's pension age,
    adjusted for inflation from the current_age to the state pension age.
    """
    years_until_state_pension = assumptions['state_pension_age'] - current_age
    if years_until_state_pension <= 0:
        # Already reached or past state pension age
        return assumptions['state_pension_income_now']
    return assumptions['state_pension_income_now'] * ((1 + assumptions['inflation_rate']) ** years_until_state_pension)

# -----------------------------------------------------------------------------
#                       Core Projection Calculation
# -----------------------------------------------------------------------------
def project_pension(
    current_age, retirement_age, initial_fund,
    monthly_contribution, monthly_employer_contribution,
    investment_growth_rate, salary_growth_rate, inflation_rate,
    target_income, annual_retirement_income,
    include_state_pension, include_db_pension,
    db_pension_income, db_pension_age,
    income_start_age, income_end_age,
    tax_free_cash_option, partial_tax_free_cash=0, ufpls_amount=0,
    strategy="Accumulation",
    immediate_capital_goal=0,
    existing_tfc_withdrawals=0,
    max_age=90,
    tax_bands=None,
):
    """
    Projects pension fund growth (pre-retirement) and retirement income
    (post-retirement) based on user-selected strategy.
    """
    years = np.arange(current_age, max_age + 1)
    uncrystallised_fund_values = []
    crystallised_fund_values = []
    total_fund_values = []
    incomes = []
    taxes = []
    net_incomes = []
    shortfalls = []

    uncrystallised_fund = initial_fund
    crystallised_fund = 0
    annual_contribution = (monthly_contribution + monthly_employer_contribution) * 12

    # If "Decumulation Income (capital)" and retirement age is basically now
    if strategy == "Decumulation Income (capital)" and (retirement_age - current_age) <= 1:
        retirement_age = current_age

    # Pre-calc state pension at retirement (for indexing inflation).
    state_pension_income_at_retirement = calculate_state_pension_income(current_age)
    annual_retirement_income_adjusted = annual_retirement_income

    # Calculate max TFC available
    max_tax_free_cash_available = uncrystallised_fund * assumptions['tax_free_withdrawal_component']
    max_tax_free_cash_available -= existing_tfc_withdrawals
    max_tax_free_cash_available = max(0, max_tax_free_cash_available)

    for age in years:
        tax_free_cash = 0
        # Grow uncrystallised fund pre-retirement by net growth
        # (growth_rate - AMC - inflation to keep real terms).
        uncrystallised_fund *= (1 + investment_growth_rate - assumptions['amc'] - inflation_rate)

        # ------------------------ Before Retirement ---------------------------
        if age < retirement_age:
            if strategy == "Accumulation":
                # Add contributions
                uncrystallised_fund += annual_contribution
                annual_contribution *= (1 + salary_growth_rate)

            # No normal retirement income withdrawn
            income = 0
            tax = 0
            net_income = 0
            shortfall = 0

            # Handle immediate capital needs for decumulation strategies
            if age == current_age and strategy != "Accumulation":
                if immediate_capital_goal > 0:
                    if strategy == "Decumulation – capital only":
                        # 100% taxable withdrawal allowed
                        withdrawal = min(immediate_capital_goal, uncrystallised_fund)
                        uncrystallised_fund -= withdrawal
                        income = withdrawal
                        tax = calculate_taxes(income, tax_bands)
                        net_income = income - tax
                    elif strategy == "Decumulation Income (capital)":
                        # Use up to 100% TFC
                        withdrawal = min(immediate_capital_goal, max_tax_free_cash_available)
                        # Crystallising: 4x the TFC (1 part tax-free, 3 parts crystallised)
                        uncrystallised_fund -= withdrawal * 4
                        crystallised_fund += (withdrawal * 3)
                        income = withdrawal  # tax-free
                        net_income = income
                        max_tax_free_cash_available -= withdrawal

                    shortfall = 0

        # ------------------------- After Retirement ---------------------------
        else:
            if age == retirement_age:
                annual_retirement_income_adjusted = annual_retirement_income
            else:
                # Adjust with inflation annually
                annual_retirement_income_adjusted *= (1 + inflation_rate)

            # Handle TFC at retirement if strategy is "Accumulation"
            if (age == retirement_age and strategy == "Accumulation"):
                if tax_free_cash_option == "Full tax-free cash":
                    tax_free_cash = uncrystallised_fund * assumptions['tax_free_withdrawal_component']
                    uncrystallised_fund -= tax_free_cash
                    # The rest becomes crystallised
                    crystallised_fund += uncrystallised_fund
                    uncrystallised_fund = 0

                elif tax_free_cash_option == "Partial tax-free cash":
                    max_tfc = uncrystallised_fund * assumptions['tax_free_withdrawal_component']
                    partial_tax_free_cash = min(partial_tax_free_cash, max_tfc)
                    uncrystallised_fund -= partial_tax_free_cash
                    crystallised_amount = partial_tax_free_cash * 3
                    crystallised_fund += crystallised_amount
                    uncrystallised_fund -= crystallised_amount
                    tax_free_cash = partial_tax_free_cash

                elif tax_free_cash_option == "UFPLS":
                    ufpls_amount = min(ufpls_amount, uncrystallised_fund)
                    uncrystallised_fund -= ufpls_amount
                    tax_free_cash = ufpls_amount * 0.25
                    taxable_cash = ufpls_amount * 0.75
                    income = taxable_cash + tax_free_cash
                    tax = calculate_taxes(income - tax_free_cash, tax_bands)
                    net_income = income - tax
                    shortfall = max(0, target_income - net_income)

                # If "No tax-free cash," do nothing special
                else:
                    tax_free_cash = 0

            # Now handle retirement income
            # If we haven't done a UFPLS in the same year or if strategy != "Accumulation"
            if (tax_free_cash_option != "UFPLS" or age > retirement_age) or (strategy != "Accumulation"):
                income = 0
                # State pension?
                if include_state_pension and age >= assumptions['state_pension_age']:
                    sp_income = state_pension_income_at_retirement * ((1 + inflation_rate) ** (age - assumptions['state_pension_age']))
                    income += sp_income
                else:
                    sp_income = 0

                # DB pension?
                if include_db_pension and age >= db_pension_age:
                    adjusted_db_pension = db_pension_income * ((1 + inflation_rate) ** (age - db_pension_age))
                    income += adjusted_db_pension
                else:
                    adjusted_db_pension = 0

            # Check if we are in the desired income drawdown window
            if income_start_age <= age <= income_end_age:
                # Additional draw needed (beyond state and DB pensions)
                remaining_needed = max(0, annual_retirement_income_adjusted - income)

                # First, try from uncrystallised fund as tax-free
                if uncrystallised_fund > 0 and remaining_needed > 0:
                    # We escalate the required amount with inflation from retirement_age, if desired
                    tax_free_draw = remaining_needed * ((1 + inflation_rate) ** (age - retirement_age))
                    withdrawal = min(uncrystallised_fund, tax_free_draw)
                    uncrystallised_fund -= withdrawal
                    # Crystallise 3x withdrawal
                    crystallised_amt = withdrawal * 3
                    crystallised_fund += crystallised_amt
                    uncrystallised_fund -= min(uncrystallised_fund, crystallised_amt)
                    income += withdrawal
                    tax_free_cash = withdrawal

                else:
                    # If no uncrystallised, or we still have more to withdraw, pull from crystallised
                    if crystallised_fund > 0:
                        taxable_amount = remaining_needed * ((1 + inflation_rate) ** (age - retirement_age))
                        withdrawal = min(crystallised_fund, taxable_amount)
                        crystallised_fund -= withdrawal
                        income += withdrawal
                        tax_free_cash = 0

            else:
                # No additional regular income in this age
                remaining_needed = 0

            # Calculate taxes
            tax = calculate_taxes(income - tax_free_cash, tax_bands)
            net_income = income - tax

            # Only measure shortfall after retirement
            shortfall = max(0, target_income - net_income)

        # Record the funds and incomes each year
        total_fund = uncrystallised_fund + crystallised_fund
        uncrystallised_fund_values.append(uncrystallised_fund)
        crystallised_fund_values.append(crystallised_fund)
        total_fund_values.append(total_fund)
        incomes.append(income)
        taxes.append(tax)
        net_incomes.append(net_income)
        shortfalls.append(shortfall)

    return (years,
            uncrystallised_fund_values,
            crystallised_fund_values,
            total_fund_values,
            incomes,
            taxes,
            net_incomes,
            shortfalls)

# -----------------------------------------------------------------------------
#                             Display Functions
# -----------------------------------------------------------------------------
def create_projection_charts(df, retirement_age, target_income):
    """
    Creates interactive Plotly charts for Pension Fund, Income, and Shortfall.
    Returns them as a list of Plotly Figure objects.
    """
    # 1) Pension Fund Chart
    fig_fund = go.Figure()
    fig_fund.add_trace(go.Scatter(
        x=df['Age'],
        y=df['Uncrystallised Fund (£)'],
        mode='lines',
        name='Uncrystallised Fund'
    ))
    fig_fund.add_trace(go.Scatter(
        x=df['Age'],
        y=df['Crystallised Fund (£)'],
        mode='lines',
        name='Crystallised Fund'
    ))
    fig_fund.add_trace(go.Scatter(
        x=df['Age'],
        y=df['Total Fund (£)'],
        mode='lines',
        name='Total Fund',
        line=dict(dash='dash')
    ))
    # Retirement Age Line
    fig_fund.add_vline(x=retirement_age, line_width=2, line_dash="dash", line_color="red")
    fig_fund.update_layout(
        title="Pension Fund Projection",
        xaxis_title="Age",
        yaxis_title="Fund Value (£)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )

    # 2) Income vs Target Chart
    fig_income = go.Figure()
    fig_income.add_trace(go.Scatter(
        x=df['Age'],
        y=df['Net Income (£)'],
        mode='lines',
        name='Net Retirement Income'
    ))
    fig_income.add_trace(go.Scatter(
        x=df['Age'],
        y=[target_income]*len(df['Age']),
        mode='lines',
        name='Target Income',
        line=dict(dash='dash')
    ))
    # Retirement Age Line
    fig_income.add_vline(x=retirement_age, line_width=2, line_dash="dash", line_color="red")
    fig_income.update_layout(
        title="Retirement Income Projection",
        xaxis_title="Age",
        yaxis_title="Annual Net Income (£)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )

    # 3) Shortfall Chart
    fig_shortfall = go.Figure()
    fig_shortfall.add_trace(go.Scatter(
        x=df['Age'],
        y=df['Income Shortfall (£)'],
        mode='lines',
        name='Income Shortfall',
        line=dict(color='orange')
    ))
    # Retirement Age Line
    fig_shortfall.add_vline(x=retirement_age, line_width=2, line_dash="dash", line_color="red")
    fig_shortfall.update_layout(
        title="Income Shortfall Over Time",
        xaxis_title="Age",
        yaxis_title="Shortfall (£)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )

    return [fig_fund, fig_income, fig_shortfall]


def display_projection_table(df):
    """Display the full projection DataFrame in a stylized format."""
    st.dataframe(
        df.style.format({
            'Uncrystallised Fund (£)': '£{:,.2f}',
            'Crystallised Fund (£)': '£{:,.2f}',
            'Total Fund (£)': '£{:,.2f}',
            'Total Income (£)': '£{:,.2f}',
            'Taxes Paid (£)': '£{:,.2f}',
            'Net Income (£)': '£{:,.2f}',
            'Income Shortfall (£)': '£{:,.2f}'
        }),
        height=500
    )

# -----------------------------------------------------------------------------
#                               Main App
# -----------------------------------------------------------------------------
def main():
    st.title("Retirement Planning Service")

    # Load external data
    life_expectancy_df = load_life_expectancy_data()
    plsa_standards = load_plsa_standards()  # currently not mandatory in this version

    # ------------------ Sidebar: Personal & Strategy Inputs ------------------
    st.sidebar.header("Your Details")
    gender = st.sidebar.selectbox("Gender at Birth", ["Male", "Female"])
    current_age = st.sidebar.number_input("Current Age", min_value=55, max_value=100, value=55, step=1)
    salary = st.sidebar.number_input("Current Annual Salary (£)", min_value=0, value=40000, step=1000)
    initial_fund = st.sidebar.number_input("Current Pension Fund Value (£)", min_value=0, value=50000, step=1000)
    existing_tfc_withdrawals = st.sidebar.number_input("Existing Tax-Free Cash Withdrawals (£)", min_value=0.0, value=0.0, step=1000.0)

    # Determine max_age from life expectancy
    max_age = get_life_expectancy(gender, current_age, life_expectancy_df)
    st.sidebar.write(f"**Projection will run until age {max_age} (1 in 4 chance age).**")

    # Location for tax
    st.sidebar.header("Location")
    lives_in_scotland = st.sidebar.selectbox("Lives in Scotland?", ["No", "Yes"])
    if lives_in_scotland == "Yes":
        tax_bands = assumptions['tax_bands_scotland']
    else:
        tax_bands = assumptions['tax_bands_england']

    # Strategy
    st.sidebar.header("Select Your Retirement Strategy")
    strategy = st.sidebar.selectbox(
        "Retirement Strategy",
        ["Accumulation", "Decumulation – capital only", "Decumulation Income (capital)"]
    )

    # Strategy-specific inputs
    if strategy == "Accumulation":
        retirement_age = st.sidebar.number_input(
            "Target Retirement Age",
            min_value=current_age+1,
            max_value=100,
            value=65
        )
        monthly_contribution = st.sidebar.number_input("Your Monthly Pension Contribution (£)", min_value=0, value=200)
        monthly_employer_contribution = st.sidebar.number_input("Employer Monthly Pension Contribution (£)", min_value=0, value=200)
        immediate_capital_goal = 0
    else:
        retirement_age = st.sidebar.number_input(
            "Target Retirement Age",
            min_value=current_age,
            max_value=100,
            value=current_age
        )
        monthly_contribution = 0
        monthly_employer_contribution = 0
        immediate_capital_goal = st.sidebar.number_input("Immediate Capital Goal (£)", min_value=0.0, value=0.0)

    # --------------------------- Retirement Income ---------------------------
    st.sidebar.header("Retirement Income Goal")
    essential_expenditure = st.sidebar.number_input("Essential Expenditure (£)", min_value=0.0, value=15000.0, step=1000.0)
    discretionary_expenditure = st.sidebar.number_input("Discretionary Expenditure (£)", min_value=0.0, value=5000.0, step=1000.0)
    initial_target_income = essential_expenditure + discretionary_expenditure

    target_income = st.sidebar.number_input(
        "Target Annual Income (£)",
        min_value=initial_target_income,
        value=initial_target_income,
        step=1000.0,
        help="Should be at least the sum of essential + discretionary expenditures."
    )
    st.sidebar.header("Income Timing")
    income_start_age = st.sidebar.number_input(
        "Income Start Age",
        min_value=int(retirement_age),
        max_value=100,
        value=int(retirement_age),
        help="Age at which you want your regular income to start."
    )
    income_end_age = st.sidebar.number_input(
        "Income End Age",
        min_value=int(income_start_age),
        max_value=100,
        value=int(retirement_age + 20),
        help="Age at which you want your regular income to end."
    )
    # Ensure integer
    income_start_age = int(income_start_age)
    income_end_age = int(income_end_age)

    annual_retirement_income = st.sidebar.number_input(
        "Desired Annual Retirement Income (£)",
        min_value=target_income,
        value=target_income,
        step=1000.0
    )

    include_state_pension = st.sidebar.checkbox("Include State Pension", value=True)
    include_db_pension = st.sidebar.checkbox("Include Defined Benefit (DB) Pension", value=False)
    db_pension_income = 0
    db_pension_age = retirement_age
    if include_db_pension:
        db_pension_income = st.sidebar.number_input("Annual DB Pension Income (£)", min_value=0, value=10000, step=1000)
        db_pension_age = st.sidebar.number_input("DB Pension Starting Age", min_value=int(retirement_age), max_value=100, value=int(retirement_age))

    # Tax-Free Cash Options
    if strategy == "Accumulation":
        st.sidebar.header("Tax-Free Cash Options at Retirement")
        tax_free_cash_option = st.sidebar.selectbox(
            "Choose an option:",
            ["No tax-free cash", "Full tax-free cash", "Partial tax-free cash", "UFPLS"]
        )
        partial_tax_free_cash = 0
        ufpls_amount = 0
        if tax_free_cash_option == "Partial tax-free cash":
            partial_tax_free_cash = st.sidebar.number_input(
                "Partial tax-free cash (£)",
                min_value=0.0,
                value=0.0,
                step=1000.0
            )
        elif tax_free_cash_option == "UFPLS":
            ufpls_amount = st.sidebar.number_input(
                "UFPLS amount (£)",
                min_value=0.0,
                value=0.0,
                step=1000.0
            )
    else:
        tax_free_cash_option = "No tax-free cash"
        partial_tax_free_cash = 0
        ufpls_amount = 0

    # --------------------------- Assumptions ---------------------------
    st.sidebar.header("Assumptions")
    investment_growth_rate = st.sidebar.slider("Investment Growth Rate (%)", 0.0, 10.0, 5.0, 0.5) / 100
    salary_growth_rate = st.sidebar.slider("Salary Growth Rate (%)", 0.0, 10.0, 2.0, 0.5) / 100
    inflation_rate = st.sidebar.slider("Inflation Rate (%)", 0.0, 10.0, 2.0, 0.5) / 100

    st.markdown("---")

    # --------------------------- Run Projection --------------------------
    if st.button("Run Retirement Projection"):
        (years,
         uncrystallised_vals,
         crystallised_vals,
         total_vals,
         incomes,
         taxes,
         net_incomes,
         shortfalls) = project_pension(
            current_age=current_age,
            retirement_age=retirement_age,
            initial_fund=initial_fund,
            monthly_contribution=monthly_contribution,
            monthly_employer_contribution=monthly_employer_contribution,
            investment_growth_rate=investment_growth_rate,
            salary_growth_rate=salary_growth_rate,
            inflation_rate=inflation_rate,
            target_income=target_income,
            annual_retirement_income=annual_retirement_income,
            include_state_pension=include_state_pension,
            include_db_pension=include_db_pension,
            db_pension_income=db_pension_income,
            db_pension_age=db_pension_age,
            income_start_age=income_start_age,
            income_end_age=income_end_age,
            tax_free_cash_option=tax_free_cash_option,
            partial_tax_free_cash=partial_tax_free_cash,
            ufpls_amount=ufpls_amount,
            strategy=strategy,
            immediate_capital_goal=immediate_capital_goal,
            existing_tfc_withdrawals=existing_tfc_withdrawals,
            max_age=max_age,
            tax_bands=tax_bands,
        )

        # Create results DataFrame
        df_results = pd.DataFrame({
            'Age': years,
            'Uncrystallised Fund (£)': uncrystallised_vals,
            'Crystallised Fund (£)': crystallised_vals,
            'Total Fund (£)': total_vals,
            'Total Income (£)': incomes,
            'Taxes Paid (£)': taxes,
            'Net Income (£)': net_incomes,
            'Income Shortfall (£)': shortfalls
        })

        # --------------------- Tabs for Output --------------------
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Projection Table",
            "Charts",
            "Personalized Messages",
            "Risk Warnings",
            "Next Steps"
        ])

        with tab1:
            st.subheader("Projection Results")
            display_projection_table(df_results)

        with tab2:
            st.subheader("Projection Charts")
            chart_fund, chart_income, chart_shortfall = create_projection_charts(
                df_results,
                retirement_age,
                target_income
            )
            st.plotly_chart(chart_fund, use_container_width=True)
            st.plotly_chart(chart_income, use_container_width=True)
            st.plotly_chart(chart_shortfall, use_container_width=True)

        with tab3:
            st.subheader("Personalized Messages")
            post_retirement_shortfalls = [
                s for age, s in zip(years, shortfalls) 
                if age >= retirement_age and s > 0
            ]
            if post_retirement_shortfalls:
                st.warning("**Income Shortfall Detected:** You may not meet your desired retirement income with current inputs.")
                st.write("Consider:")
                st.write("- Increasing monthly contributions (if possible).")
                st.write("- Adjusting your planned retirement age.")
                st.write("- Reviewing your investment growth assumptions.")
                st.write("- Reducing your target annual income or spending.")
            else:
                st.success("**On Track:** You're on track to meet your retirement income goals under current assumptions!")

        with tab4:
            st.subheader("Important Risk Warnings")
            st.markdown(
                """
                - **Investment Risk:** The value of investments can fall as well as rise, and you may get back less than you invested.
                - **Inflation Risk:** Inflation can reduce the real value of your savings and investment returns.
                - **Longevity Risk:** You may live longer than anticipated, leading to the risk of outliving your savings.
                - **Taxation:** Tax rules can change and benefits depend on individual circumstances.
                """
            )

        with tab5:
            st.subheader("Next Steps")
            st.write("You have options to further explore or save your plan:")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Plan"):
                    st.success("Your plan has been saved securely (simulation).")
            with col2:
                if st.button("Contact a Retirement Consultant"):
                    st.info("Call us at 0800 123 4567 or email support@example.com for personalized advice.")

    else:
        st.info("Use the sidebar to configure your details and click 'Run Retirement Projection' to see results.")

# -----------------------------------------------------------------------------
#                                Entry Point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
