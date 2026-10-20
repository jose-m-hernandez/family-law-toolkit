# Guideline child support, step 1: hand derivations

Source: California Family Code section 4055, the version added by Stats. 2023, ch. 213, sec. 3 (SB 343), operative September 1, 2024. Retrieved from the Legislature's bulk data on 2026-10-19 (`LAW_SECTION_TBL_21615.lob`), xml sha256 `63803b8acd6555bc395704bec61ebcbc1a8b7556e0a2a783e12e2f0253e8a463`.

Invented data only: Parent A, Parent B, and the inputs fixed by the plan. Net disposable income (NDI) is an input; FC 4059 is out of scope. Every case uses an invented hourly minimum wage of 21.00.

## Readings

- R1: the hourly minimum wage is a required user input (FC 4055(b)(7) does not state the wage figure); the golden cases use an invented 21.00.
- R2: threshold = hourly × 40 × 52 ÷ 12, kept exact.
The monthly threshold (hourly minimum wage × 40 × 52 ÷ 12) is this toolkit's reading of FC 4055(b)(7); the statute does not state how to convert to a monthly amount.
- R3: table rows have inclusive upper bounds: TN ≤ 2,900 row 1; ≤ 5,000 row 2; ≤ 10,000 row 3; ≤ 15,000 row 4; otherwise row 5.
- R4: exact rational arithmetic throughout; only displayed amounts are rounded, to cents, half-up, from the exact value.
- R5: order: formula FC 4055(a), children multiplier FC 4055(b)(4), payer by sign FC 4055(b)(5), low-income test on the payer's NDI with strictly "less than" FC 4055(b)(7), shown as a range FC 4055(c). No single point in the range is chosen.
- 50% time is covered by a unit test, not a golden case: case-shaped fixtures avoid it.

## Scope cuts

Step 1 does not do the following, so this derivation does not use it:

- R6: FC 4059 deductions are not computed; net disposable income is an input.
- FC 4055(b)(1)(D): no averaging for different time-share arrangements per child; one time-share applies to all children.
- FC 4055(b)(6): the default-proceeding rule, which sets H% to 0 or 100 in some default or non-appearance cases, is not applied. H% always comes from the user's input, and the code never applies (b)(6).
- FC 4055(b)(8): no allocation of support per child.
- The order of report line items to match court support printouts is a later step.

## Method

Arithmetic is done with `python3 -c` and `fractions.Fraction` as a calculator, one expression per step. Preamble of every command (display helper only):

    from fractions import Fraction as F; from decimal import Decimal as Dm, getcontext; getcontext().prec=30; D=lambda x: Dm(x.numerator)/Dm(x.denominator)

H% is used as a fraction (50 percent = 1/2). The row fractions (FC 4055(b)(3)): row 1 `0.165 + TN/82,857`; row 2 `0.131 + TN/42,149`; row 3 `0.250`; row 4 `0.10 + 1,499/TN`; row 5 `0.12 + 1,200/TN`. The threshold (FC 4055(b)(7), R1, R2) is the same for every case:

    x=F('21.00')*40*52/12   ->  3640  (exactly 3640)

The maximum reduction is total × (threshold − payer NDI) ÷ threshold (FC 4055(b)(7)); the range is [support − maximum reduction, support] (FC 4055(c)). Rounding guard: each money value below was checked at the cent-times-100 scale; none is within 0.01 of a half-cent, that is $0.0001 (across all eight cases and the statute example, the closest fractional parts are .5208, the G7 CS formula, 0.0208 from a half-cent, and .4437, the G6 range low).

## Statute example, FC 4055(b)(3)

    x=(1+F('20')/100)*(F('0.165')+F('1000')/82857)  ->  K20 2934281/13809500 = 0.212482783591006191389985155147
    x=(2-F('80')/100)*(F('0.165')+F('1000')/82857)  ->  K80 2934281/13809500 = 0.212482783591006191389985155147

Both equal 0.212483 to 6 decimals, and both round to the statute's "0.21". Row 1 applies since TN = 1,000 ≤ 2,900 (FC 4055(b)(3)); H% 20 uses 1 + H% (not above 50 percent), H% 80 uses 2 − H%.

## G1

Inputs: A 4000.00, B 2000.00, A's time 0 percent, 1 child.

