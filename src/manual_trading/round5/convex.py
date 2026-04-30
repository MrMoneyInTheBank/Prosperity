import numpy as np
import cvxpy as cp

products = [
    "Thermalite Core",
    "Magma Ink",
    "Volcanic Incense",
    "Sulfur Reactor",
    "Scoria Paste",
    "Lava Cake",
    "Pyroflex Cells",
    "Obsidian Cutlery",
    "Ashes of Phoenix",
]

returns = np.array([0.30, 0.25, 0.15, 0.15, 0.05, -0.60, -0.40, -0.10, -0.05])

TOTAL_BUDGET = 1_000_000

# ============================================================================
# STEP 1: Continuous relaxation using cvxpy
# ============================================================================
# Problem: maximize (TOTAL_BUDGET * sum(r_i * π_i / 100)) - (TOTAL_BUDGET * sum((π_i / 100)^2))
# Which simplifies to: maximize sum(r_i * π_i) - (1/100) * sum(π_i^2)
#
# With constraint: sum(π_i) = 100
# And bounds: -25 ≤ π_i ≤ 25

pi_cont = cp.Variable(9)

# Objective: maximize expected return minus fees
# Returns contribution: TOTAL_BUDGET * sum(r_i * π_i / 100) = 10000 * sum(r_i * π_i)
# Fee contribution: TOTAL_BUDGET * sum((π_i / 100)^2) = 100 * sum(π_i^2)
objective = cp.Maximize(10000 * returns @ pi_cont - 100 * cp.sum_squares(pi_cont))

constraints = [
    cp.norm(pi_cont, 1) <= 100,  # Sum of |π_i| ≤ 100 (total absolute allocation)
    pi_cont >= -25,  # Max short 25%
    pi_cont <= 25,  # Max long 25%
]

problem = cp.Problem(objective, constraints)
problem.solve(solver=cp.SCS, verbose=False)

print("=" * 80)
print("CONTINUOUS RELAXATION (no integer constraint)")
print("=" * 80)
print("\nOptimal Allocations (continuous):")
for i in range(9):
    print(f"{products[i]:25} | {pi_cont.value[i]:8.4f}%")

cont_returns = TOTAL_BUDGET * (returns @ (pi_cont.value / 100))
cont_fees = TOTAL_BUDGET * np.sum((pi_cont.value / 100) ** 2)
cont_profit = cont_returns - cont_fees

print(f"\n{'-' * 80}")
print(f"Expected Returns (continuous): ${cont_returns:,.2f}")
print(f"Total Fees (continuous):       ${cont_fees:,.2f}")
print(f"Net Profit (continuous):       ${cont_profit:,.2f}")
print("=" * 80)

# ============================================================================
# STEP 2: Generate Mathematica command for exact integer solution
# ============================================================================
print("\n\nMATHEMATICA INTEGER OPTIMIZATION")
print("=" * 80)

# Build Mathematica command string
mathematica_terms = []
for i in range(9):
    term = f"({returns[i]:.6f})*p{i + 1}*10000-100*(p{i + 1})^2"
    mathematica_terms.append(term)

objective_str = " + ".join(mathematica_terms)
constraint_str = " + ".join([f"Abs[p{i + 1}]" for i in range(9)]) + " <= 100,"
integer_str = ", ".join([f"Element[p{i + 1}, Integers]" for i in range(9)])
vars_str = ", ".join([f"p{i + 1}" for i in range(9)])

mathematica_command = (
    f"NMaximize[{{{objective_str},{constraint_str}{integer_str}}}, {{{vars_str}}}]"
)

print("\nMathematica NMaximize command:")
print(mathematica_command)
print("\n" + "=" * 80)

# ============================================================================
# STEP 2b: Greedy rounding as fallback
# ============================================================================
print("\nGREEDY ROUNDING APPROACH (Fallback if Mathematica unavailable)")
print("=" * 80)

# Round continuous solution to nearest integer
pi_greedy = np.round(pi_cont.value).astype(int)

# Clip to bounds
pi_greedy = np.clip(pi_greedy, -25, 25)

# Check L1 constraint
l1_sum = np.sum(np.abs(pi_greedy))
print(f"\nInitial L1 norm: {l1_sum}")

# If L1 sum exceeds 100, trim from lowest conviction positions
if l1_sum > 100:
    print(f"Over budget by {l1_sum - 100}, trimming...")
    # Find positions to trim (prioritize low-conviction or negative-return positions)
    to_trim = l1_sum - 100
    trim_order = np.argsort(returns)  # Low returns first

    for idx in trim_order:
        if to_trim <= 0:
            break
        if pi_greedy[idx] != 0:
            trim_amount = min(abs(pi_greedy[idx]), to_trim)
            if pi_greedy[idx] > 0:
                pi_greedy[idx] -= trim_amount
            else:
                pi_greedy[idx] += trim_amount
            to_trim -= trim_amount

print(f"Final L1 norm: {np.sum(np.abs(pi_greedy))}")

print("\nGreedy Rounded Allocations:")
for i in range(9):
    side = "LONG" if pi_greedy[i] > 0 else ("SHORT" if pi_greedy[i] < 0 else "NONE")
    print(f"{products[i]:25} | {pi_greedy[i]:3d}% | {side}")

greedy_returns = TOTAL_BUDGET * (returns @ (pi_greedy / 100))
greedy_fees = TOTAL_BUDGET * np.sum((pi_greedy / 100) ** 2)
greedy_profit = greedy_returns - greedy_fees

print(f"\n{'-' * 80}")
print(f"Sum of |allocations|: {np.sum(np.abs(pi_greedy))}%")
print(f"Expected Returns: ${greedy_returns:,.2f}")
print(f"Total Fees:       ${greedy_fees:,.2f}")
print(f"Net Profit:       ${greedy_profit:,.2f}")
print("=" * 80)
