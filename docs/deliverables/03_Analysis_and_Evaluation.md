# 03. Analysis and Evaluation

## Evaluation Goal
Assess whether AgriRulePH provides consistent, explainable, and decision-useful crop recommendations across varied farm-condition inputs.

## Test Approach

### A. Functional Workflow Tests
1. Submit consultation form with valid inputs.
2. Verify results page displays:
- Top recommendations
- Avoid list
- Explanation traces
3. Verify analytics page loads for same consultation ID.
4. Verify history records top recommendation correctly.

### B. Rule Behavior Scenarios
Use representative conditions and verify expected behavior patterns:
1. Wet + favorable water + staple profile -> staple-related crops rank high.
2. Low water conditions -> water-demanding crops drop or appear in avoid.
3. Vegetable preference + suitable soil/water -> vegetables climb ranking.
4. Adverse combinations -> fallback ranking still produced with lower confidence.
5. Critical mismatch triggers -> avoid list populated with clear reasons.

### C. Explainability Checks
1. Each top recommendation has trace lines that map to matched conditions.
2. Avoid cards show concise and readable negative reasons.
3. Analytics interpretation blocks are section-specific and non-redundant.

## Suggested Evaluation Metrics

1. **Recommendation Consistency**
- Same input should produce same ranking and avoid output.

2. **Explainability Coverage**
- Percentage of top results with non-empty explanation traces.

3. **Avoid Detection Coverage**
- Percentage of high-mismatch scenarios where avoid list is populated.

4. **Scenario Sensitivity**
- Number of what-if scenarios that change top recommendation.

5. **Usability Proxy**
- User can identify top crop, backup crops, and key risk factors within one session.

## Current Observations (System-Specific)
- Rule engine provides deterministic outputs with traceable reasoning.
- Top-10 and analytics sections improve transparency and comparison quality.
- What-if analysis is useful for sensitivity checking of conditions.
- Avoid section readability has improved through compact warning formatting.

## Limitations
1. Rule quality depends on knowledge base quality and completeness.
2. No real-time weather, market, or pest integration.
3. Generalized national rules may not fit all micro-locations.
4. Some interpretation text can still be refined for local language simplicity.

## Recommended Improvements
1. Expand and validate rules with agricultural domain experts.
2. Add municipality-level condition presets where feasible.
3. Add printable consultation summary for field use.
4. Add optional local language support for farmer-facing explanations.
5. Add structured benchmark evaluation against expert recommendations.
