#!/usr/bin/env python3
"""
Seed scenarios vào DynamoDB LexiApp table.
Dùng để setup test data cho API tests.
"""

import os
import sys
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from infrastructure.persistence.dynamo_scenario_repo import DynamoScenarioRepository
from domain.entities.scenario import Scenario

# Set table name
os.environ['LEXI_TABLE_NAME'] = 'LexiApp'

def seed_scenarios():
    """Seed sample scenarios."""
    repo = DynamoScenarioRepository()
    
    scenarios = [
        Scenario(
            scenario_id="restaurant-ordering",
            scenario_title="Ordering at a Restaurant",
            context="You are at a restaurant and want to order food.",
            roles=["customer", "waiter"],
            goals=["order food", "ask about menu", "request modifications"],
            is_active=True,
            usage_count=0,
            difficulty_level="A2",
            order=1,
            notes="Basic restaurant ordering scenario",
        ),
        Scenario(
            scenario_id="hotel-check-in",
            scenario_title="Hotel Check-in",
            context="You are checking into a hotel and need to complete the registration.",
            roles=["guest", "receptionist"],
            goals=["check in", "ask about amenities", "request room service"],
            is_active=True,
            usage_count=0,
            difficulty_level="A2",
            order=2,
            notes="Hotel check-in scenario",
        ),
        Scenario(
            scenario_id="job-interview",
            scenario_title="Job Interview",
            context="You are interviewing for a job position.",
            roles=["candidate", "interviewer"],
            goals=["introduce yourself", "discuss experience", "ask about role"],
            is_active=True,
            usage_count=0,
            difficulty_level="B1",
            order=3,
            notes="Job interview scenario",
        ),
        Scenario(
            scenario_id="airport-check-in",
            scenario_title="Airport Check-in",
            context="You are at the airport checking in for your flight.",
            roles=["passenger", "check-in agent"],
            goals=["check in luggage", "ask about boarding", "confirm flight details"],
            is_active=True,
            usage_count=0,
            difficulty_level="A2",
            order=4,
            notes="Airport check-in scenario",
        ),
        Scenario(
            scenario_id="doctor-appointment",
            scenario_title="Doctor Appointment",
            context="You are at a doctor's office for a medical appointment.",
            roles=["patient", "doctor"],
            goals=["describe symptoms", "ask about treatment", "get prescription"],
            is_active=True,
            usage_count=0,
            difficulty_level="B1",
            order=5,
            notes="Doctor appointment scenario",
        ),
    ]
    
    for scenario in scenarios:
        try:
            repo.create(scenario)
            print(f"✅ Created: {scenario.scenario_id}")
        except Exception as e:
            print(f"❌ Failed to create {scenario.scenario_id}: {e}")
    
    # Verify
    all_scenarios = repo.list_active()
    print(f"\n✅ Total scenarios in DB: {len(all_scenarios)}")
    for s in all_scenarios:
        print(f"  - {s.scenario_id}: {s.scenario_title} (order={s.order})")

if __name__ == "__main__":
    seed_scenarios()
