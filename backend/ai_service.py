import json
from groq import Groq
from config import get_settings
from typing import Dict, List

settings = get_settings()
client = Groq(api_key=settings.GROQ_API_KEY)

def _rule_based_budget(income: float, target_savings: float, loan_commitments: float, past_expenses: Dict) -> List[Dict]:
    """Fallback rule-based budget allocation when Groq API is unavailable."""
    import logging
    logger = logging.getLogger(__name__)

    spendable_amount = income - target_savings - loan_commitments
    if spendable_amount <= 0:
        return []

    priority_allocation = {
        "Rent":          {"min": 0.25, "max": 0.35},
        "Food":          {"min": 0.15, "max": 0.25},
        "Bills":         {"min": 0.10, "max": 0.15},
        "Transport":     {"min": 0.08, "max": 0.12},
        "Healthcare":    {"min": 0.05, "max": 0.10},
        "Education":     {"min": 0.05, "max": 0.15},
        "Shopping":      {"min": 0.05, "max": 0.10},
        "Entertainment": {"min": 0.03, "max": 0.08},
        "Other":         {"min": 0.02, "max": 0.05},
    }

    budget_categories = []
    for category, config in priority_allocation.items():
        if past_expenses and category in past_expenses:
            past_percent = past_expenses[category] / spendable_amount
            allocated_percent = max(config["min"], min(past_percent, config["max"]))
        else:
            allocated_percent = (config["min"] + config["max"]) / 2
        budget_categories.append({
            "category": category,
            "allocated_amount": round(spendable_amount * allocated_percent, 2)
        })

    total = sum(c["allocated_amount"] for c in budget_categories)
    if total > spendable_amount:
        factor = spendable_amount / total
        for c in budget_categories:
            c["allocated_amount"] = round(c["allocated_amount"] * factor, 2)

    logger.info(f"Rule-based budget: total={sum(c['allocated_amount'] for c in budget_categories)}, spendable={spendable_amount}")
    return budget_categories


def generate_budget_plan(income: float, target_savings: float, past_expenses: Dict = None, loan_commitments: float = 0) -> List[Dict]:
    import logging
    logger = logging.getLogger(__name__)

    spendable_amount = income - target_savings - loan_commitments
    if spendable_amount <= 0:
        logger.warning(f"Spendable amount is {spendable_amount}. Income: {income}, Savings: {target_savings}, Loans: {loan_commitments}")
        return []

    past_expenses_str = json.dumps(past_expenses, indent=2) if past_expenses else "{}"

    prompt = f"""You are an expert personal finance AI. Create a smart monthly budget plan.

Financial Details:
- Monthly Income: ₹{income:.2f}
- Target Monthly Savings: ₹{target_savings:.2f}
- Loan/EMI Commitments: ₹{loan_commitments:.2f}
- Available to Spend (Income - Savings - Loans): ₹{spendable_amount:.2f}

Past Spending Patterns (use this to personalise allocations):
{past_expenses_str}

Rules:
1. Total of all allocated_amount values MUST equal exactly ₹{spendable_amount:.2f}
2. Allocate across these categories: Rent, Food, Bills, Transport, Healthcare, Education, Shopping, Entertainment, Other
3. Prioritise essential categories (Rent, Food, Bills, Healthcare) over discretionary ones
4. If past spending data exists, use it to guide allocations (don't deviate more than 20%)
5. Every category must have allocated_amount > 0

Return ONLY a valid JSON array, no explanation, no markdown:
[
  {{"category": "Rent", "allocated_amount": 5000.00}},
  {{"category": "Food", "allocated_amount": 3000.00}}
]"""

    try:
        logger.info("Calling Groq AI for budget generation")
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a financial planning AI. Return only valid JSON arrays."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama3-8b-8192",
            temperature=0.2,
            max_tokens=1000,
        )

        response_text = chat_completion.choices[0].message.content.strip()

        # Strip markdown fences if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        budget_categories = json.loads(response_text)

        # Validate structure
        if not isinstance(budget_categories, list) or not all(
            "category" in c and "allocated_amount" in c for c in budget_categories
        ):
            raise ValueError("Invalid response structure from Groq")

        # Normalise total to exactly spendable_amount
        total = sum(float(c["allocated_amount"]) for c in budget_categories)
        if total > 0 and abs(total - spendable_amount) > 1:
            factor = spendable_amount / total
            for c in budget_categories:
                c["allocated_amount"] = round(float(c["allocated_amount"]) * factor, 2)

        logger.info(f"Groq AI budget generated: {len(budget_categories)} categories, total=₹{sum(c['allocated_amount'] for c in budget_categories):.2f}")
        return budget_categories

    except Exception as e:
        logger.error(f"Groq API budget generation failed: {str(e)}. Using rule-based fallback.")
        return _rule_based_budget(income, target_savings, loan_commitments, past_expenses)

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

