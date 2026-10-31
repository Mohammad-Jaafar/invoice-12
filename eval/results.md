# Results
 
## Clean invoices
model=gemini-flash-lite-latest dir=data/clean invoices=30 errors=0
supplier_name      93%
supplier_trn       83%
invoice_number     77%
invoice_date       83%
currency           100%
items              87%
subtotal           97%
vat_amount         100%
total              100%
fully correct      70%
  fully correct [en]  100%  (10 invoices)
  fully correct [ar]  60%  (10 invoices)
  fully correct [mixed]  50%  (10 invoices)


avg seconds: 6.3
avg tokens in/out: 1197/329
cost per invoice: unknown (no price for gemini-flash-lite-latest)
saved to eval/runs/gemini-flash-lite-latest__clean.json

## What the validator catches

wrong invoices flagged by validator: 4/9
correct invoices flagged by mistake: 0/21

- The validator caught 4 of 9 wrong invoices (44%) with 0 false alarms, and none of the 5 missed invoices broke one of its rules.
- invoice_number, invoice_date and supplier_name have no rules, so errors in them always pass (invoice_number was wrong in 4 of the 5 missed invoices).
- supplier_trn has a rule, but it only checks the length, so a misread TRN with 15 digits passes.
- Errors inside checked fields also pass when they don't break the math: a 1-cent subtotal error is inside the 0.02 tolerance, and "كرسي مكتبي" instead of "كرسي مكتب" is a text error with no rule.
- The validator can never catch these because it has no ground truth: it only checks that the invoice is consistent with itself, not that it is correct.


## Scanned invoices
model=gemini-flash-lite-latest dir=data/scanned invoices=30 errors=0
supplier_name      97%
supplier_trn       83%
invoice_number     83%
invoice_date       83%
currency           100%
items              87%
subtotal           93%
vat_amount         100%
total              97%
fully correct      73%
  fully correct [en]  100%  (10 invoices)
  fully correct [ar]  60%  (10 invoices)
  fully correct [mixed]  60%  (10 invoices)

avg seconds: 6.4
avg tokens in/out: 1197/327
cost per invoice: unknown (no price for gemini-flash-lite-latest)
saved to eval/runs/gemini-flash-lite-latest__scanned.json

## What the validator catches on scanned
wrong invoices flagged by validator: 4/8
correct invoices flagged by mistake: 0/22


| field            | clean | scanned | change |
|-------           |-------|---------|--------|
| supplier_name    | 93%   |   97%   |   +4   |
| invoice_number   | 77%   |   83%   |   +6   |
| total            | 100%  |   97%   |   -3   |
| fully correct    | 70%   |   73%   |   +3   |
| subtotal         | 97%   |   93%   |   -4   |
| validator caught | 4/9   |   4/8   |        |
| false alarms     | 0/21  |   0/22  |        |


There was no change: the same result after 2 prompt changes.
It didn't exceed the noise.
I will remove the change.

## Error analysis : 
1. The most common digit error is reading ٢ as ٣ "inv_001_ar_classic"
   Hypothesis : the invoices are small
   Next : test 2x size
2. The model makes mistakes when reading invoice number reads the RTL invoice number as LTR     "inv_001_ar_classic"
   Hypothesis : the model read LTR in arabic or mixed invoices
   Next : add additional information to the prompts
3. The model adds Arabic letters that are not printed "inv_002_mixed_classic"
   Hypothesis : the model is weak on reading arabic letters and numbers
   Next : try another model



## Model comparison (scanned, 30 invoices)
I tried gemini-3.8-flash, but 17 of 30 invoices failed (11 because of the free tier limit of 20 requests per day, 5 because the server was busy, 1 cut-off answer), so the comparison is not complete.
Because of that I decided to keep gemini-flash-lite-latest as the default model.

## Decision
Default model: gemini-flash-lite-latest
Why: it has 500 free requests per day (gemini-3.8-flash has 20), and it gets 70-73% fully correct in about 6 seconds per invoice.
When I would switch: when I activate the payment and a stronger model improves fully correct by more than the noise (±1 invoice).
Next idea: test 2x image size to see if the ٢/٣ error goes down.

## Review
Reviewed 10 scanned synthetic invoices in the dashboard.
Average review time: 80 seconds per invoice (min 20, max 120).
Flagged by the validator: 2. Corrected by me: 2. Corrected but NOT flagged: 0.
