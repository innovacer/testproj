# retirement_planner.py

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Set page configuration
st.set_page_config(
    page_title="Retirement Planning Service",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Helper Functions and PLSA Standards ---
assumptions = {
    "inflation_rate": 0.02,  # Annual inflation rate
    "salary_indexation_rate": 0.035,  # Annual salary indexation rate
    # "max_age": 120,  # This will be updated based on life expectancy
    "investment_growth_rate": 0.05,  # Annual investment growth rate
    "amc": 0.01,  # Annual AMC (Annual Management Charge)
    "income_escalation_rate": 0.02,  # Annual income escalation rate
    "state_pension_age": 65,  # Age when state pension starts
    "state_pension_income_now": 10600.20,  # Current annual state pension income
    "tax_free_withdrawal_component": 0.25,  # 25% of the fund can be taken as a tax-free lump sum
    "annual_allowance_contributions": 60000,
    "money_purchase_annual_allowance": 10000,
    "annual_allowance_high_income_threshold": 200000,
    "annual_allowance_high_income_threshold_adjusted": 260000,
    "personal_allowance_threshold": 100000,
    "no_personal_allowance_threshold": 125000,
    "personal_allowance_taper_rate": 0.5,
    "tax_bands_england": [
        (12570, 0.0),    # Personal Allowance
        (50270, 0.20),   # Basic Rate
        (125140, 0.40),  # Higher Rate
        (np.inf, 0.45)   # Additional Rate
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

# PLSA Retirement Living Standards Data
plsa_standards = {
    "Minimum": {"Single": 14400, "Single_London": 15700, "Couple": 22400, "Couple_London": 24500},
    "Moderate": {"Single": 31300, "Single_London": 32800, "Couple": 43100, "Couple_London": 44900},
    "Comfortable": {"Single": 47000, "Single_London": 53000, "Couple": 54000, "Couple_London": 60000}
}

# Life Expectancy Data
life_expectancy_data = """
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

import io

# Read the life expectancy data into a DataFrame
life_expectancy_df = pd.read_csv(io.StringIO(life_expectancy_data))

# Function to get life expectancy based on gender and current age
def get_life_expectancy(gender, current_age):
    df = life_expectancy_df[(life_expectancy_df['Gender'] == gender) & (life_expectancy_df['Current Age'] == current_age)]
    if not df.empty:
        return int(df['1 In 4 Chance Age'].values[0])
    else:
        # If age not found, default to 90
        return 90

# Function to calculate taxes based on income
def calculate_taxes(income, tax_bands):
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

# Function to calculate state pension income at retirement age
def calculate_state_pension_income(current_age):
    years_until_state_pension = assumptions['state_pension_age'] - current_age
    state_pension_income_at_retirement = assumptions['state_pension_income_now'] * ((1 + assumptions['inflation_rate']) ** years_until_state_pension)
    return state_pension_income_at_retirement

# Projection function
def project_pension(current_age, retirement_age, initial_fund, monthly_contribution, monthly_employer_contribution,
                    investment_growth_rate, salary_growth_rate, inflation_rate, target_income,
                    annual_retirement_income, include_state_pension, include_db_pension, db_pension_income, db_pension_age,
                    tax_free_cash_option,income_start_age,
                    income_end_age, partial_tax_free_cash=0, ufpls_amount=0,
                    tax_free_lump_sum=False,
                    strategy="Accumulation",
                    immediate_capital_goal=0,
                    existing_tfc_withdrawals=0,
                    max_age=90,
                    tax_bands=None,
                    ):
    """Projects pension fund growth and retirement income."""
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

    # Adjust retirement_age if strategy dictates immediate retirement
    if strategy == "Decumulation Income (capital)" and (retirement_age - current_age) <= 1:
        retirement_age = current_age  # Retirement is now

    # Calculate initial state pension income at state pension age
    state_pension_income_at_retirement = calculate_state_pension_income(current_age)

    # Initialize the annual retirement income with inflation adjustment
    annual_retirement_income_adjusted = annual_retirement_income

    # Calculate maximum TFC available
    max_tax_free_cash_available = uncrystallised_fund * assumptions['tax_free_withdrawal_component']
    # Subtract existing TFC withdrawals
    max_tax_free_cash_available -= existing_tfc_withdrawals
    max_tax_free_cash_available = max(0, max_tax_free_cash_available)

    for age in years:
        tax_free_cash = 0  # Initialize tax_free_cash to zero
        # Apply investment growth to the uncrystallised fund
        uncrystallised_fund *= (1 + investment_growth_rate - assumptions['amc'] - inflation_rate)

        if age < retirement_age:
            # Pre-retirement phase
            if strategy == "Accumulation":
                uncrystallised_fund += annual_contribution
                # Increase contributions with salary growth rate
                annual_contribution *= (1 + salary_growth_rate)
            # No income during pre-retirement
            income = 0
            tax = 0
            net_income = 0
            shortfall = 0  # No shortfall before retirement

            # Handle immediate capital goal for decumulation strategies
            if age == current_age and strategy != "Accumulation":
                if immediate_capital_goal > 0:
                    if strategy == "Decumulation – capital only":
                        # Allow taxable withdrawals up to 100% of DC value
                        withdrawal = min(immediate_capital_goal, uncrystallised_fund)
                        uncrystallised_fund -= withdrawal
                        income = withdrawal
                        tax = calculate_taxes(income, tax_bands)
                        net_income = income - tax
                    elif strategy == "Decumulation Income (capital)":
                        # Allow withdrawals up to 100% of TFC
                        withdrawal = min(immediate_capital_goal, max_tax_free_cash_available)
                        uncrystallised_fund -= withdrawal * 4  # Taking TFC implies crystallising 4 times the amount
                        crystallised_fund += withdrawal * 3
                        income = withdrawal  # Tax-free income
                        net_income = income
                        max_tax_free_cash_available -= withdrawal
                    shortfall = 0  # No shortfall before retirement
        else:
            # Retirement phase

            # Adjust annual retirement income for inflation
            if age == retirement_age:
                annual_retirement_income_adjusted = annual_retirement_income
            else:
                annual_retirement_income_adjusted *= (1 + inflation_rate)

            # Handle tax-free cash options at retirement age
            if age == retirement_age and strategy == "Accumulation":
                if tax_free_cash_option == "Full tax-free cash":
                    # Take 25% of uncrystallised fund as tax-free cash
                    tax_free_cash = uncrystallised_fund * assumptions['tax_free_withdrawal_component']
                    uncrystallised_fund -= tax_free_cash
                    crystallised_fund += uncrystallised_fund  # Move remaining to crystallised fund
                    uncrystallised_fund = 0  # Uncrystallised fund now zero

                elif tax_free_cash_option == "Partial tax-free cash":
                    # Validate partial tax-free cash amount
                    max_tax_free_cash = uncrystallised_fund * assumptions['tax_free_withdrawal_component']
                    partial_tax_free_cash = min(partial_tax_free_cash, max_tax_free_cash)
                    uncrystallised_fund -= partial_tax_free_cash
                    crystallised_amount = partial_tax_free_cash * 3  # Move 3 times the tax-free cash to crystallised
                    crystallised_fund += crystallised_amount
                    uncrystallised_fund -= crystallised_amount
                    tax_free_cash = partial_tax_free_cash

                elif tax_free_cash_option == "UFPLS":
                    # Take specified amount from uncrystallised fund (25% tax-free, 75% taxable)
                    ufpls_amount = min(ufpls_amount, uncrystallised_fund)
                    uncrystallised_fund -= ufpls_amount
                    tax_free_cash = ufpls_amount * 0.25
                    taxable_cash = ufpls_amount * 0.75
                    income = taxable_cash + tax_free_cash
                    tax = calculate_taxes(income - tax_free_cash, tax_bands)
                    net_income = income - tax
                    shortfall = max(0, target_income - net_income)
                else:
                    tax_free_cash = 0  # No tax-free cash taken

            # Income calculation
            if (tax_free_cash_option != "UFPLS" or age > retirement_age) or strategy != "Accumulation":
                income = 0

                # Include state pension if applicable
                if include_state_pension and age >= assumptions['state_pension_age']:
                    state_pension_income = state_pension_income_at_retirement * ((1 + inflation_rate) ** (age - assumptions['state_pension_age']))
                    income += state_pension_income
                else:
                    state_pension_income = 0  # Ensure it's zero if not started yet

                # Include DB pension if applicable
                if include_db_pension and age >= db_pension_age:
                    adjusted_db_pension_income = db_pension_income * ((1 + inflation_rate) ** (age - db_pension_age))
                    income += adjusted_db_pension_income
                else:
                    adjusted_db_pension_income = 0  # Ensure it's zero if not started yet
            if age >= income_start_age and age <= income_end_age:   
                remaining_income_needed = annual_retirement_income_adjusted - income
                remaining_income_needed = max(0, remaining_income_needed)

               
                    # Take income from uncrystallised fund as tax-free cash
                if uncrystallised_fund > 0 and remaining_income_needed>0:
                        tax_free_income = remaining_income_needed * ((1 + inflation_rate) ** (age - retirement_age))
                        withdrawal = min(uncrystallised_fund, tax_free_income)
                        uncrystallised_fund -= withdrawal
                        # Move 3 times the withdrawal to crystallised fund
                        crystallised_amount = withdrawal * 3
                        crystallised_fund += crystallised_amount
                        uncrystallised_fund -= min(uncrystallised_fund, crystallised_amount)
                        income += withdrawal  # Tax-free income
                        tax_free_cash = withdrawal
                else:
                        # Switch to taxable income from crystallised fund
                    if crystallised_fund > 0:
                            taxable_income = remaining_income_needed * ((1 + inflation_rate) ** (age - retirement_age))
                            withdrawal = min(crystallised_fund, taxable_income)
                            crystallised_fund -= withdrawal
                            income += withdrawal
                            tax_free_cash = 0  # This is taxable income
                    else:
                         withdrawal = 0  # No funds to withdraw
                
            else:
                    # No regular income withdrawn during this age
                    remaining_income_needed = 0
                    tax_free_withdrawal = 0
                    taxable_withdrawal = 0
                    tax_free_cash = 0  # No tax-free cash withdrawn

                # Calculate taxes
            tax = calculate_taxes(income - tax_free_cash, tax_bands)
            net_income = income - tax

                # Calculate shortfall only after retirement age
            shortfall = max(0, target_income - net_income)
            if age < retirement_age:
                    shortfall = 0  # No shortfall before retirement

        # Record fund values
        total_fund = uncrystallised_fund + crystallised_fund
        uncrystallised_fund_values.append(uncrystallised_fund)
        crystallised_fund_values.append(crystallised_fund)
        total_fund_values.append(total_fund)
        incomes.append(income)
        taxes.append(tax)
        net_incomes.append(net_income)
        shortfalls.append(shortfall)

    return years, uncrystallised_fund_values, crystallised_fund_values, total_fund_values, incomes, taxes, net_incomes, shortfalls

def display_results(years, uncrystallised_fund_values, crystallised_fund_values, total_fund_values,
                    incomes, taxes, net_incomes, shortfalls, retirement_age, target_income, strategy):
    """Displays projection results with charts."""
    df = pd.DataFrame({
        'Age': years,
        'Uncrystallised Fund (£)': uncrystallised_fund_values,
        'Crystallised Fund (£)': crystallised_fund_values,
        'Total Fund (£)': total_fund_values,
        'Total Income (£)': incomes,
        'Taxes Paid (£)': taxes,
        'Net Income (£)': net_incomes,
        'Income Shortfall (£)': shortfalls
    })
    st.subheader("Projection Results")
    st.dataframe(df.style.format({'Uncrystallised Fund (£)': '£{:,.2f}', 'Crystallised Fund (£)': '£{:,.2f}',
                                  'Total Fund (£)': '£{:,.2f}', 'Total Income (£)': '£{:,.2f}',
                                  'Net Income (£)': '£{:,.2f}', 'Income Shortfall (£)': '£{:,.2f}'}))

    # Display scenario based on strategy
    st.markdown(f"### Scenario: {strategy}")

    # Plotting
    fig, ax = plt.subplots(3, 1, figsize=(10, 15))
    ax[0].plot(df['Age'], df['Uncrystallised Fund (£)'], label='Uncrystallised Fund')
    ax[0].plot(df['Age'], df['Crystallised Fund (£)'], label='Crystallised Fund')
    ax[0].plot(df['Age'], df['Total Fund (£)'], label='Total Fund', linestyle='--')
    ax[0].axvline(x=retirement_age, color='r', linestyle='--', label='Retirement Age')
    ax[0].set_xlabel('Age')
    ax[0].set_ylabel('Fund Value (£)')
    ax[0].set_title('Pension Fund Projection')
    ax[0].legend()
    ax[0].grid(True)

    ax[1].plot(df['Age'], df['Net Income (£)'], label='Net Retirement Income')
    ax[1].plot(df['Age'], [target_income]*len(df['Age']), label='Target Income', linestyle='--')
    ax[1].axvline(x=retirement_age, color='r', linestyle='--', label='Retirement Age')
    ax[1].set_xlabel('Age')
    ax[1].set_ylabel('Annual Net Income (£)')
    ax[1].set_title('Retirement Income Projection')
    ax[1].legend()
    ax[1].grid(True)

    ax[2].plot(df['Age'], df['Income Shortfall (£)'], label='Income Shortfall', color='orange')
    ax[2].axvline(x=retirement_age, color='r', linestyle='--', label='Retirement Age')
    ax[2].set_xlabel('Age')
    ax[2].set_ylabel('Income Shortfall (£)')
    ax[2].set_title('Income Shortfall Over Time')
    ax[2].legend()
    ax[2].grid(True)

    st.pyplot(fig)

# --- Main Application ---

def main():
    st.title("Retirement Planning Service")

    # Sidebar for user inputs
    st.sidebar.header("Your Details")
    gender = st.sidebar.selectbox("Gender at Birth", ["Male", "Female"])
    current_age = st.sidebar.number_input("Current Age", min_value=55, max_value=100, value=55)
    salary = st.sidebar.number_input("Current Annual Salary (£)", min_value=0, value=40000)
    initial_fund = st.sidebar.number_input("Current Pension Fund Value (£)", min_value=0, value=50000)
    existing_tfc_withdrawals = st.sidebar.number_input("Existing Tax-Free Cash Withdrawals (£)", min_value=0.0, value=0.0)

    # Get life expectancy based on gender and current age
    max_age = get_life_expectancy(gender, current_age)
    st.sidebar.write(f"**Projection will run until age {max_age} based on life expectancy data.**")
    # Location
    st.sidebar.header("Location")
    lives_in_scotland = st.sidebar.selectbox("Lives in Scotland?", ["No", "Yes"])

    # Determine tax bands based on location
    if lives_in_scotland == "Yes":
        tax_bands = assumptions['tax_bands_scotland']
    else:
        tax_bands = assumptions['tax_bands_england']

    # Strategy Selection
    st.sidebar.header("Select Your Retirement Strategy")
    strategy = st.sidebar.selectbox("Retirement Strategy", ["Accumulation", "Decumulation – capital only", "Decumulation Income (capital)"])

    # Strategy-specific inputs
    if strategy == "Accumulation":
        retirement_age = st.sidebar.number_input("Target Retirement Age", min_value=current_age+1, max_value=100, value=65)
        monthly_contribution = st.sidebar.number_input("Your Monthly Pension Contribution (£)", min_value=0, value=200)
        monthly_employer_contribution = st.sidebar.number_input("Employer Monthly Pension Contribution (£)", min_value=0, value=200)
        immediate_capital_goal = 0  # Not applicable
    else:
        # Decumulation strategies
        retirement_age = st.sidebar.number_input("Target Retirement Age", min_value=current_age, max_value=100, value=current_age)
        monthly_contribution = 0  # No further contributions
        monthly_employer_contribution = 0
        immediate_capital_goal = st.sidebar.number_input("Immediate Capital Goal (£)", min_value=0.0, value=0.0)

    # Select Living Standard, Location, and Household Type
    #st.sidebar.header("Retirement Income Goal (PLSA Standards)")
    #living_standard = st.sidebar.selectbox("Select Your Retirement Living Standard:", ["Minimum", "Moderate", "Comfortable"])
    #living_location = st.sidebar.selectbox("Are you based in London?", ["No", "Yes"])
    #household_type = st.sidebar.selectbox("Household Type", ["Single", "Couple"])

    # Determine target income based on selected PLSA standards
    #location_key = f"{household_type}_London" if living_location == "Yes" else household_type
    #target_income = plsa_standards[living_standard][location_key]

    # Display the selected target income for user reference
    #st.sidebar.write(f"**Your Target Annual Income (Based on PLSA):** £{target_income}")
    st.sidebar.header("Retirement Income Goal")
    essential_expenditure = st.sidebar.number_input("Essential Expenditure (£)", min_value=0.0, value=15000.0, step=1000.0)
    discretionary_expenditure = st.sidebar.number_input("Discretionary Expenditure (£)", min_value=0.0, value=5000.0, step=1000.0)
    initial_target_income = essential_expenditure + discretionary_expenditure
    target_income = st.sidebar.number_input(
    "Target Annual Income (£)",
    min_value=initial_target_income,
    value=initial_target_income,
    step=1000.0,
    help="This amount should be at least the sum of your Essential and Discretionary expenditures."
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
    income_start_age = int(income_start_age)
    income_end_age = int(income_end_age)
    # Retirement Income Inputs
    annual_retirement_income = st.sidebar.number_input(
    "Desired Annual Retirement Income (£)",
    min_value=target_income,
    value=target_income,
    step=1000.0,
    help="This should be at least equal to your Target Annual Income."
)

    include_state_pension = st.sidebar.checkbox("Include State Pension", value=True)
    include_db_pension = st.sidebar.checkbox("Include Defined Benefit Pension", value=False)
    db_pension_income = 0
    db_pension_age = retirement_age
    if include_db_pension:
        db_pension_income = st.sidebar.number_input("Annual DB Pension Income (£)", min_value=0, value=10000)
        db_pension_age = st.sidebar.number_input("DB Pension Starting Age", min_value=int(retirement_age), max_value=100, value=int(retirement_age))

    # Tax-Free Cash Options
    if strategy == "Accumulation":
        st.sidebar.header("Tax-Free Cash Options at Retirement")
        tax_free_cash_option = st.sidebar.selectbox("Choose an option:", ["No tax-free cash", "Full tax-free cash", "Partial tax-free cash", "UFPLS"])
        partial_tax_free_cash = 0
        ufpls_amount = 0
        if tax_free_cash_option == "Partial tax-free cash":
            partial_tax_free_cash = st.sidebar.number_input("Specify amount of partial tax-free cash (£)", min_value=0.0, value=0.0)
        elif tax_free_cash_option == "UFPLS":
            ufpls_amount = st.sidebar.number_input("Specify UFPLS amount (£)", min_value=0.0, value=0.0)
    else:
        # For decumulation strategies, handle immediate capital goal
        tax_free_cash_option = "No tax-free cash"
        partial_tax_free_cash = 0
        ufpls_amount = 0

    # Regular Income Options
  #   st.sidebar.header("Regular Income Options")
 #    regular_income_option = st.sidebar.selectbox("Choose an option:", ["Tax-free regular income", "Taxable regular income", "Combination regular income"])
  #   tax_free_income_amount = 0
   #  if regular_income_option == "Tax-free regular income":
    #    tax_free_income_amount = st.sidebar.number_input("Specify annual tax-free income amount (£)", min_value=0.0, value=0.0)

    # Assumptions
    st.sidebar.header("Assumptions")
    investment_growth_rate = st.sidebar.slider("Investment Growth Rate (%)", min_value=0.0, max_value=10.0, value=5.0) / 100
    salary_growth_rate = st.sidebar.slider("Salary Growth Rate (%)", min_value=0.0, max_value=10.0, value=2.0) / 100
    inflation_rate = st.sidebar.slider("Inflation Rate (%)", min_value=0.0, max_value=10.0, value=2.0) / 100

    # Run Projection
    years, uncrystallised_fund_values, crystallised_fund_values, total_fund_values, incomes, taxes, net_incomes, shortfalls = project_pension(
        current_age,
        retirement_age,
        initial_fund,
        monthly_contribution,
        monthly_employer_contribution,
        investment_growth_rate,
        salary_growth_rate,
        inflation_rate,
        target_income,
        annual_retirement_income,
        include_state_pension,
        include_db_pension,
        db_pension_income,
        db_pension_age,
        income_start_age = income_start_age,  # Pass the new parameter
        income_end_age = income_end_age, 
        tax_free_cash_option = tax_free_cash_option,
        partial_tax_free_cash=partial_tax_free_cash,
        ufpls_amount=ufpls_amount,
        strategy=strategy,
        immediate_capital_goal=immediate_capital_goal,
        existing_tfc_withdrawals=existing_tfc_withdrawals,
        max_age=max_age,
        tax_bands=tax_bands,
     
    )

    # Display Results
    display_results(years, uncrystallised_fund_values, crystallised_fund_values, total_fund_values,
                    incomes, taxes, net_incomes, shortfalls, retirement_age, target_income, strategy)

    # Personalized Messaging
    st.header("Personalized Messages and Risk Warnings")
    post_retirement_shortfalls = [s for age, s in zip(years, shortfalls) if age >= retirement_age and s > 0]
    if post_retirement_shortfalls:
        st.warning("**Income Shortfall Detected During Retirement:** You may not meet your desired retirement income based on current projections.")
        st.write("Consider taking the following actions:")
        st.write("- Increase your monthly contributions (if possible).")
        st.write("- Adjust your retirement age.")
        st.write("- Review your investment growth assumptions.")
        st.write("- Adjust your target annual income.")
    else:
        st.success("**On Track:** You're on track to meet your retirement income goals!")

    # Risk Warnings
    st.markdown("""
    ### Important Risk Warnings

    - **Investment Risk:** The value of investments can go down as well as up, and you may get back less than you invested.
    - **Inflation Risk:** Inflation can reduce the real value of your savings and investment returns.
    - **Longevity Risk:** You may live longer than expected, which could result in your funds running out.
    - **Taxation:** Tax rules can change, and the value of any benefits depends on individual circumstances.

    ### Next Steps

    - **Save Your Plan:** You can save your projection for future reference.
    - **Seek Professional Advice:** Consider speaking to a financial advisor for personalized advice.
    - **Contact Us:** If you have any questions, please contact our support team.
    """)

    # Fulfillment Options
    st.header("What Would You Like to Do Next?")
    col1, col2 = st.columns(2)
    with col1:
        save_plan = st.button("Save Plan")
        if save_plan:
            st.success("Your plan has been saved securely.")
    with col2:
        contact_support = st.button("Contact a Retirement Consultant")
        if contact_support:
            st.info("Please call us at **0800 123 4567** or email **support@example.com**.")

if __name__ == "__main__":
    main()
