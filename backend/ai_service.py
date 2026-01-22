import json
from groq import Groq
from config import get_settings
from typing import Dict, List

settings = get_settings()
client = Groq(api_key=settings.GROQ_API_KEY)

def generate_budget_plan(income: float, target_savings: float, past_expenses: Dict = None, loan_commitments: float = 0) -> List[Dict]:
    import logging
    logger = logging.getLogger(__name__)
    
    # HARD CONSTRAINT: total_budget <= monthly_income
    # spendable_amount = monthly_income - savings_goal - loan_commitments
    spendable_amount = income - target_savings - loan_commitments
    
    if spendable_amount <= 0:
        logger.warning(f"Spendable amount is {spendable_amount}. Income: {income}, Savings: {target_savings}, Loans: {loan_commitments}")
        return []
    
    # Define priority-based allocation percentages
    priority_allocation = {
        "Rent": {"priority": 1, "min": 0.25, "max": 0.35},
        "Food": {"priority": 1, "min": 0.15, "max": 0.25},
        "Bills": {"priority": 1, "min": 0.10, "max": 0.15},
        "Transport": {"priority": 2, "min": 0.08, "max": 0.12},
        "Healthcare": {"priority": 1, "min": 0.05, "max": 0.10},
        "Education": {"priority": 2, "min": 0.05, "max": 0.15},
        "Shopping": {"priority": 3, "min": 0.05, "max": 0.10},
        "Entertainment": {"priority": 3, "min": 0.03, "max": 0.08},
        "Other": {"priority": 3, "min": 0.02, "max": 0.05}
    }
    
    budget_categories = []
    total_allocated = 0
    
    # Allocate based on priority and past spending patterns
    for category, config in priority_allocation.items():
        if past_expenses and category in past_expenses:
            # Use past spending as a guide
            past_amount = past_expenses[category]
            past_percent = past_amount / spendable_amount if spendable_amount > 0 else 0
            # Cap it within min/max range
            allocated_percent = max(config["min"], min(past_percent, config["max"]))
        else:
            # Use average of min/max for new categories
            allocated_percent = (config["min"] + config["max"]) / 2
            
        allocated_amount = spendable_amount * allocated_percent
        budget_categories.append({
            "category": category,
            "allocated_amount": round(allocated_amount, 2)
        })
        total_allocated += allocated_amount
    
    # MANDATORY: Adjust if total exceeds spendable amount
    if total_allocated > spendable_amount:
        logger.info(f"Adjusting budget: {total_allocated} > {spendable_amount}")
        adjustment_factor = spendable_amount / total_allocated
        for cat in budget_categories:
            cat["allocated_amount"] = round(cat["allocated_amount"] * adjustment_factor, 2)
        total_allocated = sum(cat["allocated_amount"] for cat in budget_categories)
    
    # VALIDATION: Ensure total never exceeds spendable amount
    final_total = sum(cat["allocated_amount"] for cat in budget_categories)
    if final_total > spendable_amount:
        logger.error(f"Budget validation failed: {final_total} > {spendable_amount}")
        # Force proportional reduction
        reduction_factor = spendable_amount / final_total
        for cat in budget_categories:
            cat["allocated_amount"] = round(cat["allocated_amount"] * reduction_factor, 2)
    
    logger.info(f"Budget generated: Total={sum(cat['allocated_amount'] for cat in budget_categories)}, Spendable={spendable_amount}")
    return budget_categories

