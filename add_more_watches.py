#!/usr/bin/env python3
"""
Example of how to add more watches to monitor ANY items on Vinted.
"""

print("🔍 Your Vinted Monitor Works with ANY Items!")
print("=" * 50)
print()
print("✅ You already have 2 watches configured:")
print("   1. 'ETB aventures ensemble' - under 150 EUR")
print("   2. 'blister rivalités destinées' - under 5 EUR")
print()
print("🎯 To add MORE watches, edit config/watches.yaml:")
print()

example_watches = """
watches:
  # Your existing watches
  - name: "ETB aventures ensemble"
    vinted_domain: "vinted.fr"
    query: "ETB aventures ensemble"
    max_price: 150.0
    currency: "EUR"
    polling_interval_sec: 30

  - name: "blister rivalités destinées"
    vinted_domain: "vinted.fr"
    query: "blister rivalités destinées"
    max_price: 5.0
    currency: "EUR"
    polling_interval_sec: 45

  # ADD NEW WATCHES HERE:
  - name: "Nike Air Force 1"
    vinted_domain: "vinted.fr"
    query: "nike air force 1"
    max_price: 80.0
    currency: "EUR"
    polling_interval_sec: 60

  - name: "iPhone 13"
    vinted_domain: "vinted.fr"
    query: "iphone 13"
    max_price: 400.0
    currency: "EUR"
    polling_interval_sec: 30

  - name: "Vintage Denim Jacket"
    vinted_domain: "vinted.fr"
    query: "veste jean vintage"
    max_price: 25.0
    currency: "EUR"
    polling_interval_sec: 45

  - name: "PlayStation 5"
    vinted_domain: "vinted.fr"
    query: "playstation 5 ps5"
    max_price: 350.0
    currency: "EUR"
    polling_interval_sec: 30
"""

print(example_watches)
print()
print("🚀 How to add new watches:")
print("1. Edit config/watches.yaml")
print("2. Add new watch entries (copy the format above)")
print("3. Restart the monitor: python -m app.main run")
print()
print("🔔 You'll get Discord notifications for ALL watches!")
print("   Each watch monitors different items independently.")
print()
print("💡 Pro tips:")
print("• Use specific queries for better results")
print("• Set realistic max_price limits")
print("• Different polling intervals for different priorities")
print("• Test new watches first: python -m app.main test-watch 'Watch Name' --dry-run")
