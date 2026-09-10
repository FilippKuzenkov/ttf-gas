# TTF Gas Price vs. German Day-Ahead Electricity Price

**Decision.** Framed as if delivered to an energy trading/risk desk: is TTF gas price a reliable leading indicator for German day-ahead electricity price exposure, and under what conditions should that signal be trusted more or less? 

**North Star metrics.**
1. **Correlation strength** - how tightly does gas price move with electricity price?
2. **Reliability by condition** - does that relationship hold evenly across weekday/weekend and season, or does confidence need to vary?
3. **Magnitude** - how much does electricity price move per unit of gas price change?

## Recommendation

1. **Trust the gas-price signal at full weight for weekday and summer exposure; apply a wider margin for weekends and winter.** Weekday correlation (r=0.905) is meaningfully stronger than weekend (r=0.837) - checked directly and confirmed this isn't a data-staleness artifact (see Evidence, below). Summer (r=0.946) is stronger than winter (r=0.783). For a desk calibrating hedge ratios or position sizing off this indicator.
2. **Don't use gas price alone for peak/extreme-price risk - pair it with a volatility or demand-spike indicator.** Gas explains average electricity pricing better than price peaks (mean r=0.874 vs. peak r=0.837), and the same pattern holds by hour (nighttime r=0.883 vs. daytime r=0.822) - the driver is extremeness, not time-of-day. For a desk building tail-risk/VaR models, where over-trusting this indicator would fail worst.
3. **Investigate why winter specifically weakens the relationship before extending this indicator to winter risk models.** Not yet actionable - this is the next analysis, not a confident recommendation. Plausible cause: winter introduces electricity-price volatility (cold-snap demand, wind-generation swings) that a single-variable linear fit can't capture. For whoever owns this indicator's methodology, before it's relied on in Q4/Q1 risk cycles.

## Evidence

**The baseline relationship holds, and holds tightly.** Daily gas price (TTF, ACER/ICIS) correlates strongly with both mean (r=0.874, R²=0.764) and peak (r=0.837, R²=0.701) daily German electricity price, across 1,924 days from 2021 to 2026. This is consistent with Germany's merit-order power market, where gas plants are frequently the marginal, most expensive generator dispatched - gas price often directly sets the electricity clearing price. Correlation alone says nothing about causation, and no other driver of electricity price (demand, renewable output, carbon price) is controlled for here - that caveat applies to every finding below.

![Gas vs. daily mean electricity price](charts/gas_vs_electricity_mean.png)
![Gas vs. daily peak electricity price](charts/gas_vs_electricity_peak.png)

**The relationship is tighter on weekdays than weekends** Weekday r=0.905 (n=1,374) vs. weekend r=0.837 (n=550). Because TTF gas doesn't trade weekends (Saturday/Sunday carry Friday's price forward), a real methodological risk here is that the weekend gap is a join artifact - restricted gas-price variation on weekends mechanically depressing the correlation - rather than a genuine economic difference. Staling weekday gas price by one day (mimicking mild staleness) barely moved weekday r (0.905 → 0.909) - the opposite of what an artifact explanation predicts. Plausible real mechanism: weekday electricity demand is more industrial/predictable, weekend demand shifts toward residential and is more variable, diluting the gas signal.

**The relationship is strongest in summer, weakest in winter - the opposite of what was expected going in.** A stated hypothesis (heating-driven gas demand should make winter the strongest season) was checked directly against the data and falsified: summer r=0.946, winter r=0.783, with spring (0.843) and autumn (0.814) between. Plausible explanation, not yet confirmed: winter likely introduces electricity-price volatility from sources other than gas - cold-snap demand spikes, wind-generation swings - that a single-variable fit can't capture even though gas still matters. This is the open thread behind Recommendation 3.

![Correlation by segment](charts/correlation_by_segment.png)

**Peak prices are noisier than average prices.** Mean electricity correlates more tightly with gas than peak electricity does (0.874 vs. 0.837). The same shape shows up again by hour: nighttime (r=0.883) beats daytime (r=0.822) - the opposite of what "daytime is noisier" would predict. Read together, the sharper explanation is that a single extreme value (a demand spike, a curtailment event) carries more idiosyncratic noise than an averaged window, independent of when in the day or week it happens. This is the basis for Recommendation 2.

## Appendix - data, methodology, and scope

**Sources and validation.** TTF gas (ACER/ICIS, daily, 2021-01-01 to 2026-04-08) and German day-ahead electricity (SMARD, hourly, same range) - both checked against independent references (energy-charts.info for electricity, Yahoo `TTF=F` for gas) before any analysis; gas's weekend carry-forward pattern confirmed across 4 separate weekends. Full detail, exact download steps, and known data quirks: [`DATA_SOURCES.md`](DATA_SOURCES.md).

**Reproduction.** `scripts/pull_smard.py` → `scripts/join_data.py` → `scripts/analyze_correlation.py`, in order. Each step's row counts and a hand-traced sample are checked against the raw inputs - see the scripts themselves, not narrated here.

**Limitations.** Correlation, not causation - demand, renewable output, and carbon price are unaccounted for. Gas is a futures/day-ahead assessment, not a perfect proxy for real-time spot price (a small, consistent gap against Yahoo's futures close confirms this, rather than being a red flag). Weekend gas prices are carried forward, not real settlement values - a documented source limitation, checked and found not to explain the weekday/weekend finding above.

**Tool-stack note.** Analysis is Python; [`excel/ttf_electricity.xlsx`](excel/ttf_electricity.xlsx) is a deliberate second-tool addition: a pivot-table view of the same joined data (monthly gas/electricity averages, conditional-formatted), plus the Issues Log and Insights Log tabs transcribed by hand from `DATA_SOURCES.md`.

