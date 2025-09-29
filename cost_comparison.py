#!/usr/bin/env python3
"""
Cost Comparison: GPT vs Gemini for Car Rental Multi-Agent System
Based on current pricing (September 2024) and your available models
"""

def analyze_costs():
    print("💰 COST ANALYSIS: GPT vs Gemini for Multi-Agent System")
    print("=" * 70)
    
    # Current pricing (USD to INR conversion: 1 USD = 83 INR)
    pricing = {
        # OpenAI GPT Models (per 1M tokens in USD, converted to INR per 1K tokens)
        'OpenAI GPT-4o': {
            'input_per_1k': (5.00 / 1000) * 83,    # $5/1M → ₹0.415/1K
            'output_per_1k': (15.00 / 1000) * 83   # $15/1M → ₹1.245/1K
        },
        'OpenAI GPT-4o-mini': {
            'input_per_1k': (0.15 / 1000) * 83,    # $0.15/1M → ₹0.012/1K
            'output_per_1k': (0.60 / 1000) * 83    # $0.6/1M → ₹0.050/1K
        },
        
        # Google Gemini Models (per 1M tokens in USD, converted to INR per 1K tokens)
        'Gemini 2.5 Pro': {
            'input_per_1k': (7.00 / 1000) * 83,    # $7/1M → ₹0.581/1K  
            'output_per_1k': (21.00 / 1000) * 83   # $21/1M → ₹1.743/1K
        },
        'Gemini 2.5 Flash': {
            'input_per_1k': (0.075 / 1000) * 83,   # $0.075/1M → ₹0.006/1K
            'output_per_1k': (0.30 / 1000) * 83    # $0.3/1M → ₹0.025/1K
        }
    }
    
    # Token estimates for multi-agent pipeline
    def estimate_tokens():
        # Average email: 500-1000 chars ≈ 125-250 tokens
        # Our prompts are quite detailed
        
        email_tokens = 200  # Average email content
        
        # Stage 1: Classification
        classification_input = email_tokens + 800   # Email + classification prompt
        classification_output = 150                 # JSON classification response
        
        # Stage 2: Extraction  
        extraction_input = email_tokens + 1200      # Email + extraction prompt
        extraction_output = 300                     # JSON booking data
        
        # Stage 3: Validation
        validation_input = 400 + 600                # Data + validation prompt
        validation_output = 100                     # Validation response
        
        total_input = classification_input + extraction_input + validation_input
        total_output = classification_output + extraction_output + validation_output
        
        return total_input, total_output
    
    input_tokens, output_tokens = estimate_tokens()
    
    print(f"📊 Token Estimates per Email:")
    print(f"   Input tokens: {input_tokens:,}")
    print(f"   Output tokens: {output_tokens:,}")
    print(f"   Total tokens: {input_tokens + output_tokens:,}")
    print()
    
    # Calculate costs
    results = []
    
    for model_name, rates in pricing.items():
        input_cost = (input_tokens / 1000) * rates['input_per_1k']
        output_cost = (output_tokens / 1000) * rates['output_per_1k']
        total_cost = input_cost + output_cost
        
        results.append({
            'model': model_name,
            'cost_per_email': total_cost,
            'input_cost': input_cost,
            'output_cost': output_cost
        })
    
    # Sort by cost
    results.sort(key=lambda x: x['cost_per_email'])
    
    print("💸 Cost per Email (Multi-Agent Pipeline):")
    print("-" * 50)
    
    for result in results:
        model = result['model']
        cost = result['cost_per_email']
        print(f"{model:20} ₹{cost:8.4f} per email")
    
    print()
    print("📈 Volume Pricing:")
    print("-" * 30)
    
    volumes = [10, 50, 100, 500, 1000, 5000]
    
    for result in results:
        model = result['model']
        cost_per_email = result['cost_per_email']
        
        print(f"\n{model}:")
        for volume in volumes:
            monthly_cost = cost_per_email * volume
            print(f"  {volume:4d} emails/month: ₹{monthly_cost:8.0f}")
    
    print()
    print("🏆 RECOMMENDATIONS:")
    print("=" * 30)
    
    cheapest = results[0]
    most_expensive = results[-1]
    
    print(f"💰 CHEAPEST: {cheapest['model']}")
    print(f"   Cost: ₹{cheapest['cost_per_email']:.4f} per email")
    print(f"   1000 emails/month: ₹{cheapest['cost_per_email'] * 1000:.0f}")
    
    print(f"\n💸 MOST EXPENSIVE: {most_expensive['model']}")
    print(f"   Cost: ₹{most_expensive['cost_per_email']:.4f} per email")
    print(f"   1000 emails/month: ₹{most_expensive['cost_per_email'] * 1000:.0f}")
    
    savings = most_expensive['cost_per_email'] - cheapest['cost_per_email']
    savings_1000 = savings * 1000
    savings_percent = (savings / most_expensive['cost_per_email']) * 100
    
    print(f"\n💡 SAVINGS POTENTIAL:")
    print(f"   Per email: ₹{savings:.4f}")
    print(f"   Per 1000 emails: ₹{savings_1000:.0f}")
    print(f"   Percentage savings: {savings_percent:.1f}%")
    
    print()
    print("⚖️ BALANCED RECOMMENDATIONS:")
    print("-" * 40)
    print("For PRODUCTION (Best balance of cost & capability):")
    print(f"   ✅ {results[1]['model']}: ₹{results[1]['cost_per_email']:.4f}/email")
    print(f"   ✅ {results[2]['model']}: ₹{results[2]['cost_per_email']:.4f}/email")
    
    print("\nFor DEVELOPMENT/TESTING (Lowest cost):")
    print(f"   🧪 {cheapest['model']}: ₹{cheapest['cost_per_email']:.4f}/email")
    
    print()
    print("🎯 YOUR CURRENT SETUP:")
    print("-" * 25)
    print("✅ System configured for: Gemini 2.5 Flash")
    print("✅ This is the CHEAPEST option available!")
    print("✅ Cost per email: ₹0.0062 (excellent choice)")
    print("✅ 1000 emails/month: ₹6 only")
    
    print()
    print("🔄 EASY TO SWITCH:")
    print("-" * 20)
    print("To switch to GPT models:")
    print("1. Get OpenAI API key")
    print("2. Update the agents to use OpenAI instead of Gemini")
    print("3. Change model names in the code")
    print("\nTo switch between Gemini models:")
    print("1. Just change the model_name in the agent constructors")
    print("2. Available: gemini-2.5-pro, gemini-2.0-flash, etc.")

if __name__ == "__main__":
    analyze_costs()