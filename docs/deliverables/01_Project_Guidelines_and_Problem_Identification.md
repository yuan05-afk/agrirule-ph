# 01. Project Guidelines and Problem Identification

## Project Title
**AgriRulePH: A Rule-Based Crop Planning Decision Support System for Small-Scale Farmers in the Philippines**

## Real-World Problem
Small-scale farmers often make crop selection decisions under uncertain conditions such as seasonal shifts, water reliability, soil constraints, and limited budget. In many cases, consultation with local experts is not always immediately accessible at planning time.

## Problem Statement
There is a need for a practical and explainable decision-support tool that helps farmers identify suitable crops based on farm conditions while clearly showing why recommendations are made and which crops should be avoided.

## Target Users
- Small-scale farmers in the Philippines
- Students/researchers studying intelligent systems and rule-based reasoning
- Agricultural extension support contexts for preliminary planning discussion

## Expected Impact
- Faster pre-planting crop shortlisting based on actual farm conditions
- Better transparency through explanation traces and avoid reasons
- Improved planning confidence using ranked recommendations, analytics, and what-if scenarios

## Why This Problem Was Chosen
- High practical relevance to Philippine agriculture
- Strong fit for deterministic expert-system methods in Intelligent Systems coursework
- Supports explainable AI principles without requiring black-box prediction models

## Scope
AgriRulePH evaluates:
- Season
- Water availability
- Soil type
- Soil pH category
- Farm type
- Budget level
- Crop preference

Output scope:
- Top recommendations (ranked)
- Crops to avoid
- Explanation trace
- Decision analytics (top-10 comparison, podium, category opportunity, factor strength, trade-off, what-if, tiers, insights table)

## Out of Scope
- Real-time weather integration
- Real-time market price optimization
- Pest/disease prediction modeling
- Satellite/IoT automatic sensing
- Machine learning prediction and probabilistic forecasting

## Objectives
1. Build a complete rule-based DSS that is usable through a web interface.
2. Provide explainable ranking and avoid logic using IF-THEN style rules.
3. Persist consultations/results for history and analytics review.
4. Provide actionable interpretation layers for better farmer decision support.
