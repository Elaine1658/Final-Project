from __future__ import annotations
from dataclasses import dataclass
from statistics import mean
from pathlib import Path
import json
import os
from mcp_server.server import get_sales_history, get_inventory, get_dining_context

@dataclass
class Event:
    agent: str
    kind: str
    text: str
    tool: str | None = None

def _forecast(meal, history, context):
    sold = [r['sold'] for r in history if r['meal'] == meal]
    baseline = mean(sold) if sold else 20
    event_factor = 1 + min(context['expected_attendance'] / 1000, 0.35)
    weather_factor = 0.92 if context['weather'] == 'rain' and meal == 'Soup and sandwich' else 1.0
    demand = round(baseline * event_factor * weather_factor)
    return demand, round(baseline, 1)

def build_plan(weather_override=None, attendance_override=None):
    events = []
    events.append(Event('Manager', 'message', 'Starting a draft plan for tomorrow; no purchase or inventory update will be made.'))
    history = get_sales_history()
    events.append(Event('Demand Forecast', 'tool', 'Read recent portions sold and prepared for each menu item.', 'sales_history'))
    inventory = get_inventory()
    events.append(Event('Inventory', 'tool', 'Read on-hand quantities, unit costs, and expiry windows.', 'inventory_snapshot'))
    context = dict(get_dining_context())
    if weather_override:
        context['weather'] = weather_override
    if attendance_override is not None:
        context['expected_attendance'] = max(0, int(attendance_override))
    events.append(Event('Context', 'tool', f"Read weather ({context['weather']}), event ({context['event_name']}), and attendance ({context['expected_attendance']}).", 'campus_context'))
    rows = []
    for item in inventory:
        demand, baseline = _forecast(item['meal'], history, context)
        safety_buffer = 0.08 if context['confidence'] >= 0.8 else 0.03
        recommended = round(demand * (1 + safety_buffer))
        recommended = min(recommended, item['on_hand'])
        coverage = recommended / demand if demand else 1
        projected_waste = max(0, recommended - demand)
        risk = []
        if item['expiry_days'] <= 1:
            risk.append('use soon')
        if coverage < 0.9:
            risk.append('shortage risk')
        if context['confidence'] < 0.8:
            risk.append('low context confidence')
        rows.append({
            'meal': item['meal'], 'baseline_demand': baseline, 'predicted_demand': demand,
            'recommended_prep': recommended, 'on_hand': item['on_hand'],
            'unit_cost': item['unit_cost'], 'projected_waste': projected_waste,
            'projected_waste_cost': round(projected_waste * item['unit_cost'], 2),
            'coverage': round(coverage, 2), 'expiry_days': item['expiry_days'],
            'risk': risk, 'needs_review': bool(risk)
        })
    events.append(Event('Waste Reduction', 'analysis', 'Compared predicted demand with inventory and marked expiry and shortage risks.'))
    waste_cost = round(sum(r['projected_waste_cost'] for r in rows), 2)
    expected_demand = sum(r['predicted_demand'] for r in rows)
    prep = sum(r['recommended_prep'] for r in rows)
    events.append(Event('Cost', 'analysis', f'Estimated {prep} portions prepared and ${waste_cost:.2f} of projected overproduction cost.'))
    blockers = []
    if context['confidence'] < 0.8:
        blockers.append('event attendance confidence is below 80%')
    if any(r['coverage'] < 0.9 for r in rows):
        blockers.append('at least one item has shortage risk')
    if any(r['expiry_days'] <= 1 for r in rows):
        blockers.append('an ingredient should be used soon')
    status = 'needs_manager_review' if blockers else 'draft_ready'
    historical_avg_waste = round(mean(r['wasted'] for r in history), 1)
    reduction = round(max(0, (historical_avg_waste - sum(r['projected_waste'] for r in rows)) / historical_avg_waste * 100), 1) if historical_avg_waste else 0
    events.append(Event('Safety Review', 'review', 'Plan is held for manager review: ' + '; '.join(blockers) if blockers else 'No blocking safety flags found.'))
    plan = {
      'context': context, 'rows': rows,
      'metrics': {'predicted_demand': expected_demand, 'recommended_prep': prep,
                  'projected_waste': sum(r['projected_waste'] for r in rows),
                  'projected_waste_cost': waste_cost,
                  'items_needing_review': sum(r['needs_review'] for r in rows),
                  'historical_avg_waste': historical_avg_waste,
                  'estimated_waste_reduction_pct': reduction},
      'status': status, 'events': [e.__dict__ for e in events]
    }
    if os.getenv('LIVE_AI', 'false').lower() == 'true' and (os.getenv('PORTKEY_API_KEY') or os.getenv('OPENAI_API_KEY')):
        try:
            from .live_ai import run_live_review
            live = run_live_review(plan, history, inventory, context)
            plan['live_ai'] = live
            plan['events'].append(Event('Live Review', 'model', 'Reviewed the draft with the configured provider-backed model.', None).__dict__)
        except Exception as exc:
            plan['live_ai'] = {'mode': 'error', 'error': type(exc).__name__}
            plan['events'].append(Event('Live Review', 'error', 'Live review failed; deterministic draft retained for safety.', None).__dict__)
    else:
        plan['live_ai'] = {'mode': 'offline', 'model': None, 'usage': {'input_tokens': 0, 'cached_input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0, 'cost': 0}}
    return plan