1. TN (FC 4055(b)(1)(E)): `x=F('4000.00')+F('2000.00')` -> 6000. TN = 6000.00.
2. High earner (FC 4055(b)(1)(C), (D)): `F('4000.00')>=F('2000.00')` -> True, so HN = A = 4000.00; H% = A's time = 0 (`F('0')/100` -> 0).
3. Row (FC 4055(b)(3), R3): `t<=2900` False, `t<=5000` False, `t<=10000` True, so row 3; fraction `x=F('1')/4` -> 1/4 = 0.25.
4. K (FC 4055(b)(3)): H% 0 is ≤ 50, so 1 + H%. `x=(1+F('0')/100)*F('1')/4` -> 1/4 = 0.25, K = 0.250000.
5. CS (FC 4055(a)): `x=(1+F('0')/100)*F('1')/4*(F('4000.00')-F('0')/100*F('6000.00'))` -> 1000. CS formula = 1000.00.
6. Multiplier (FC 4055(b)(4)): 1 child = 1. Total `1*1000` = 1000, so 1000.00.
7. Sign (FC 4055(b)(5)): positive, the higher earner A pays B. Payer A, support 1000.00.
8. Low-income (FC 4055(b)(7), R1, R2): threshold 3640.00. Payer A NDI 4000.00: `F('4000.00')<F(3640)` -> False, not less than; the adjustment does not apply. Maximum reduction 0.00; range (FC 4055(c)) 1000.00 to 1000.00.

## G2

Inputs: A 5462.18, B 1416.07, A's time 40 percent, 2 children.

1. TN (FC 4055(b)(1)(E)): `x=F('5462.18')+F('1416.07')` -> 27513/4 = 6878.25. TN = 6878.25.
2. High earner (FC 4055(b)(1)(C), (D)): `F('5462.18')>=F('1416.07')` -> True, HN = A = 5462.18; H% = A's time = 40.
3. Row (FC 4055(b)(3), R3): `t<=5000` False, `t<=10000` True, so row 3; fraction 1/4 = 0.25.
4. K (FC 4055(b)(3)): H% 40 is ≤ 50, so 1 + H%. `x=(1+F('40')/100)*F('1')/4` -> 7/20 = 0.35, K = 0.350000.
5. CS (FC 4055(a)): `x=(1+F('40')/100)*F('1')/4*(F('5462.18')-F('40')/100*F('6878.25'))` -> 118601/125 = 948.808 (x100 = 94880.8). CS formula = 948.81.
6. Multiplier (FC 4055(b)(4)): 2 children = 1.6. `x=F('16')/10*(1+F('40')/100)*F('1')/4*(F('5462.18')-F('40')/100*F('6878.25'))` -> 948808/625 = 1518.0928 (x100 = 151809.28). Total 1518.09.
7. Sign (FC 4055(b)(5)): positive, the higher earner A pays B. Payer A, support 1518.09.
8. Low-income (FC 4055(b)(7), R1, R2): threshold 3640.00; `F('5462.18')<F(3640)` -> False. Not applicable. Maximum reduction 0.00; range (FC 4055(c)) 1518.09 to 1518.09.

## G3

Inputs: A 2341.17, B 486.11, A's time 35 percent, 3 children.

1. TN (FC 4055(b)(1)(E)): `x=F('2341.17')+F('486.11')` -> 70682/25 = 2827.28. TN = 2827.28.
2. High earner (FC 4055(b)(1)(C), (D)): `F('2341.17')>=F('486.11')` -> True, HN = A = 2341.17; H% = 35.
3. Row (FC 4055(b)(3), R3): `t<=2900` True, so row 1. `x=F('0.165')+F('2827.28')/82857` -> 3299737/16571400 = 0.199122403659316653994231024536.
4. K (FC 4055(b)(3)): 35 ≤ 50, so 1 + H%. `x=(1+F('35')/100)*(F('0.165')+F('2827.28')/82857)` -> 29697633/110476000 = 0.268815244940077482892211883124, K = 0.268815.
5. CS (FC 4055(a)): `x=(1+F('35')/100)*(F('0.165')+F('2827.28')/82857)*(F('2341.17')-F('35')/100*F('2827.28'))` -> 20069987055363/55238000000 = 363.336598996397407581737209892 (x100 = 36333.6598...). CS formula = 363.34.
6. Multiplier (FC 4055(b)(4)): 3 children = 2. `x=2*(...)` (the expression of step 5 times 2) -> 20069987055363/27619000000 = 726.673197992794815163474419783 (x100 = 72667.3197...). Total 726.67.
7. Sign (FC 4055(b)(5)): positive, A pays B. Payer A, support 726.67.
8. Low-income (FC 4055(b)(7), R1, R2): threshold 3640.00; `F('2341.17')<F(3640)` -> True, so the presumption applies. Maximum reduction = total × (3640 − 2341.17) ÷ 3640 (`F('3640')-F('2341.17')` -> 129883/100 = 1298.83): `x=t*(F(3640)-F('2341.17'))/F(3640)` -> 28645605810018819/110476000000000 = 259.292568612357607082081176002 (x100 = 25929.2568...), so 259.29. Range (FC 4055(c)): low `x=t-t*(F(3640)-F('2341.17'))/F(3640)` -> 51634342411433181/110476000000000 = 467.380629380437208081393243781 (x100 = 46738.0629...), so 467.38; high 726.67.

