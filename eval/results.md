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
1. The most of errors 16 from first test and 22 from the second are mistake between 2 and 3 in indic digits "inv_001_ar_classic"
   Hypothesis : the invoices are small
   Next : test 2x size
2. The model make mistake when read invoice number RTL read as LTR "inv_001_ar_classic"
   Hypothesis : the model read LTR in arabic or mixed invoices
   Next : add additional information to the prompts
3. The model add arabic letters to words without needed "inv_002_mixed_classic"
   Hypothesis : the model is weak on reading arabic letters and numbers
   Next : try another model



## Model comparison (scanned, 30 invoices)
 
| metric | gemini-3.8-flash | gemini-3.8-flash-lite |
|---------------|------------------|-----------------------|
| fully correct | ..% | ..% |
| weakest field | field ..% | field ..% |
| validator caught | ../.. | ../.. |
| false alarms | ../.. | ../.. |
| avg seconds | .. | .. |
| cost per invoice | $.. | $.. |
| cost per fully-correct invoice | $.. | $.. |
 
## Decision
Default model: ...
Why: ...
When I would switch: ...
Next idea: ...
