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