def rule_based_anomaly_detection(
    income: float,
    monthly_limit: float,
    target_savings: float,
    current_expenses: Dict[str, float],
    budget_allocations: Dict[str, float],
    last_month_expenses: Dict[str, float]
) -> List[Dict]:
    """Fallback rule-based anomaly detection when Groq API fails"""
    import logging
    logger = logging.getLogger(__name__)
    
    anomalies = []
    detected_categories = set()  # Track to avoid duplicates
    
    # RULE 1: Category overspending (current > allocated budget)
    for category, current_amount in current_expenses.items():
        if category in budget_allocations:
            allocated = budget_allocations[category]
            if current_amount > allocated:
                overspend = current_amount - allocated
                reduction_amount = overspend
                anomalies.append({
                    "category": category,
                    "issue": f"{category} spending exceeded budget by ₹{overspend:.2f}",
                    "impact_amount": overspend,
                    "recommendation": f"Reduce {category} spending by ₹{reduction_amount:.2f} to stay within ₹{allocated:.2f} budget"
                })
                detected_categories.add(category)
    
    # RULE 2: Expense spike > 30% compared to last month
    for category, current_amount in current_expenses.items():
        if category in last_month_expenses and category not in detected_categories:
            last_amount = last_month_expenses[category]
            if last_amount > 0:
                increase_percent = ((current_amount - last_amount) / last_amount) * 100
                if increase_percent > 30:
                    increase_amount = current_amount - last_amount
                    anomalies.append({
                        "category": category,
                        "issue": f"{category} spending increased by {increase_percent:.1f}% compared to last month",
                        "impact_amount": increase_amount,
                        "recommendation": f"Review {category} expenses and reduce by ₹{increase_amount:.2f} to match last month's spending"
                    })
                    detected_categories.add(category)
    
    # RULE 3: Single transaction > 2× average transaction amount
    if current_expenses:
        total_current = sum(current_expenses.values())
        num_categories = len(current_expenses)
        average_per_category = total_current / num_categories if num_categories > 0 else 0
        
        for category, amount in current_expenses.items():
            if category not in detected_categories and average_per_category > 0:
                if amount > (average_per_category * 2):
                    excess = amount - average_per_category
                    anomalies.append({
                        "category": category,
                        "issue": f"Unusually large {category} expense of ₹{amount:.2f} detected (2× average)",
                        "impact_amount": excess,
                        "recommendation": f"Verify if this {category} expense was necessary. Consider spreading large expenses across months"
                    })
                    detected_categories.add(category)
    
    # RULE 4: Total expenses exceed monthly limit (risk to savings)
    total_current = sum(current_expenses.values())
    if total_current > monthly_limit:
        excess = total_current - monthly_limit
        anomalies.append({
            "category": "Overall Budget",
            "issue": f"Total expenses exceeded monthly limit by ₹{excess:.2f}",
            "impact_amount": excess,
            "recommendation": f"Reduce discretionary spending by ₹{excess:.2f} to meet your savings goal of ₹{target_savings:.2f}"
        })
    
    # RULE 5: Approaching monthly limit (>90% of limit)
    elif total_current > (monthly_limit * 0.9) and total_current <= monthly_limit:
        remaining = monthly_limit - total_current
        anomalies.append({
            "category": "Overall Budget",
            "issue": f"You've used {(total_current/monthly_limit*100):.1f}% of your monthly budget",
            "impact_amount": total_current,
            "recommendation": f"Only ₹{remaining:.2f} remaining. Monitor spending carefully to avoid exceeding your limit"
        })
    
    logger.info(f"Rule-based detection found {len(anomalies)} anomalies with recommendations")
    return anomalies

def detect_anomalies(
    income: float,
    monthly_limit: float,
    target_savings: float,
    current_expenses: Dict[str, float],
    budget_allocations: Dict[str, float],
    last_month_expenses: Dict[str, float]
) -> List[Dict]:
    import logging
    logger = logging.getLogger(__name__)
    
    prompt = f"""You are a personal finance AI assistant specialized in anomaly detection.

Analyze the following financial data and detect anomalies:

Monthly Income: ₹{income}
Monthly Expense Limit: ₹{monthly_limit}
Target Savings: ₹{target_savings}

Budget Allocations:
{json.dumps(budget_allocations, indent=2)}

Current Month Expenses by Category:
{json.dumps(current_expenses, indent=2)}

Last Month Expenses by Category:
{json.dumps(last_month_expenses, indent=2)}

Detect anomalies based on:
1. Category overspending (current > allocated)
2. Significant increase vs last month (>30% increase)
3. Risk to savings goal (total expenses approaching limit)

For each anomaly found, provide:
- category: The spending category
- issue: Clear description of the problem
- impact_amount: Dollar amount of the issue
- recommendation: Specific, actionable recommendation

Return ONLY a JSON array with this structure:
[
  {{
    "category": "Food",
    "issue": "Food spending exceeded budget by ₹150",
    "impact_amount": 150,
    "recommendation": "Reduce dining out to 2 times per week and meal prep at home to save ₹150/month"
  }}
]

If no anomalies are detected, return an empty array: []

Return only the JSON array, no other text."""

    try:
        logger.info("Attempting Groq API anomaly detection")
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a financial anomaly detection AI. Always return valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama3-8b-8192",
            temperature=0.3,
            max_tokens=2000,
        )
        
        response_text = chat_completion.choices[0].message.content.strip()
        
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        anomalies = json.loads(response_text)
        logger.info(f"Groq API detected {len(anomalies)} anomalies")
        return anomalies
    except Exception as e:
        logger.error(f"Groq API failed: {str(e)}. Falling back to rule-based detection")
        return rule_based_anomaly_detection(
            income, monthly_limit, target_savings,
            current_expenses, budget_allocations, last_month_expenses
        )

def get_financial_recommendations(
    income: float,
    total_expenses: float,
    savings: float,
    target_savings: float,
    anomaly_count: int
) -> str:
    
    prompt = f"""You are a personal finance AI assistant.

Provide personalized financial recommendations based on:
- Monthly Income: ${income}
- Total Expenses: ${total_expenses}
- Current Savings: ${savings}
- Target Savings: ${target_savings}
- Number of Anomalies Detected: {anomaly_count}

Provide 3-5 specific, actionable recommendations to improve financial health.
Focus on practical steps the user can take immediately.

Return your response as plain text, not JSON."""

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful financial advisor providing practical advice."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama3-8b-8192",
            temperature=0.5,
            max_tokens=1000,
        )
        
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        return "Unable to generate recommendations at this time. Please try again later."
