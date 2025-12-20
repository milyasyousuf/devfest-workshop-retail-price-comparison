import os
import json
from dotenv import load_dotenv
import google.generativeai as genai



load_dotenv()
API_KEY = os.getenv('GEMINI_API_KEY')

base_path = "/Users/mi/Desktop/Projects/Gemini/data"
files = os.listdir(base_path)


genai.configure(api_key=API_KEY)

def analyze_single_spec(pdf_path: str) -> dict:
    print(f"\n Analyzing: {pdf_path}")

    try:
        # Upload PDF directly by path
        file = genai.upload_file(
            path=pdf_path,
            mime_type="application/pdf"
        )

        model = genai.GenerativeModel("gemini-2.0-flash")

        response = model.generate_content([
            """Extract these fields from the PDF and return ONLY valid JSON:
            {
                "product_name": "...",
                "processor": "...",
                "ram": "...",
                "storage": "...",
                "price": (number only),
                "battery": "...",
                "weight": "..."
            }""",
            file
        ])

        clean_text = response.text.strip().strip("```json").strip("```")
        result = json.loads(clean_text)

        print(f"Extracted: {result.get('product_name')}")

        # Cleanup uploaded file
        try:
            genai.delete_file(file.name)
        except:
            pass

        return result

    except Exception as e:
        print(f"Error: {str(e)}")
        return {}

def compare_products(specs_list: list):
    """
    Create simple comparison table
    """
    print("\n" + "="*80)
    print("PRICE COMPARISON TABLE")
    print("="*80)
    
    # Header
    products = [s.get('product_name', 'Unknown') for s in specs_list]
    print(f"{'Specification':<20} {products[0]:<20} {products[1]:<20} {products[2]:<20}")
    print("-"*80)
    
    # Rows
    fields = ['processor', 'ram', 'storage', 'battery', 'weight', 'price']
    for field in fields:
        row = f"{field.title():<20}"
        for specs in specs_list:
            value = specs.get(field, 'N/A')
            row += f" {str(value):<20}"
        print(row)
    
    # Winner
    print("\n" + "="*80)
    prices = [(s['product_name'], s['price']) for s in specs_list if 'price' in s]
    if prices:
        winner = min(prices, key=lambda x: x[1])
        print(f"Best Price: {winner[0]} at ${winner[1]}")
    print("="*80)


def gemini_compare_results(specs_list: list) -> dict:

    print("\n🤖 Gemini AI Comparison in progress...\n")

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = f"""
            You are a retail product analyst.

            Compare the following products and return ONLY valid JSON in this format:

            {{
            "best_value_product": "...",
            "reason": "...",
            "comparison_summary": [
                {{
                "product_name": "...",
                "strengths": ["..."],
                "weaknesses": ["..."]
                }}
            ]
            }}

            Products data:
            {json.dumps(specs_list, indent=2)}
            """

        response = model.generate_content(prompt)

        clean_text = response.text.strip().strip("```json").strip("```")
        result = json.loads(clean_text)

        print("Gemini comparison completed")
        return result

    except Exception as e:
        print(f"Gemini comparison failed: {str(e)}")
        return {}

def main():
    """Run the demo"""
    print("\n GEMINI MULTIMODAL DEMO - SPEC SHEET COMPARISON\n")
    
    # Analyze each spec sheet
    
    print("📋 Loading and analyzing spec sheets...")
    results = []
    print(files)
    for spec_file in files:
        spec_file = str("{}/{}".format(base_path, spec_file))
        print(spec_file)
        if os.path.exists(spec_file):
            specs = analyze_single_spec(spec_file)
            if specs:
                results.append(specs)
    if results:
        compare_products(results)
        
        # Save results
        with open('demo_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print("\n Results saved to demo_results.json")
        
        ai_result = gemini_compare_results(results)

        print("\nAI Verdict")
        print("=" * 80)
        print(f"Best Value Product: {ai_result.get('best_value_product')}")
        print(f"Reason: {ai_result.get('reason')}\n")

        for item in ai_result.get("comparison_summary", []):
            print(f"{item['product_name']}")
            print(f"Strengths: {', '.join(item['strengths'])}")
            print(f"Weaknesses: {', '.join(item['weaknesses'])}")
            print()


main()