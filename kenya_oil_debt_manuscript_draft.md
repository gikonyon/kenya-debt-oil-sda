Oil Shocks, Domestic Debt and Fiscal Space in Kenya: A Stochastic Debt Sustainability Analysis
Author: Gikonyo Ndugu, Independent Researcher/Consultant, Nairobi, Kenya
Contact: ndugu.gikonyo@hotmail.com | ORCID: 0009-0000-4524-5384
Status: Skeleton draft. Text in [BRACKETS] is a result, source or decision still to be filled. No result below has been estimated yet.
---
Abstract
Kenya enters FY2026/27 with public debt of about KSh 13 trillion, close to 69% of GDP, and a domestic share of about 56% of the stock, at the same time as a global oil price shock. This paper asks how likely it is that Kenya's debt-to-GDP ratio crosses [THRESHOLD, to be set from the statutory anchor] by FY[YEAR], and how much of that risk comes from domestic borrowing costs rather than external debt. I estimate oil price pass-through to pump prices, inflation, the exchange rate and yields using [DATA SPAN] data, and feed the estimates into a two-currency debt dynamics model with [N] simulated shock paths. [MAIN RESULT: probability range and the oil price at which it changes.] [SECOND RESULT: domestic versus external contribution.] The results suggest [POLICY IMPLICATION, only after estimation].
Keywords: public debt sustainability; oil price shocks; domestic debt; fiscal space; Kenya; fan chart
JEL codes: E62, H63, Q43, O55 [verify]
---
1. Introduction
The 2026 shock: Murban crude rose from about USD 63 a barrel in December 2025 to nearly USD 98 by late March 2026; diesel prices rose 17.9% in one month; the CBK raised its 2026 current account deficit projection from 2.2% to 3.0% of GDP. [Cite sources with dates.]
Kenya's position: debt of KSh 13.01 trillion at end-June 2026 (KSh 13.23 trillion by July, provisional); debt-to-GDP about 69%; domestic debt 56.3% of the stock; 2026/27 deficit KSh 1.145 trillion (5.5% of GDP). [Verify each against the latest Treasury and CBK bulletins.]
Forecasts disagree on 2026 growth: World Bank 4.3%, IMF 4.5%, AfDB 4.6%, CBK 4.9%, Treasury 5.0%. [Verify.]
Gap: official and multilateral debt sustainability analyses exist, but [CONFIRM after literature search: whether any published study models the oil shock and the domestic debt channel jointly for Kenya].
Contribution: [state only what the literature search supports].
Research questions and structure.
2. Literature review
[To be completed after a systematic search. Starting points to verify before citing:]
Fiscal reaction functions and sustainability: Bohn (1998), Quarterly Journal of Economics.
Fiscal fatigue and fiscal space: Ghosh, Kim, Mendoza, Ostry and Qureshi (2013), Economic Journal.
Fan-chart approaches to debt risk in emerging markets: Celasun, Debrun and Ostry (2006), IMF Staff Papers.
IMF and World Bank debt sustainability frameworks for market-access and low-income countries.
Oil price pass-through in net-importing African economies: [SEARCH].
Kenya-specific debt and fiscal studies: [SEARCH].
3. Data and Kenya's debt structure
Variable	Source	Frequency	Span
Debt stock by instrument, domestic and external	National Treasury; CBK	Monthly/Quarterly	[ ]
Interest payments, primary balance	Treasury; Controller of Budget	Annual/Quarterly	[ ]
GDP, CPI	KNBS	Quarterly/Monthly	[ ]
Pump prices	EPRA	Monthly	[ ]
Brent/Murban	EIA; World Bank	Monthly	[ ]
Exchange rate, T-bill and bond yields	CBK	Monthly	[ ]
Definitions: public and publicly guaranteed debt as defined by the Treasury [confirm]. Effective interest rates are computed as interest paid divided by the prior-period stock, not from headline yields.
Descriptive facts to tabulate: debt composition, maturity profile, interest-to-revenue ratio, holders of domestic debt [SOURCE].
4. Model and estimation
4.1 Debt dynamics
For domestic and external debt as shares of GDP:
d_dom(t) = d_dom(t-1) (1 + i_d) / (1 + g_n) - phi * pb(t)
d_ext(t) = d_ext(t-1) (1 + i_e)(1 + e) / (1 + g_n) - (1 - phi) * pb(t)
where i is the effective interest rate, g_n nominal GDP growth, e depreciation, pb the primary balance and phi the domestic financing share.
4.2 Oil block
Pass-through of oil prices to pump prices, CPI, the exchange rate, growth and yields, estimated by [METHOD: ARDL / VAR / local projections] on [SPAN]. 2026 is treated as a scenario, not an estimation point, because the shock history is too short.
4.3 Stochastic layer
Shocks drawn from the estimated residual distribution, [N] paths, horizon [H] years. Threshold probabilities and fan charts reported.
4.4 Scenarios
Oil at USD 70, 90 and 110; consolidation of 0.5 and 1.0 pp of GDP per year. Forecast-source sensitivity: World Bank versus Treasury growth.
5. Results
[Pass-through estimates table] [Fan chart] [Threshold probabilities by scenario] [Domestic versus external contribution] [Robustness: alternative growth path, alternative threshold, alternative pass-through].
6. Policy implications and fiscal space
[Write only after results. Link to debt management strategy, domestic market development, and the cost of consolidation.]
7. Limitations
Short history for the 2026 shock; reliance on long-sample pass-through.
Disagreement among growth forecasts.
Simplified financing split and exogenous primary balance.
Debt data definitions differ across sources.
Simulation outputs are conditional on estimated parameters, not forecasts.
8. Conclusion
[After results.]
Data and code availability
Interactive simulation: [GITHUB URL] and [STREAMLIT URL]. Parameters in the public version are placeholders until the estimates are final.
References
[Complete after literature search. Do not cite from this skeleton without verifying each reference.]
---
Target journals to check (scope, fees, review times)
Journal of African Economies
African Development Review
Review of Development Finance
[Check each journal's current scope and article processing charges before choosing.]
