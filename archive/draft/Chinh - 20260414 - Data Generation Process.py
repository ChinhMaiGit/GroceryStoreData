import marimo

__generated_with = "0.23.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Business Data Generator

    I'm designing a business case for a personal data analytics project and needs your help with the script for generating data. The script should follow the criteria below:
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1 Technical Requirements

    The simulation script is designed to meet the following technical specifications, ensuring reproducibility, transparency, and ease of use:

    1. The script is written entirely in Python.
    2. It is implemented as a Marimo notebook, providing an interactive yet fully executable Python-based environment.
    3. Data generation is performed using either NumPy or PyMC, with PyMC being the preferred library due to its powerful probabilistic modeling capabilities.
    4. Comprehensive documentation is provided directly within the script through inline comments and Markdown cells.
    5. The complete algorithm for data simulation is described explicitly within the notebook.
    6. Where appropriate, a graphical representation (e.g., a flowchart or directed acyclic graph) is included to illustrate the data-generation process.

    These requirements ensure that the notebook serves as a self-contained, professionally documented artifact suitable for both educational and practical business-analytics applications.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2 Purposes

    The primary objective of this simulation is to generate a realistic business dataset that can be used to demonstrate the complete analytics value chain across four progressive layers of analysis. These layers mirror the natural flow of information within a business environment: from raw data collection through analytical processing to the derivation of actionable insights and informed decision-making.

    **Descriptive Analysis**
    The first layer focuses on understanding the current state of the business and includes the following activities:
    1. Data cleaning and manipulation
    2. Feature engineering
    3. Data visualization
    4. Correlation analysis using Bayesian statistical methods (explanatory models)

    **Diagnostic Analysis**
    The second layer investigates underlying causes and relationships:
    5. Causal inference employing Directed Acyclic Graphs (DAGs) within Pearl’s causal framework
    6. Counterfactual analysis

    **Predictive Analysis**
    The third layer focuses on the forecasting problems:
    7. Correlation analysis using machine-learning predictive models

    **Prescriptive Analysis**
    The fourth layer supports decision-making under constraints:
    8. Optimization using linear programming

    Collectively, these analyses address the core business questions that arise in any operational context:

    1. What is the current situation of the business? (Descriptive “IS” question)
    2. What factors tend to occur together in the business? (Correlation questions)
    3. What is the cause of the observed phenomena? (Causal questions)
    4. What is expected to happen in the future based on current patterns and trends? (Predictive questions)
    5. What would have happened if an external intervention—such as engaging a service to boost sales—had been implemented? (Counterfactual questions)
    6. What actions should be taken to maximize revenue under given conditions? (Optimization questions)

    By progressing systematically through these four layers, the simulation illustrates how raw transactional data is transformed into strategic insights that directly support business decisions. This structured approach reinforces the intuitive and practical nature of data analytics while demonstrating its relevance to everyday operational challenges.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3 Philosophy of the Case Design

    The design of this business-case simulation is guided by a clear philosophy. Its primary objective is to present a simple yet meaningful scenario while providing comprehensive explanations that render the material accessible to individuals without a statistical or technical background. Through this approach, the simulation demonstrates three fundamental principles:

    1. Data analytics is not an esoteric or highly advanced discipline reserved for specialists; rather, it comprises systematic practices that are employed daily by businesses of all sizes.
    2. The natural progression of data collection, analytical reasoning, and decision-making that occurs within any business environment.
    3. The core concepts of data analytics are inherently intuitive and accessible, representing structured extensions of everyday business judgment.

    A business frequently originates from a straightforward concept that expands rapidly as the owner confronts practical operational challenges. Consider, for example, an entrepreneur who establishes a small grocery store to generate income for their family. Although the core idea can be expressed in a single sentence, its successful implementation requires the owner to address several essential questions:

    1. Where should the shop be located? (This decision directly determines monthly fixed costs, such as rent.)
    2. What products should the shop offer? (This choice shapes the product portfolio, inventory management, storage requirements, variable costs, and associated optimization challenges.)
    3. How should inventory be replenished, managed, and maintained? (This involves inventory optimization and demand forecasting, drawing on predictive models.)
    4. Which information should be recorded, and in what format? (This supports performance tracking, accounting, and regulatory compliance.)
    5. How much initial capital is available? (This constrains the scale of operations and overall financial planning.)

    These questions, though seemingly elementary, are critical to business viability. Each can be formulated as an optimization, explanatory, or predictive problem. Importantly, such questions often admit straightforward solutions once the business context and underlying drivers are clearly understood.

    Accordingly, this simulation is constructed around the operations of a small neighborhood grocery store that opened one year ago and has been active for the past 12 months. The case illustrates how routine business decisions naturally generate data that can be analyzed to produce actionable insights.

    The analytical process begins with the systematic recording of business activities—specifically, *what* occurred, *where* it occurred, and *when* it occurred. These transactional records constitute the raw data that virtually every business produces. Although voluminous, such data is typically noisy and requires careful processing to extract meaningful insights, accurately reflecting the daily reality faced by business managers, accountants, and analysts.

    To ensure realism, consistency, and analytical value, the data-generation process follows a structured four-step methodology:

    1. Establish a comprehensive business model that defines both deterministic characteristics (location, fixed costs, product portfolio, owner profile, and operational rules) and stochastic factors (weather conditions, random daily events, and macroeconomic influences).
    2. Simulate the evolution of the stochastic factors over the 12-month period.
    3. Model the impact of these stochastic factors on business operations.
    4. Simulate the business’s responses and decision-making processes under the prevailing conditions.

    This rigorous generative approach creates a transparent causal framework. While the true underlying mechanisms are known to the script author, they remain hidden from the analyst. Consequently, the resulting dataset exhibits realistic trends, correlations, and inherent noise, thereby providing an authentic and educationally rich foundation for the subsequent descriptive, diagnostic, and prescriptive analyses.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4 Generation logic

    Step 1: define deterministic characteristics and stochastic factors
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    SCM at $t = 0$:

    Decision variables:
    * $\text{LocationQuality}_t$
    * $\text{SKURestockUnitCount}_{it}$
    * $\text{TotalEmployee}_t$
    * $\text{OperationalHours}_t$
    * $\text{SetupOrRepairCost}_t$

    Variables determined by stochastic factors:
    * $\text{HourlyUtilityRate}_t$
    * $\text{SKUUnitCost}_{it}$
    * $\text{HourlySalaryRate}_t$
    * $\text{UnitStorageCost}_t$

    SCM equations:

    $$
    \begin{align}
        \text{TotalCost}_t &\overset{\leftarrow}{=} \text{FixedCost}_t + \text{VariableCost}_t \\
        \text{FixedCost}_t &\overset{\leftarrow}{=} \text{Rent}_t + \text{SetupOrRepairCost}_t\\
        \text{VariableCost}_t &\overset{\leftarrow}{=} \text{InventoryManagementCost}_t + \text{OverheadCost}_t + \text{Utility}_t\\
        \text{InventoryManagementCost}_t &\overset{\leftarrow}{=} \text{InventoryRestockCost}_t + \text{StorageCost}_t \\
        \text{InventoryRestockCost}_t &\overset{\leftarrow}{=} \sum^N_{i=1} \text{SKURestockUnitCount}_{it} \times \text{SKUUnitCost}_{it} \\
        \text{StorageCost}_t &\overset{\leftarrow}{=} \text{InventoryUnitCount}_t\times\text{UnitStorageCost}_t \\
        \text{InventoryUnitCount}_t &\overset{\leftarrow}{=} \left(\text{InitialInventoryCount}_t + \sum^N_{i=1}\text{SKURestockUnitCount}_{it}\right) \\
        \text{OverheadCost}_t &\overset{\leftarrow}{=} \text{TotalEmployee}_t \times \text{HourlySalaryRate}_t \times \text{OperationalHours}_t\\
        \text{Utility}_t &\overset{\leftarrow}{=} \text{OperationalHours}_t \times \text{HourlyUtilityRate}_t\\
        \text{Rent}_t &\overset{\leftarrow}{=} f(\text{LocationQuality}_t) \\
        \text{OperationalNeeds}_t &\overset{\leftarrow}{=} g(\text{LocationQuality}_t)\\
        \text{MinInventory}_t &\overset{\leftarrow}{=} h(\text{LocationQuality}_t)\\
        \text{SetupOrRepairCost}_t &\overset{\leftarrow}{=} c(\text{LocationQuality}_t)
    \end{align}
    $$

    (the sign $\overset{\leftarrow}{=}$ indicates that the RHS is the cause of the LHS)

    Given at $t=0$:

    $$\text{InitialInventoryCount}_t = 0$$

    Constraints (feasibility and non-negativity rules):

    $$
    \begin{align}
        \text{TotalEmployee}_t &\geq \text{OperationalNeeds}_t \\
        \text{InitialCapital}_t &\geq \text{TotalCost}_t \\
        \text{InventoryUnitCount}_t &\geq \text{MinInventory}_t\\
        \text{LocationQuality}_t &\geq 0 \\
        \text{SKURestockUnitCount}_{it}  &\geq 0 \\
        \text{TotalEmployee}_t  &\geq 0 \\
        \text{OperationalHours}_t  &\geq 0 \\
        \text{SetupOrRepairCost}_t &\geq 0 \\
    \end{align}
    $$

    The causal expression $\text{MinInventory}_t \overset{\leftarrow}{=} h(\text{LocationQuality}_t)$ is a heuristic threshold for determining minimum inventory using the characteristics of the neighborhood. In periods where $t > 0$, this might lead to unoptimal inventory management where the inventory is overstocked due to seasonal changes in actual demand, which leads to higher inventory cost. In the actual analysis of the generated data, the analyst won't know this rule so it opens door for optimization by linear programming.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Details of the Data generation process

    The first steps in the data generation process is to generate data for basic choices that are not determined by market forces. In this case, the neighborhood information (also information of the possible locations for opening the store) and the list of SKUs are such data.

    1. Location and their features

    For each location $l \in L$, generate the following data:
    * $\text{LocationQuality}_l$
    * $\text{Rent}_l \overset{\leftarrow}{=} f(\text{LocationQuality}_l)$
    * $\text{OperationalNeeds}_l \overset{\leftarrow}{=} g(\text{LocationQuality}_l)$
    * $\text{MinInventory}_l \overset{\leftarrow}{=} h(\text{LocationQuality}_l)$
    * $\text{SetupOrRepairCost}_l \overset{\leftarrow}{=} c(\text{LocationQuality}_l)$

    This will create a table for locations and their features. The subscripts of these features are $l$, not $t$. This means they are corresponding features of the location $l$. At each period $t$, a certain location $l$ is chosen, then the features of the location turn to the feature of the period $t$. The change of $l$ at a certain period $t$ means that the owner change the store location in this period.

    In this setup, $\text{MinInventory}_l$ is treated as a given information, at least for now, but I want them to be determined by actual demand force that will be modelled later

    2. SKUs

    Description of the set of SKUs $S$:

    This list is manually crafted in such a way that it reflects a real list of products that a grocery owner could actually choose to buy from different retailers. The list contains a comprehensive product catalog comprising approximately 709 SKUs, systematically organized across 12 major categories and numerous sub-categories. The data includes essential attributes such as:

    * `uid`
    * `name`
    * `brand_level`
    * `category`
    * `product_type`
    * `unit`
    * `weight_g`
    * `retail_base_price_EUR`

    The owner will choose a portfolio of products from this list following his budget constraint and from his perception/expectation/experience/information about the demand of the neighborhood.

    The structure of this list will also affect the $\text{MinInventory}_l$ requirements in the list of neighborhood. Suppose that there are 12 categories of products described in the list of SKUs, then the $\text{MinInventory}_l$ must show the minimum stocks for all of these categories.

    With this, we need to construct the optimization problem (with suboptimal constraints) to illustrate the decision problem that the store owner faces when he has to decide on which products and how many of them he need to stock up.

    For this first iteration of the model, the `retail_base_price_EUR` or the $\text{SKUUnitCost}$ is fixed, but in later iteration, it could also change following some random patterns.

    3. Details of the inventory management problem

    Problem description:

    Given the following information:

    The list of locations $L$ containing information about:
    * $\text{LocationQuality}_l$
    * $\text{MinInventory}_{cl}$
    * $\text{Rent}_l$
    * $\text{OperationalNeeds}_l$
    * $\text{SetupOrRepairCost}_l$

    The list of SKUs $S$ contains information about:
    * $\text{SKUUnitCost}_{scl}$

    Other given info includes:
    * $\text{HourlyUtilityRate}_t$
    * $\text{HourlySalaryRate}_t$
    * $\text{UnitStorageCost}_t$

    Assuming that the $\text{UnitStorageCost}_t$ is universal to all product and only changes through time.

    The owner has to choose the location $l$ and the product portfolio for the stocks. For each SKU $s$ of the category $c$ in the period $t$, the decision variable for whether the owner should buy this SKU and its quantity are respectively $x_{sct}$ and $\text{InventoryUnitCount}_{sct}$ so that the following conditions are satisfied:

    $$
    \begin{align}
        \text{TotalEmployee}_t &\geq \text{OperationalNeeds}_t \\
        \text{InitialCapital}_t &\geq \text{TotalCost}_t \\
        \sum_{s}\text{InventoryUnitCount}_{sct} &\geq \text{MinInventory}_{ct}\\
    \end{align}
    $$

    (It should be noted that for the period $t$, if the location $l$ is chosen, on the subscript $l$ is changed to $t$, reflecting the fact that the characteristics of the period $t$ is partially chosen by the owner )

    Afterwards, he needs to decide the markup charged on all the products to deduce the shelf prices.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Formulation of the Owner’s Full Decision Problem as a Linear/Mixed-Integer Linear Program (MILP)**

    The resulting model is a **Mixed-Integer Linear Program (MILP)** because binary variables are required for location choice and (optionally) SKU selection.

    The formulation is designed for direct implementation in PuLP (or SciPy) inside the Marimo notebook. For the first iteration I keep the model tractable while preserving realism; later iterations can add stochastic demand feedback and dynamic relocation.

    ### Indices and Sets
    - \( l \in L \): possible store locations (small finite set, e.g., 5–10)
    - \( c \in C \): product categories (exactly 12, derived from the SKU Excel file)
    - \( s \in S_c \): SKUs belonging to category \( c \) (≈709 total SKUs)

    ### Parameters (Given at Each \( t \))
    - Location table: \(\text{LocationQuality}_l\), \(\text{Rent}_l\), \(\text{OperationalNeeds}_l\), \(\text{MinInventory}_{c l}\), \(\text{SetupOrRepairCost}_l\) for every \( l \)
    - SKU table: \(\text{SKUUnitCost}_s\) (initially fixed from `retail_base_price_EUR`; later stochastic)
    - Exogenous rates: \(\text{HourlyUtilityRate}_t\), \(\text{HourlySalaryRate}_t\), \(\text{UnitStorageCost}_t\) (universal across products)
    - \(\text{InitialInventoryCount}_t\) (carry-over from previous period; = 0 at \( t = 0 \))
    - \(\text{InitialCapital}_t\)

    ### Decision Variables
    - \( y_l \in \{0,1\} \): 1 if location \( l \) is selected at period \( t \)
      (constraint: \(\sum_{l \in L} y_l = 1\))
    - \( x_{s t} \in \{0,1\} \): 1 if SKU \( s \) is stocked at period \( t \)
    - \( q_{s t} \geq 0 \): \(\text{SKURestockUnitCount}_{s t}\) (units of SKU \( s \) to restock)
    - \(\text{TotalEmployee}_t \geq 0\)
    - \(\text{OperationalHours}_t \geq 0\)

    ### Derived (Auxiliary) Expressions – All Linear
    \[
    \begin{align*}
    \text{LocationQuality}_t &= \sum_l y_l \cdot \text{LocationQuality}_l \\
    \text{Rent}_t &= \sum_l y_l \cdot \text{Rent}_l \\
    \text{OperationalNeeds}_t &= \sum_l y_l \cdot \text{OperationalNeeds}_l \\
    \text{MinInventory}_{c t} &= \sum_l y_l \cdot \text{MinInventory}_{c l} \\
    \text{SetupOrRepairCost}_t &= \sum_l y_l \cdot \text{SetupOrRepairCost}_l \\
    \text{InventoryRestockCost}_t &= \sum_s q_{s t} \cdot \text{SKUUnitCost}_s \\
    \text{InventoryUnitCount}_t &= \text{InitialInventoryCount}_t + \sum_s q_{s t} \\
    \text{StorageCost}_t &= \text{InventoryUnitCount}_t \cdot \text{UnitStorageCost}_t \\
    \text{InventoryManagementCost}_t &= \text{InventoryRestockCost}_t + \text{StorageCost}_t \\
    \text{OverheadCost}_t &= \text{TotalEmployee}_t \cdot \text{HourlySalaryRate}_t \cdot \text{OperationalHours}_t \\
    \text{Utility}_t &= \text{OperationalHours}_t \cdot \text{HourlyUtilityRate}_t \\
    \text{VariableCost}_t &= \text{InventoryManagementCost}_t + \text{OverheadCost}_t + \text{Utility}_t \\
    \text{FixedCost}_t &= \text{Rent}_t + \text{SetupOrRepairCost}_t \\
    \text{TotalCost}_t &= \text{FixedCost}_t + \text{VariableCost}_t
    \end{align*}
    \]

    All the above are linear (or can be declared as linear expressions in PuLP), exactly reproducing the SCM you supplied.

    ### Constraints (Feasibility Rules)
    1. Location uniqueness: \(\sum_l y_l = 1\)
    2. Staffing requirement: \(\text{TotalEmployee}_t \geq \text{OperationalNeeds}_t\)
    3. Capital sufficiency: \(\text{InitialCapital}_t \geq \text{TotalCost}_t\)
    4. Category-level minimum inventory (per the user’s section 3):
       \[
       \forall c \in C: \quad \sum_{s \in S_c} q_{s t} \geq \text{MinInventory}_{c t}
       \]
    5. SKU selection linkage (big-M formulation, \( M \) = a large constant, e.g. 10 000):
       \[
       \forall s: \quad q_{s t} \leq M \cdot x_{s t}
       \]
       (ensures that if a SKU is not selected, its restock quantity is zero)
    6. Non-negativity: \( y_l \in \{0,1\} \), \( x_{s t} \in \{0,1\} \), \( q_{s t} \geq 0 \), \(\text{TotalEmployee}_t \geq 0 \), \(\text{OperationalHours}_t \geq 0 \)

    ### Objective Function (Proposed for First Iteration)
    Because the SCM is cost-centric and demand-side information is not yet available, the natural objective for the initial generative step is **cost minimization** while satisfying all operational minimums:

    \[
    \min \quad \text{TotalCost}_t
    \]

    This yields a feasible, realistic baseline inventory plan. Suboptimality (the behavioral realism you require) can be introduced in one of two transparent ways inside the notebook:
    - Add a small positive “behavioral slack” term to the objective (e.g., \(\min \text{TotalCost}_t + \epsilon \cdot \sum_s q_{s t}\) with \(\epsilon > 0\)), or
    - Solve the LP, then perturb the obtained quantities by a small random factor drawn from a PyMC distribution (documented as the owner’s “bounded rationality”).

    ### Markup Decision (Post-LP Step)
    After the LP is solved and the chosen quantities \( q_{s t}^* \) and location are known, the owner sets shelf prices via a simple multiplicative markup rule (separate from the LP, as it does not affect the cost side):

    \[
    \text{ShelfPrice}_{s t} = \text{SKUUnitCost}_s \times (1 + \text{Markup}_{s t})
    \]

    where \(\text{Markup}_{s t}\) can be a category-specific constant (e.g., 0.25–0.60) or another lightweight optimization. This completes the supply-side generation for period \( t \).

    ### Practical Implementation Notes for the Marimo Notebook
    - The MILP is small (≈10 locations + 709 SKUs × 2 binaries) and solves in seconds with PuLP + CBC solver.
    - Category-level aggregation can be added later for even faster runs if needed.
    - All parameters (\( f, g, h, c \), rates, capital) will be exposed as interactive widgets.
    - The notebook will contain: (1) Markdown description of the full algorithm, (2) the exact LP code block, (3) a NetworkX DAG visualization of the SCM, and (4) seeded random generation for reproducibility.

    This formulation fully satisfies the requirements of section 3, integrates every equation from the SCM you copied, and produces the raw transactional data (chosen location, restocked quantities, total costs, etc.) required for the four analytics layers. It is ready for immediate coding.

    If the objective, big-M formulation, or any constraint needs adjustment before implementation, please specify; otherwise I will proceed to generate the complete Marimo notebook skeleton incorporating this exact MILP.
    """)
    return


if __name__ == "__main__":
    app.run()
