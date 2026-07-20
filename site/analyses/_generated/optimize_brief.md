*Client: Erik Malm, owner, Malm's Market, Bjorkvagen, Solby.*

### The letter

> Dear analyst,
>
> I'm 51. I spent 15 years working for Nordmart before I opened Malm's Market myself, on Bjorkvagen in Solby, with about 60,000 euros of my own money behind it. That was 2025.
>
> Over one year we have taken in about 479,000 euros across the till altogether, and the bottom line came out to a loss. I want someone who isn't me to look at my numbers properly before I decide whether to hold on, change something, or walk away.
>
> I've kept everything — every receipt, every invoice, every month's books. My records aren't perfect, and I'll tell you honestly where they wobble, but they're complete, and my own monthly ledger is right, because I check it myself.
>
> Tell me what the numbers actually say.
>
> — Erik Malm

### Intake interview notes

*In Erik Malm's own words.*

**Q: Tell me about yourself and how the shop started.**

He: I'm 51. I spent 15 years working for Nordmart before deciding to open my own place. I had about 60,000 euros saved, and I took a spot on Bjorkvagen, in Solby. We opened in 2025.

**Q: What kind of shop is it?**

He: A full grocery, small format — about 162 products on the shelf at any time. People come because we're close and we have what they need — that's the whole business. I'd guess close to 62 percent of what we take is by card, the rest cash.

**Q: Walk me through the routine.**

He: Same routine most weeks. Deliveries come every Wednesday, one truck. I do the shelf prices myself, only when they've genuinely drifted.

**Q: What do you think happened?**

He: Honestly, I don't think it's one single villain. I think we're just not running as tight as we should be — waste, small inefficiencies, day to day. That's what I want you to find, not one big story.

**Q: Anything I should know about the records before you start?**

He: Yes, be careful with 4 things. First, the till terminal mis-rings an item now and then — I void it and re-ring it, so you'll find 66 paired correction lines in the receipts over the whole period, nothing missing, just messy. Second, my supplier's system has posted the same invoice twice before — I caught 21 such duplicates myself, but I'll admit I don't check every single one. Third, some delivery paperwork never got typed in — there were weeks I was alone and exhausted, and I paid the supplier for goods you won't find an invoice line for; my bank-account ledger is still right, I just can't always show you the paper behind it. Fourth, the little weather log I keep goes dark for a few days now and then — 4 missing day(s) over the whole period — the station on the roof is nothing fancy.

**Q: What does a useful answer look like to you?**

He: Pages I can read. A number, and how sure you are behind it. Don't be polite about it either.

### The data

Erik Malm hands over complete records for the full one year:

| File | What it is |
|---|---|
| `calendar` | the trading calendar |
| `cost_sheet` | the monthly ledger, authoritative for money: revenue, procurement, rent, wages, utilities, VAT remitted, capital spend, tax payments |
| `inventory_eod` | end-of-day book stock per product |
| `locations` | the site-scouting notes from before opening |
| `price_history` | every shelf-tag change, per product |
| `procurement` | supplier invoice lines: order/delivery/posted dates, quantity, unit cost |
| `promotions` | markdown campaigns: dates, depth, category |
| `receipts` | every till line: date, hour, product, quantity, unit price, payment type; card payments carry a stable but anonymized customer code; voided lines and refunds reference the original line |
| `tax_statement` | the annual filings |
| `weather` | the shop's own temperature and rainfall log |
| `write_offs` | everything binned, with a reason |

### The questions

1. "Show me where the money actually goes."
2. "What is the shrinkage costing me, and should I be worried about theft?"
3. "Where am I bleeding money without noticing it day to day?"
4. "What should I actually do next?"

### Stakes

Erik Malm doesn't think one event explains the numbers — he suspects the day-to-day running of the shop itself, and wants that priced before weighing whether to hold on, change something, or walk away.

*(This brief is generated from this run's own settings and its own real results — no hidden simulation parameter appears above. Edit freely; this is a starting outline, not a finished case.)*