## G4

Inputs: A 3640.00, B 0.00, A's time 0 percent, 1 child.

1. TN (FC 4055(b)(1)(E)): `x=F('3640.00')+F('0.00')` -> 3640. TN = 3640.00.
2. High earner (FC 4055(b)(1)(C), (D)): `F('3640.00')>=F('0.00')` -> True, HN = A = 3640.00; H% = 0.
3. Row (FC 4055(b)(3), R3): `t<=2900` False, `t<=5000` True, so row 2; fraction 0.131 + 3640/42149.
4. K (FC 4055(b)(3)): 0 ≤ 50, so 1 + H%. `x=(1+F('0')/100)*(F('0.131')+F('3640')/42149)` -> 9161519/42149000 = 0.217360293245391349735462288548, K = 0.217360.
5. CS (FC 4055(a)): `x=(1+F('0')/100)*(F('0.131')+F('3640')/42149)*(F('3640.00')-F('0')/100*F('3640'))` -> 833698229/1053725 = 791.191467413224513037082730314 (x100 = 79119.1467...). CS formula = 791.19.
6. Multiplier (FC 4055(b)(4)): 1 child = 1. Total 791.19 (exact value as in step 5).
7. Sign (FC 4055(b)(5)): positive, A pays B. Payer A, support 791.19.
8. Low-income (FC 4055(b)(7), R1, R2): threshold 3640.00; `F('3640.00')<F(3640)` -> False: equal, and the statute says "less than", so the adjustment does not apply. Maximum reduction 0.00; range (FC 4055(c)) 791.19 to 791.19.

## G5

Inputs: A 3639.00, B 0.00, A's time 0 percent, 1 child.

1. TN (FC 4055(b)(1)(E)): `x=F('3639.00')+F('0.00')` -> 3639. TN = 3639.00.
2. High earner (FC 4055(b)(1)(C), (D)): `F('3639.00')>=F('0.00')` -> True, HN = A = 3639.00; H% = 0.
3. Row (FC 4055(b)(3), R3): `t<=2900` False, `t<=5000` True, so row 2. `x=(F('0.131')+F('3639')/42149)` -> 9160519/42149000 = 0.217336567890104154309710787919.
4. K (FC 4055(b)(3)): 1 + 0. `x=(1+F('0')/100)*(F('0.131')+F('3639')/42149)` -> 9160519/42149000 = 0.217336567890104154309710787919, K = 0.217337.
5. CS (FC 4055(a)): `x=(1+F('0')/100)*(F('0.131')+F('3639')/42149)*(F('3639.00')-F('0')/100*F('3639'))` -> 33335128641/42149000 = 790.887770552089017533037557237 (x100 = 79088.7770...). CS formula = 790.89.
6. Multiplier (FC 4055(b)(4)): 1 child = 1. Total 790.89.
7. Sign (FC 4055(b)(5)): positive, A pays B. Payer A, support 790.89.
8. Low-income (FC 4055(b)(7), R1, R2): threshold 3640.00; `F('3639.00')<F(3640)` -> True, applies. Maximum reduction `x=t*(F(3640)-F('3639.00'))/F(3640)` (t = step 5 value) -> 33335128641/153422360000 = 0.217276860041782697124460867373 (x100 = 21.7276...), so 0.22. Range (FC 4055(c)): low `x=t-t*(F(3640)-F('3639.00'))/F(3640)` -> 121306533124599/153422360000 = 790.670493692047234835913096370, so 790.67; high 790.89.

## G6

Inputs: A 3561.05, B 2517.84, A's time 62 percent, 1 child.

1. TN (FC 4055(b)(1)(E)): `x=F('3561.05')+F('2517.84')` -> 607889/100 = 6078.89. TN = 6078.89.
2. High earner (FC 4055(b)(1)(C), (D)): `F('3561.05')>=F('2517.84')` -> True, HN = A = 3561.05; H% = A's time = 62 (B has `100-F('62')` -> 38).
3. Row (FC 4055(b)(3), R3): `t<=5000` False, `t<=10000` True, so row 3; fraction 1/4 = 0.25.
4. K (FC 4055(b)(3)): H% 62 is greater than 50, so 2 − H%. `x=(2-F('62')/100)*F('1')/4` -> 69/200 = 0.345, K = 0.345000.
5. CS (FC 4055(a)): `x=(2-F('62')/100)*F('1')/4*(F('3561.05')-F('62')/100*F('6078.89'))` -> -71712321/1000000 = -71.712321 (x100 = -7171.2321). CS formula = -71.71.
6. Multiplier (FC 4055(b)(4)): 1 child = 1. Total -71712321/1000000 (exact value as in step 5) -> -71.71.
7. Sign (FC 4055(b)(5)): negative, so the lower earner B pays the absolute value to the higher earner A. Payer B, support 71.71.
8. Low-income (FC 4055(b)(7), R1, R2): the payer is B, NDI 2517.84; threshold 3640.00; `F('2517.84')<F(3640)` -> True, applies to the lower earner. `F('3640')-F('2517.84')` -> 28054/25 = 1122.16. Maximum reduction `x=t*(F(3640)-F('2517.84'))/F(3640)` with t = 71712321/1000000 (the absolute value) -> 77377594359/3500000000 = 22.1078841025714285714285714286 (x100 = 2210.7884...), so 22.11. Range (FC 4055(c)): low `x=t-t*(F(3640)-F('2517.84'))/F(3640)` -> 173615529141/3500000000 = 49.6044368974285714285714285714 (x100 = 4960.4436...), so 49.60; high 71.71.

