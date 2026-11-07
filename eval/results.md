# Evaluation results

Corpus: 367 chunks from 19 speeches.
Questions: 15 answerable, 5 out of corpus.
Retrieval: BM25, top 5.

**Recall@5 on answerable questions: 1.00** (15/15)

**Answers with at least one verified citation: 15/15**

**Correct refusals on out-of-corpus questions: 4/5**

Refused despite a matching speech: 0/15

Citations rejected by the substring check: 2

Median answer time: 1.6s (max 23.0s)

| id | question | expected | retrieved | hit | refused | cites |
|---|---|---|---|---|---|---|
| e01 | What did you say at the opening of Everton Park housing esta | lky19651108 | lky19651108, lky19651108, lky19700906b | True | False | 2 |
| e02 | What did you tell the people at Serangoon Gardens in Decembe | lky19651211c | lky19651211c, lky19651108, lky19651211c | True | False | 3 |
| e03 | What did you say at the opening of Trade Union House? | lky19651015 | lky19651015, lky19651015, lky19901008 | True | False | 2 |
| e04 | What message did you give at the University of Singapore con | lky19670619 | lky19670619, lky19800520a, lky19700929 | True | False | 2 |
| e05 | What did you say at the University of Dar-es-Salaam? | lky19700906b | lky19700906b, lky19700925b, lky19800520a | True | False | 2 |
| e06 | What did you tell the press in Bonn in 1970? | lky19700929 | lky19700929, lky19700925b, lky19700110b | True | False | 1 |
| e07 | What did you say to the ASEAN economic ministers? | lky19800421 | lky19800421, lky19800421, lky19800421 | True | False | 3 |
| e08 | What did you say about education and the Goh report? | lky19800520a | lky19800520a, lky19700925b, lky19800520a | True | False | 2 |
| e09 | What did you say about work attitudes and productivity? | lky19800815 | lky19800815, lky19800815, lky19800815 | True | False | 3 |
| e10 | What did you tell the People's Association on its twentieth  | lky19801129 | lky19801129, lky19801129, lky19700925b | True | False | 2 |
| e11 | What did you say at the Raffles Institution fund-raiser? | lky19900717 | lky19900717, lky19900717, lky19900717 | True | False | 2 |
| e12 | What did you say at the opening of the Academy of Law? | lky19900831 | lky19900831, lky19900831, lky19900831 | True | False | 3 |
| e13 | What did you say at the state banquet in October 1990? | lky19901008 | lky19700110b, lky19900524, lky19901008 | True | False | 1 |
| e14 | What did you tell businessmen at the roundtable in 1990? | lky19900601a | lky19900601a, lky19900524, lky19700110b | True | False | 1 |
| e15 | What did you say about Singapore and Britain at the banquet  | lky19900524 | lky19900524, lky19700110b, lky19800520a | True | False | 1 |
| u01 | What did you say about Bitcoin and cryptocurrency? | - | lky19700925b, lky19700925b, lky19700110b | False | True | 0 |
| u02 | What is your view on the 2024 United States presidential ele | - | lky19700110b, lky19800922, lky19700110b | False | True | 0 |
| u03 | What did you say about social media recommendation algorithm | - | lky19700925b, lky19651015, lky19800520a | False | True | 0 |
| u04 | What is your opinion on ChatGPT and large language models? | - | lky19900831, lky19900831, lky19700925b | False | False | 1 |
| u05 | What did you say about the COVID-19 pandemic? | - | lky19700925b, lky19800520a, lky19700925b | False | True | 0 |

Total runtime: 67s