def generate_ai_recommendations(
    income: float,
    current_month_expenses: Dict[str, float],
    last_month_expenses: Dict[str, float],
    budget_allocations: Dict[str, float],
    total_expenses: float,
) -> List[Dict]:
    """Call Groq AI to generate specific, practical recommendations per category."""
    import logging
    logger = logging.getLogger(__name__)

    # Build overrun list for the prompt
    overruns = []
    for category, spent in current_month_expenses.items():
        allocated = budget_allocations.get(category, 0)
        if allocated > 0 and spent > allocated:
            overruns.append({
                "category": category,
                "allocated": round(allocated, 2),
                "spent": round(spent, 2),
                "exceeded_by": round(spent - allocated, 2)
            })

    # Month-over-month changes
    mom_changes = []
    for category, spent in current_month_expenses.items():
        last = last_month_expenses.get(category, 0)
        if last > 0:
            change_pct = ((spent - last) / last) * 100
            if change_pct > 20:
                mom_changes.append({"category": category, "increase_pct": round(change_pct, 1)})

    prompt = f"""You are a personal finance advisor for an Indian user. Analyse their spending and give specific, practical recommendations.

Monthly Income: ₹{income:.2f}
Total Expenses This Month: ₹{total_expenses:.2f}

Categories where budget was EXCEEDED this month:
{json.dumps(overruns, indent=2) if overruns else "None"}

Categories with >20% increase vs last month:
{json.dumps(mom_changes, indent=2) if mom_changes else "None"}

Current month spending by category:
{json.dumps(current_month_expenses, indent=2)}

Rules for your response:
1. For EACH exceeded category, give a specific practical tip to reduce that exact category's spending.
   Examples:
   - Entertainment exceeded → "Switch to free streaming (YouTube, MX Player) instead of paid subscriptions. Play offline games or visit free public parks."
   - Food exceeded → "Meal prep on Sundays to avoid ordering food. Cook at home 5 days a week and limit restaurant visits to weekends."
   - Shopping exceeded → "Uninstall shopping apps for 2 weeks. Use a 48-hour rule before buying anything above ₹500."
   - Transport exceeded → "Use public transport or carpool 3 days a week. Combine errands into single trips."
   - Bills exceeded → "Switch off appliances at the plug. Use fans instead of AC for 2 hours daily."
2. Also include 1-2 general positive recommendations (savings, investment).
3. Each recommendation must have: category (string), message (specific actionable tip), type ("warning"/"success"/"info")
4. Return ONLY a valid JSON array, no markdown, no explanation.

Return format:
[
  {{"category": "Entertainment", "message": "Your entertainment spend exceeded budget by ₹X. Switch to free streaming platforms like YouTube and MX Player. Play offline games or visit free public parks on weekends.", "type": "warning"}},
  {{"category": "Savings Tip", "message": "You can save ₹X by reducing discretionary spending. Set up an auto-transfer to savings on salary day.", "type": "success"}}
]"""

    try:
        logger.info("Calling Groq AI for personalised recommendations")
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a practical personal finance advisor for India. Always return valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama3-8b-8192",
            temperature=0.4,
            max_tokens=1500,
        )

        response_text = chat_completion.choices[0].message.content.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        result = json.loads(response_text)
        if isinstance(result, list) and all("category" in r and "message" in r for r in result):
            logger.info(f"Groq AI generated {len(result)} recommendations")
            return result
        raise ValueError("Invalid structure")

    except Exception as e:
        logger.error(f"Groq recommendations failed: {str(e)}. Using rule-based fallback.")
        # Rule-based fallback with practical tips
        recs = []
        category_tips = {
            "Entertainment": "Switch to free streaming (YouTube, MX Player). Play offline games or visit free public parks.",
            "Food": "Meal prep on Sundays to avoid ordering food. Cook at home 5 days a week.",
            "Shopping": "Use a 48-hour rule before buying anything above ₹500. Uninstall shopping apps temporarily.",
            "Transport": "Use public transport or carpool 3 days a week. Combine errands into single trips.",
            "Bills": "Switch off appliances at the plug. Use fans instead of AC for a few hours daily.",
            "Healthcare": "Use generic medicines and government hospitals for routine checkups.",
            "Education": "Use free resources like YouTube, Coursera free tier, or library books.",
            "Rent": "Consider splitting rent with a flatmate or negotiating with your landlord.",
            "Other": "Review miscellaneous expenses and categorise them to identify where to cut.",
        }
        for overrun in overruns:
            cat = overrun["category"]
            tip = category_tips.get(cat, f"Review your {cat} spending and identify non-essential items to cut.")
            recs.append({
                "category": f"{cat} Budget Alert",
                "message": f"You exceeded your {cat} budget by ₹{overrun['exceeded_by']:.2f}. {tip}",
                "type": "warning"
            })
        for change in mom_changes:
            cat = change["category"]
            tip = category_tips.get(cat, f"Your {cat} spending rose sharply.")
            recs.append({
                "category": f"{cat} Spike",
                "message": f"{cat} spending increased {change['increase_pct']:.1f}% vs last month. {tip}",
                "type": "warning"
            })
        if total_expenses > 0:
            recs.append({
                "category": "Savings Opportunity",
                "message": f"Reducing expenses by 10% saves ₹{total_expenses * 0.1:.2f}/month — ₹{total_expenses * 1.2:.2f} annually. Set up an auto-transfer to savings on salary day.",
                "type": "success"
            })
        if not recs:
            recs.append({
                "category": "Financial Health",
                "message": "Your spending looks on track. Keep monitoring category budgets to maintain this.",
                "type": "success"
            })
        return recs


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