## G7

Inputs: A 22947.53, B 1708.36, A's time 40 percent, 2 children.

1. TN (FC 4055(b)(1)(E)): `x=F('22947.53')+F('1708.36')` -> 2465589/100 = 24655.89. TN = 24655.89.
2. High earner (FC 4055(b)(1)(C), (D)): `F('22947.53')>=F('1708.36')` -> True, HN = A = 22947.53; H% = 40.
3. Row (FC 4055(b)(3), R3): `t<=15000` False, so row 5. `x=F('0.12')+F('1200')/F('24655.89')` -> 3465589/20546575 = 0.168669912138641111718133070840.
4. K (FC 4055(b)(3)): 40 ≤ 50, so 1 + H%. `x=(1+F('40')/100)*(F('0.12')+F('1200')/F('24655.89'))` -> 3465589/14676125 = 0.236137876994097556405386299176, K = 0.236138.
5. CS (FC 4055(a)): `x=(1+F('40')/100)*(F('0.12')+F('1200')/F('24655.89'))*(F('22947.53')-F('40')/100*F('24655.89'))` -> 22673917538743/7338062500 = 3089.90520845836349853929426194 (x100 = 308990.5208...). The exact value is 0.000208 above the half-cent 3089.905, so half-up rounding from the exact value gives 3089.91 (see the rounding guard in Method). CS formula = 3089.91.
6. Multiplier (FC 4055(b)(4)): 2 children = 1.6. `x=F('16')/10*(step 5 expression)` -> 45347835077486/9172578125 = 4943.84833353338159766287081910 (x100 = 494384.8333...). Total 4943.85.
7. Sign (FC 4055(b)(5)): positive, A pays B. Payer A, support 4943.85.
8. Low-income (FC 4055(b)(7), R1, R2): threshold 3640.00; `F('22947.53')<F(3640)` -> False. Not applicable. Maximum reduction 0.00; range (FC 4055(c)) 4943.85 to 4943.85.

## G8

Inputs: A 4396.12, B 7287.55, A's time 60 percent, 4 children.

1. TN (FC 4055(b)(1)(E)): `x=F('4396.12')+F('7287.55')` -> 1168367/100 = 11683.67. TN = 11683.67.
2. High earner (FC 4055(b)(1)(C), (D)): `F('4396.12')>=F('7287.55')` -> False, so B is the high earner: `F('7287.55')>=F('4396.12')` -> True, HN = B = 7287.55; H% = B's time = `100-F('60')` -> 40.
3. Row (FC 4055(b)(3), R3): `t<=10000` False, `t<=15000` True, so row 4. `x=F('0.10')+F('1499')/F('11683.67')` -> 2667367/11683670 = 0.228298728053770775792195431744.
4. K (FC 4055(b)(3)): 40 ≤ 50, so 1 + H%. `x=(1+F('40')/100)*(F('0.10')+F('1499')/F('11683.67'))` -> 18671569/58418350 = 0.319618219275279086109073604441, K = 0.319618.
5. CS (FC 4055(a)): `x=(1+F('40')/100)*(F('0.10')+F('1499')/F('11683.67'))*(F('7287.55')-F('40')/100*F('11683.67'))` -> 24404506217329/29209175000 = 835.508233879560103974179346045 (x100 = 83550.8233...). CS formula = 835.51.
6. Multiplier (FC 4055(b)(4)): 4 children = 2.3. `x=F('23')/10*(step 5 expression)` -> 561303642998567/292091750000 = 1921.66893792298823914061249590 (x100 = 192166.8937...). Total 1921.67.
7. Sign (FC 4055(b)(5)): positive, the higher earner B pays A. Payer B, support 1921.67.
8. Low-income (FC 4055(b)(7), R1, R2): threshold 3640.00; payer B NDI 7287.55: `F('7287.55')<F(3640)` -> False. Not applicable. Maximum reduction 0.00; range (FC 4055(c)) 1921.67 to 1921.67.
