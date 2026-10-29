## Day zero :
setting up the environment

## Day 1 : 
Goal : Generate 10 invoices (en,ar,mix) with ground truth JSON
Pydantic : validate the data and throw errors
Jinja2 : provide a templates
Playwright : Run hidden browser to see the result without run the real browser

What happen : I didn't really understand 100% of the codebase but about 70-80%
Tomorrow I will try to understand 100% of it

1-We Generate the invoices with no real data to be sure that the json files match 100% as the invoice image 

2-It is hard to get real invoices 

3-The system is trust because we knew the answer from the beginning so when we test and have an error we really know where is the error 

## Day 2
Goal: first real extraction + validator rule 1

1- The extractor sends the image to the model via API.
2- The model converts this image to text, follows the schema style, and sends it to the extractor as JSON text.
3- The extractor validates this text with Pydantic and turns it into an Invoice object.
4- try_one.py saves the Invoice object as a JSON file.

I have built an invoice extractor that extracts the invoice information from an image using the Gemini model.
I also built a diff tool that compares the extracted invoice with the real JSON invoice, to see the differences or make sure they are completely the same.
I also built a validator that checks whether the extracted invoice is consistent with itself (for now: the sum of the line totals must equal the subtotal). It does not need the real JSON, but it cannot tell if the invoice is correct.

The difference between free-text responses and structured outputs is that free-text responses may come back in a broken shape (missing fields, extra text, invalid JSON). With structured outputs, the shape is guaranteed, so we can check the values automatically. But the values themselves can still be wrong, so we still need diff and the validator.

## Day 3
Goal: validator complete, evaluation numbers on 30 invoices

wrong invoices flagged by validator: 4/9
correct invoices flagged by mistake: 0/21

The completely correct invoice mean that the extractor have extract the invoice image exactly as it is without any mistake
The validator can never catch errors that doesn't have a rule or have a rule but doesn't break the math "like 1 cent error or text error" because it has no ground truth: it only checks that the invoice is consistent with itself, not that it is correct.

## Day 4
Goal: scanned invoices, clean vs scanned numbers, one controlled experiment

The difference between the clean invoices and the scanned invoices is small.
In fact, in some places the scanned invoices were more accurate than the clean ones, but the difference was only 1 invoice.
I ran the same test twice without any change and the result changed by 1 invoice, so the noise is ±1 invoice. This means the difference between clean and scanned is just noise, not a real change.
We tried changing the prompt to see if the problem came from the scanning or from reading Arabic numbers, but it didn't help at all. I think the problem is in two things:
the model is weak, and the digits are too small to read.

## Day 5
Goal: compare two models, write the decision, build POST /extract

Decision rule: I will choose the cheaper model if its fully-correct rate is within the noise I measured on day 4; otherwise the stronger one.
The model : Gemini flash lite 3.8 
Why : the other one have a usage limit 20 invoice a day
When I would switch : when i activate the payment
Next idea : just use Gemini flash lite

"I skipped steps 5.2 to 5.4 because the free tier of the Gemini API allows only 20 requests per day for the Flash models, and I did not enable billing. My attempt with gemini-3.8-flash failed on 17 of 30 invoices."

## Day 6
Goal: README, clean-clone test, public repo, video, first applications



## Day 7
Goal: review, KPIs, pitch, week 2 handoff



# Week 2
Goal: store, review, containerize and deploy the extractor; measure it on real invoices.

## Day 1
Goal: postgres in docker, SQL basics, ask for real invoices
