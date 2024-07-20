from openai import OpenAI
from django.conf import settings
import json


def fetch_expense(transactions, categories):
    expenses = {}
    category_names = []

    # Populate the expenses dictionary
    for item in transactions:
        expenses[item.pk] = item.description

    # Collect category names using list comprehension
    category_names = [category.name for category in categories]

    ai_result = ai_categorization(expenses, category_names)
    print("AI Response: ", ai_result)

    if ai_result is None:
        print("AI categorization returned None")
        return {}

    try:
        # Attempt to parse the JSON string to a dictionary
        result_dict = json.loads(ai_result)
        return result_dict

    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON: {e}")
        return {}


def ai_categorization(expenses, categories):
    # Format expenses and categories as JSON strings

    system_prompt = """
    You are an accountant assistant that will categorize 
    expense items based on its descriptions. 
    You must use the given categories and you must return
    only a JSON of 'transaction_id': 'category'.
    """
    user_prompt = f"""
    Expenses: {expenses}
    Categories: {categories}
    """
    try:
        openai_api_key = settings.OPENAI_API_KEY
        client = OpenAI(api_key=openai_api_key)

        response = client.chat.completions.create(
            model="gpt-4-turbo",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {"role": "user", "content": user_prompt},
            ],
        )

        return response.choices[0].message.content
    except Exception as e:
        return f"An error occurred: {e}"
