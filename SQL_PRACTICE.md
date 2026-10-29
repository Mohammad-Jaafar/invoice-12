# SQL Practice

## 1. How many invoices are there?
SELECT COUNT(*) FROM practice;
-- answer: 30

## 2. Top five most expensive invoices (file and total), most expensive first
SELECT file, total FROM practice ORDER BY total DESC LIMIT 5;
-- answer:
--  inv_008_mixed_classic | 61340.16
--  inv_007_ar_classic    | 52171.34
--  inv_006_en_classic    | 37005.07
--  inv_015_en_modern     | 32411.28
--  inv_012_en_classic    | 27761.32

## 3. How many invoices have a total above 10000?
SELECT COUNT(*) FROM practice WHERE total > 10000;
-- answer: 14

## 4. Average number of items per invoice (two decimals)
SELECT ROUND(AVG(items), 2) FROM practice;
-- answer: 3.43

## 5. How many invoices per language?
SELECT split_part(file, '_', 3) AS lang, COUNT(*) FROM practice GROUP BY lang ORDER BY lang;
-- answer:
--  ar    | 10
--  en    | 10
--  mixed | 10

## 6. Total VAT per month
SELECT EXTRACT(MONTH FROM invoice_date) AS month, SUM(vat) FROM practice GROUP BY month ORDER BY month;
-- answer:
--   1 | 1543.39
--   2 |  138.22
--   3 |  725.35
--   4 | 3466.55
--   5 | 2806.95
--   6 |  597.24
--   7 |  845.58
--   8 | 1230.86
--   9 | 2920.96
--  10 | 1604.97
--  11 | 1049.92
--  12 | 3860.28

## 7. Validator in SQL: how many invoices where subtotal + vat is not equal to total?
SELECT COUNT(*) FROM practice WHERE subtotal + vat <> total;
-- answer: 0

## 8. Suppliers with more than one invoice, and how many each
SELECT supplier, COUNT(*) AS invoices FROM practice GROUP BY supplier HAVING COUNT(*) > 1 ORDER BY invoices DESC;
-- answer:
--  Crescent Printing Press  | 4
--  Sharjah Medical Supplies | 4
--  وردة الصحراء للتموين     | 4
--  Desert Rose Catering     | 4
--  Blue Wave Logistics      | 3
--  الإمارات للحلول التقنية  | 2
--  Oasis Cleaning Services  | 2

## 9. Break invoice 1 on purpose, run query 7 again, then fix it
UPDATE practice SET total = total + 10 WHERE id = 1;
-- answer: UPDATE 1
SELECT COUNT(*) FROM practice WHERE subtotal + vat <> total;
-- answer: 1
UPDATE practice SET total = total - 10 WHERE id = 1;
-- answer: UPDATE 1
SELECT COUNT(*) FROM practice WHERE subtotal + vat <> total;
-- answer: 0

## 10. Delete all rows inside a transaction, then roll back
BEGIN;
DELETE FROM practice;
-- answer: DELETE 30
SELECT COUNT(*) FROM practice;
-- answer: 0
ROLLBACK;
SELECT COUNT(*) FROM practice;
-- answer: 30
