# Guideline child support, step 2: hand derivations for the per-child allocation

Source: California Family Code section 4055, the version added by Stats. 2023, ch. 213, sec. 3 (SB 343), operative September 1, 2024. Retrieved from the Legislature's bulk data on 2026-10-19 (`LAW_SECTION_TBL_21615.lob`), xml sha256 `63803b8acd6555bc395704bec61ebcbc1a8b7556e0a2a783e12e2f0253e8a463`. The statute text is `docs/sources/fc4055.xml`; short phrases are quoted from `docs/sources/fc4055.txt`.

Invented data only: Parent A, Parent B, and the inputs fixed by the plan. Net disposable income (NDI) is an input; FC 4059 is out of scope. Every case uses an invented hourly minimum wage of 21.00 and sets the same-time-sharing-arrangement answer to yes.

## Method

Arithmetic is done with `python3 -I -c` and `fractions.Fraction` as a calculator, one expression per step, never importing the calculator. Every command starts with the shell variable `P` (display helper only):

    P="from fractions import Fraction as F; from decimal import Decimal as Dm, getcontext; getcontext().prec=30; D=lambda x: Dm(x.numerator)/Dm(x.denominator)"

Each printed result is the exact fraction, then the value times 100 (so the cent boundary is visible), then, for money, the displayed amount rounded half-up from the exact value (R4); negative amounts are rounded by magnitude. A carried exact value is written as `F('p/q')`, the exact result of the step named. H% is used as a fraction (50 percent = 1/2). Row fractions (FC 4055(b)(3)): row 1 `0.165 + TN/82,857`; row 2 `0.131 + TN/42,149`; row 3 `0.250`; row 4 `0.10 + 1,499/TN`; row 5 `0.12 + 1,200/TN`. Multipliers (FC 4055(b)(4)): 1, 1.6, 2, 2.3, 2.5 for 1 to 5 children.

Rounding guard: every rounded money value was checked at the cent-times-100 scale; none is within 0.01 of a half-cent, that is $0.0001.

## Readings

- R1: the hourly minimum wage is a required user input (FC 4055(b)(7) does not state the wage figure); the golden cases use an invented 21.00.
- R2: threshold = hourly × 40 × 52 ÷ 12, kept exact.
The monthly threshold (hourly minimum wage × 40 × 52 ÷ 12) is this toolkit's reading of FC 4055(b)(7); the statute does not state how to convert to a monthly amount.
- R3: table rows have inclusive upper bounds: TN ≤ 2,900 row 1; ≤ 5,000 row 2; ≤ 10,000 row 3; ≤ 15,000 row 4; otherwise row 5.
- R4: exact rational arithmetic throughout; only displayed amounts are rounded, to cents, half-up, from the exact value.
- R5: order: formula FC 4055(a), children multiplier FC 4055(b)(4), payer by sign FC 4055(b)(5), low-income test on the payer's NDI with strictly "less than" FC 4055(b)(7), shown as a range FC 4055(c). No single point in the range is chosen.
- High earner: Parent A is the high earner when A's NDI is greater than or equal to B's (FC 4055(b)(1)(C)).
- R7 When (b)(7) applies, the (b)(8) allocation is shown at each end of the range and never for a point inside it; the top end allocates the unadjusted amounts for 1..n children, the bottom end the amounts reduced by the maximum (b)(7) fraction. This is a reading, because (b)(7) never says the (b)(8) amounts are adjusted.
- R8 Each cumulative amount (1..n children) is computed exactly and displayed rounded half-up to the cent; each per-child amount is the difference between consecutive displayed cumulative amounts, so the per-child amounts add to the shown total.
Rounding the amount for each number of children to the cent before taking the FC 4055(b)(8) differences is this toolkit's reading; FC 4055 does not say how to round.
Applying the largest FC 4055(b)(7) reduction to the amount for each number of children is this toolkit's reading; the statute does not say that the (b)(8) amounts are adjusted.
- R9 Per-child amounts are labelled by position only, youngest to oldest; no names, ages or dates.
- R10 (b)(8) does not apply when the children have different time-sharing arrangements; the allocation is computed only when the user states one shared arrangement (--same-time-sharing-arrangement yes), and every case here sets that flag to yes.
- R11 The allocation is the one used when the court orders nothing else; a negative result allocates the absolute amount the lower earner pays, shown positive; cumulative amounts are shown before the differences; the limit stays 1 to 10 children.
- R12 (General Counsel, 2026-11-04, D1c; beside R10, which is unchanged and still governs a single share of time) When one share of time is entered per child: (1) if the percentages differ, the children do not share one time-sharing arrangement, so no (b)(8) allocation is shown whatever --same-time-sharing-arrangement says, and the report says (b)(8) does not apply; (2) if they differ and --same-time-sharing-arrangement yes is also given, the inputs contradict each other, and the calculator stops with an error naming both; (3) if all the percentages are equal, the R10 confirmation is still required before the allocation is shown, because equal percentages do not establish the same arrangement (D1b); without it the report behaves as with a single share of time.
- R13 (General Counsel, 2026-11-04, D1a) Under FC 4055(b)(1)(D), when one share of time is entered per child, H% is the arithmetic mean of the high earner's per-child percentages, each child counted once: their sum divided by the number of children. FC 4055 gives no weights and no rounding rule for the average, so the mean is kept exact and used unrounded everywhere H% appears, including the (b)(3) choice for K and CS = K[HN - (H%)(TN)]; only the displayed H% is rounded, to two decimals, half-up (R4). Averaging Parent A's percentages and then taking the high earner's share gives the same H% as the other order; that is arithmetic, not a reading.

## S1

Inputs: A 6919.09, B 2255.71, A's time 35 percent, 2 children, same time-sharing arrangement (yes). Hourly minimum wage 21.00.

1. TN (FC 4055(b)(1)(E)):

    python3 -I -c "$P; x=F('6919.09')+F('2255.71'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 45874/5 917480 9174.80

2. High earner (FC 4055(b)(1)(C), (D)): A is the high earner when A's NDI is at least B's.

    python3 -I -c "$P; print(F('6919.09')>=F('2255.71'))"
    -> True

   So HN = A = 6919.09 and H% = A's time = 35 (FC 4055(b)(1)(D)).

3. Row (FC 4055(b)(3), R3): TN 9174.80 selects row 3.

   Row fraction (FC 4055(b)(3)):

    python3 -I -c "$P; x=F('1')/4; print(x, D(x*100))"
    -> 1/4 25

4. K (FC 4055(b)(3)): H% 35 is at most 50, so 1 + H%.

    python3 -I -c "$P; x=(1+F('35')/100)*(F('1')/4); print(x, D(x*100))"
    -> 27/80 33.75

   K = 0.337500 (rounded to 6 decimals, half-up).

5. CS (FC 4055(a)): high earner is A.

    python3 -I -c "$P; x=(1+F('35')/100)*(F('1')/4)*(F('6919.09')-F('35')/100*F('45874/5')); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 10011357/8000 125141.9625 1251.42

   CS formula = 1251.42.

6. Multiplier (FC 4055(b)(4)): 2 children = 1.6. Total for 2 children:

    python3 -I -c "$P; x=F('1.6')*F('10011357/8000'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 10011357/5000 200227.14 2002.27

   Total = 2002.27.

7. Sign (FC 4055(b)(5)): positive, so the high earner A pays the lower earner B. Payer A, support 2002.27 (the absolute value of the total).

8. Low-income (FC 4055(b)(7), R1, R2): threshold:

    python3 -I -c "$P; x=F('21.00')*40*52/12; print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 3640 364000 3640.00

   Payer A NDI 6919.09, strictly less than the threshold (FC 4055(b)(7)):

    python3 -I -c "$P; print(F('6919.09')<F(3640))"
    -> False

   Not applicable. Maximum reduction 0.00; range (FC 4055(c)) 2002.27 to 2002.27.

### S1: allocation under FC 4055(b)(8)

- Amount for 1 child (FC 4055(b)(8), (b)(4) multiplier 1):

    python3 -I -c "$P; x=F('1')*F('10011357/8000'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 10011357/8000 125141.9625 1251.42

- Amount for 2 children (FC 4055(b)(8), (b)(4) multiplier 1.6):

    python3 -I -c "$P; x=F('1.6')*F('10011357/8000'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 10011357/5000 200227.14 2002.27

- Per-child amounts (FC 4055(b)(8)), youngest first, differences of the displayed amounts (R8, R9):

    python3 -I -c "from decimal import Decimal as Dm; print([Dm('1251.42')]+[Dm(y)-Dm(x) for x,y in zip(['1251.42'],['2002.27'])])"
    -> [Decimal('1251.42'), Decimal('750.85')]

- Sum against the shown support (FC 4055(b)(8)):

    python3 -I -c "from decimal import Decimal as Dm; print(sum([Dm('1251.42'), Dm('750.85')]))"
    -> 2002.27, equal to the shown 2002.27.

Rounding guard: 6 rounded money values in this case; the closest to a half-cent is 0.36 of a cent-times-100 unit away (limit 0.01).

## S2

Inputs: A 8208.09, B 5127.40, A's time 65 percent, 3 children, same time-sharing arrangement (yes). Hourly minimum wage 21.00.

1. TN (FC 4055(b)(1)(E)):

    python3 -I -c "$P; x=F('8208.09')+F('5127.40'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 1333549/100 1333549 13335.49

2. High earner (FC 4055(b)(1)(C), (D)): A is the high earner when A's NDI is at least B's.

    python3 -I -c "$P; print(F('8208.09')>=F('5127.40'))"
    -> True

   So HN = A = 8208.09 and H% = A's time = 65 (FC 4055(b)(1)(D)).

3. Row (FC 4055(b)(3), R3): TN 13335.49 selects row 4.

   Row fraction (FC 4055(b)(3)):

    python3 -I -c "$P; x=F('0.10')+F('1499')/F('1333549/100'); print(x, D(x*100))"
    -> 2832549/13335490 21.2406818197156609918345707582

4. K (FC 4055(b)(3)): H% 65 is greater than 50, so 2 - H%.

    python3 -I -c "$P; x=(2-F('65')/100)*(F('0.10')+F('1499')/F('1333549/100')); print(x, D(x*100))"
    -> 76478823/266709800 28.6749204566161423389766705235

   K = 0.286749 (rounded to 6 decimals, half-up).

5. CS (FC 4055(a)): high earner is A.

    python3 -I -c "$P; x=(2-F('65')/100)*(F('0.10')+F('1499')/F('1333549/100'))*(F('8208.09')-F('65')/100*F('1333549/100')); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> -70357228570611/533419600000 -13189.8468992536082288689804424 -131.90

   CS formula = -131.90.

6. Multiplier (FC 4055(b)(4)): 3 children = 2. Total for 3 children:

    python3 -I -c "$P; x=F('2')*F('-70357228570611/533419600000'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> -70357228570611/266709800000 -26379.6937985072164577379608848 -263.80

   Total = -263.80.

7. Sign (FC 4055(b)(5)): negative, so the lower earner B pays the absolute value of the amount to the high earner A. Payer B, support 263.80 (the absolute value of the total).

8. Low-income (FC 4055(b)(7), R1, R2): threshold:

    python3 -I -c "$P; x=F('21.00')*40*52/12; print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 3640 364000 3640.00

   Payer B NDI 5127.40, strictly less than the threshold (FC 4055(b)(7)):

    python3 -I -c "$P; print(F('5127.40')<F(3640))"
    -> False

   Not applicable. Maximum reduction 0.00; range (FC 4055(c)) 263.80 to 263.80.

### S2: allocation under FC 4055(b)(8)

- Amount for 1 child (FC 4055(b)(8), (b)(4) multiplier 1):

    python3 -I -c "$P; x=F('1')*F('70357228570611/533419600000'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 70357228570611/533419600000 13189.8468992536082288689804424 131.90

- Amount for 2 children (FC 4055(b)(8), (b)(4) multiplier 1.6):

    python3 -I -c "$P; x=F('1.6')*F('70357228570611/533419600000'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 70357228570611/333387250000 21103.7550388057731661903687079 211.04

- Amount for 3 children (FC 4055(b)(8), (b)(4) multiplier 2):

    python3 -I -c "$P; x=F('2')*F('70357228570611/533419600000'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 70357228570611/266709800000 26379.6937985072164577379608848 263.80

- Per-child amounts (FC 4055(b)(8)), youngest first, differences of the displayed amounts (R8, R9):

    python3 -I -c "from decimal import Decimal as Dm; print([Dm('131.90')]+[Dm(y)-Dm(x) for x,y in zip(['131.90', '211.04'],['211.04', '263.80'])])"
    -> [Decimal('131.90'), Decimal('79.14'), Decimal('52.76')]

- Sum against the shown support (FC 4055(b)(8)):

    python3 -I -c "from decimal import Decimal as Dm; print(sum([Dm('131.90'), Dm('79.14'), Dm('52.76')]))"
    -> 263.80, equal to the shown 263.80.

Rounding guard: 7 rounded money values in this case; the closest to a half-cent is 0.19379850 of a cent-times-100 unit away (limit 0.01).

## S3

Inputs: A 4459.28, B 523.82, A's time 40 percent, 5 children, same time-sharing arrangement (yes). Hourly minimum wage 21.00.

1. TN (FC 4055(b)(1)(E)):

    python3 -I -c "$P; x=F('4459.28')+F('523.82'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 49831/10 498310 4983.10

2. High earner (FC 4055(b)(1)(C), (D)): A is the high earner when A's NDI is at least B's.

    python3 -I -c "$P; print(F('4459.28')>=F('523.82'))"
    -> True

   So HN = A = 4459.28 and H% = A's time = 40 (FC 4055(b)(1)(D)).

3. Row (FC 4055(b)(3), R3): TN 4983.10 selects row 2.

   Row fraction (FC 4055(b)(3)):

    python3 -I -c "$P; x=F('0.131')+F('49831/10')/42149; print(x, D(x*100))"
    -> 10504619/42149000 24.9225817931623526062302782984

4. K (FC 4055(b)(3)): H% 40 is at most 50, so 1 + H%.

    python3 -I -c "$P; x=(1+F('40')/100)*(F('0.131')+F('49831/10')/42149); print(x, D(x*100))"
    -> 73532333/210745000 34.8916145104272936487223896178

   K = 0.348916 (rounded to 6 decimals, half-up).

5. CS (FC 4055(a)): high earner is A.

    python3 -I -c "$P; x=(1+F('40')/100)*(F('0.131')+F('49831/10')/42149)*(F('4459.28')-F('40')/100*F('49831/10')); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 4533341861783/5268625000 86044.1170472941232294953616930 860.44

   CS formula = 860.44.

6. Multiplier (FC 4055(b)(4)): 5 children = 2.5. Total for 5 children:

    python3 -I -c "$P; x=F('2.5')*F('4533341861783/5268625000'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 4533341861783/2107450000 215110.292618235308073738404233 2151.10

   Total = 2151.10.

7. Sign (FC 4055(b)(5)): positive, so the high earner A pays the lower earner B. Payer A, support 2151.10 (the absolute value of the total).

8. Low-income (FC 4055(b)(7), R1, R2): threshold:

    python3 -I -c "$P; x=F('21.00')*40*52/12; print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 3640 364000 3640.00

   Payer A NDI 4459.28, strictly less than the threshold (FC 4055(b)(7)):

    python3 -I -c "$P; print(F('4459.28')<F(3640))"
    -> False

   Not applicable. Maximum reduction 0.00; range (FC 4055(c)) 2151.10 to 2151.10.

### S3: allocation under FC 4055(b)(8)

- Amount for 1 child (FC 4055(b)(8), (b)(4) multiplier 1):

    python3 -I -c "$P; x=F('1')*F('4533341861783/5268625000'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 4533341861783/5268625000 86044.1170472941232294953616930 860.44

- Amount for 2 children (FC 4055(b)(8), (b)(4) multiplier 1.6):

    python3 -I -c "$P; x=F('1.6')*F('4533341861783/5268625000'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 4533341861783/3292890625 137670.587275670597167192578709 1376.71

- Amount for 3 children (FC 4055(b)(8), (b)(4) multiplier 2):

    python3 -I -c "$P; x=F('2')*F('4533341861783/5268625000'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 4533341861783/2634312500 172088.234094588246458990723386 1720.88

- Amount for 4 children (FC 4055(b)(8), (b)(4) multiplier 2.3):

    python3 -I -c "$P; x=F('2.3')*F('4533341861783/5268625000'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 104266862821009/52686250000 197901.469208776483427839331894 1979.01

- Amount for 5 children (FC 4055(b)(8), (b)(4) multiplier 2.5):

    python3 -I -c "$P; x=F('2.5')*F('4533341861783/5268625000'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 4533341861783/2107450000 215110.292618235308073738404233 2151.10

- Per-child amounts (FC 4055(b)(8)), youngest first, differences of the displayed amounts (R8, R9):

    python3 -I -c "from decimal import Decimal as Dm; print([Dm('860.44')]+[Dm(y)-Dm(x) for x,y in zip(['860.44', '1376.71', '1720.88', '1979.01'],['1376.71', '1720.88', '1979.01', '2151.10'])])"
    -> [Decimal('860.44'), Decimal('516.27'), Decimal('344.17'), Decimal('258.13'), Decimal('172.09')]

- Sum against the shown support (FC 4055(b)(8)):

    python3 -I -c "from decimal import Decimal as Dm; print(sum([Dm('860.44'), Dm('516.27'), Dm('344.17'), Dm('258.13'), Dm('172.09')]))"
    -> 2151.10, equal to the shown 2151.10.

Rounding guard: 9 rounded money values in this case; the closest to a half-cent is 0.03079122 of a cent-times-100 unit away (limit 0.01).

## S4

Inputs: A 2258.50, B 612.53, A's time 45 percent, 3 children, same time-sharing arrangement (yes). Hourly minimum wage 21.00.

1. TN (FC 4055(b)(1)(E)):

    python3 -I -c "$P; x=F('2258.50')+F('612.53'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 287103/100 287103 2871.03

2. High earner (FC 4055(b)(1)(C), (D)): A is the high earner when A's NDI is at least B's.

    python3 -I -c "$P; print(F('2258.50')>=F('612.53'))"
    -> True

   So HN = A = 2258.50 and H% = A's time = 45 (FC 4055(b)(1)(D)).

3. Row (FC 4055(b)(3), R3): TN 2871.03 selects row 1.

   Row fraction (FC 4055(b)(3)):

    python3 -I -c "$P; x=F('0.165')+F('287103/100')/82857; print(x, D(x*100))"
    -> 1102829/5523800 19.9650421811072088055324233318

4. K (FC 4055(b)(3)): H% 45 is at most 50, so 1 + H%.

    python3 -I -c "$P; x=(1+F('45')/100)*(F('0.165')+F('287103/100')/82857); print(x, D(x*100))"
    -> 31982041/110476000 28.9493111626054527680220138311

   K = 0.289493 (rounded to 6 decimals, half-up).

5. CS (FC 4055(a)): high earner is A.

    python3 -I -c "$P; x=(1+F('45')/100)*(F('0.165')+F('287103/100')/82857)*(F('2258.50')-F('45')/100*F('287103/100')); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 61823619941993/220952000000 27980.5658885156051993193091712 279.81

   CS formula = 279.81.

6. Multiplier (FC 4055(b)(4)): 3 children = 2. Total for 3 children:

    python3 -I -c "$P; x=F('2')*F('61823619941993/220952000000'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 61823619941993/110476000000 55961.1317770312103986386183424 559.61

   Total = 559.61.

7. Sign (FC 4055(b)(5)): positive, so the high earner A pays the lower earner B. Payer A, support 559.61 (the absolute value of the total).

8. Low-income (FC 4055(b)(7), R1, R2): threshold:

    python3 -I -c "$P; x=F('21.00')*40*52/12; print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 3640 364000 3640.00

   Payer A NDI 2258.50, strictly less than the threshold (FC 4055(b)(7)):

    python3 -I -c "$P; print(F('2258.50')<F(3640))"
    -> True

   Maximum reduction fraction (FC 4055(b)(7)), (3640 - payer NDI) / 3640:

    python3 -I -c "$P; x=(F(3640)-F('2258.50'))/F(3640); print(x, D(x*100))"
    -> 2763/7280 37.9532967032967032967032967033

   Maximum reduction = support x fraction:

    python3 -I -c "$P; x=F('61823619941993/110476000000')*F('2763/7280'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 1877128152744249/8838080000000 21239.0943818595102103624316594 212.39

   Range low (FC 4055(c)) = support - maximum reduction:

    python3 -I -c "$P; x=F('61823619941993/110476000000')-F('61823619941993/110476000000')*F('2763/7280'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 3068761442615191/8838080000000 34722.0373951717001882761866831 347.22

   Range (FC 4055(c)): 347.22 to 559.61.

### S4: allocation under FC 4055(b)(8)

**Top end of the range (R7).** Unadjusted amounts (FC 4055(b)(4), (b)(8)).

- Amount for 1 child (FC 4055(b)(8), (b)(4) multiplier 1):

    python3 -I -c "$P; x=F('1')*F('61823619941993/220952000000'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 61823619941993/220952000000 27980.5658885156051993193091712 279.81

- Amount for 2 children (FC 4055(b)(8), (b)(4) multiplier 1.6):

    python3 -I -c "$P; x=F('1.6')*F('61823619941993/220952000000'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 61823619941993/138095000000 44768.9054216249683189108946740 447.69

- Amount for 3 children (FC 4055(b)(8), (b)(4) multiplier 2):

    python3 -I -c "$P; x=F('2')*F('61823619941993/220952000000'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 61823619941993/110476000000 55961.1317770312103986386183424 559.61

- Per-child amounts (FC 4055(b)(8)), youngest first, differences of the displayed amounts (R8, R9):

    python3 -I -c "from decimal import Decimal as Dm; print([Dm('279.81')]+[Dm(y)-Dm(x) for x,y in zip(['279.81', '447.69'],['447.69', '559.61'])])"
    -> [Decimal('279.81'), Decimal('167.88'), Decimal('111.92')]

- Sum against the shown range high (FC 4055(b)(8)):

    python3 -I -c "from decimal import Decimal as Dm; print(sum([Dm('279.81'), Dm('167.88'), Dm('111.92')]))"
    -> 559.61, equal to the shown 559.61.

**Bottom end of the range (R7).** Amounts reduced by the maximum (b)(7) fraction (R7).

- Amount for 1 child (FC 4055(b)(8), (b)(4) multiplier 1):

    python3 -I -c "$P; x=F('1')*F('61823619941993/220952000000')*(1-F('2763/7280')); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 3068761442615191/17676160000000 17361.0186975858500941380933415 173.61

- Amount for 2 children (FC 4055(b)(8), (b)(4) multiplier 1.6):

    python3 -I -c "$P; x=F('1.6')*F('61823619941993/220952000000')*(1-F('2763/7280')); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 3068761442615191/11047600000000 27777.6299161373601506209493465 277.78

- Amount for 3 children (FC 4055(b)(8), (b)(4) multiplier 2):

    python3 -I -c "$P; x=F('2')*F('61823619941993/220952000000')*(1-F('2763/7280')); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 3068761442615191/8838080000000 34722.0373951717001882761866831 347.22

- Per-child amounts (FC 4055(b)(8)), youngest first, differences of the displayed amounts (R8, R9):

    python3 -I -c "from decimal import Decimal as Dm; print([Dm('173.61')]+[Dm(y)-Dm(x) for x,y in zip(['173.61', '277.78'],['277.78', '347.22'])])"
    -> [Decimal('173.61'), Decimal('104.17'), Decimal('69.44')]

- Sum against the shown range low (FC 4055(b)(8)):

    python3 -I -c "from decimal import Decimal as Dm; print(sum([Dm('173.61'), Dm('104.17'), Dm('69.44')]))"
    -> 347.22, equal to the shown 347.22.

Rounding guard: 12 rounded money values in this case; the closest to a half-cent is 0.06588851 of a cent-times-100 unit away (limit 0.01).

## S5

Inputs: A 12105.04, B 1639.79, A's time 60 percent, 4 children, same time-sharing arrangement (yes). Hourly minimum wage 21.00.

1. TN (FC 4055(b)(1)(E)):

    python3 -I -c "$P; x=F('12105.04')+F('1639.79'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 1374483/100 1374483 13744.83

2. High earner (FC 4055(b)(1)(C), (D)): A is the high earner when A's NDI is at least B's.

    python3 -I -c "$P; print(F('12105.04')>=F('1639.79'))"
    -> True

   So HN = A = 12105.04 and H% = A's time = 60 (FC 4055(b)(1)(D)).

3. Row (FC 4055(b)(3), R3): TN 13744.83 selects row 4.

   Row fraction (FC 4055(b)(3)):

    python3 -I -c "$P; x=F('0.10')+F('1499')/F('1374483/100'); print(x, D(x*100))"
    -> 2873483/13744830 20.9059188072897227539372986061

4. K (FC 4055(b)(3)): H% 60 is greater than 50, so 2 - H%.

    python3 -I -c "$P; x=(2-F('60')/100)*(F('0.10')+F('1499')/F('1374483/100')); print(x, D(x*100))"
    -> 20114381/68724150 29.2682863302056118555122180485

   K = 0.292683 (rounded to 6 decimals, half-up).

5. CS (FC 4055(a)): high earner is A.

    python3 -I -c "$P; x=(2-F('60')/100)*(F('0.10')+F('1499')/F('1374483/100'))*(F('12105.04')-F('60')/100*F('1374483/100')); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 38802069070051/34362075000 112921.204758592139735449619966 1129.21

   CS formula = 1129.21.

6. Multiplier (FC 4055(b)(4)): 4 children = 2.3. Total for 4 children:

    python3 -I -c "$P; x=F('2.3')*F('38802069070051/34362075000'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 892447588611173/343620750000 259718.770944761921391534125922 2597.19

   Total = 2597.19.

7. Sign (FC 4055(b)(5)): positive, so the high earner A pays the lower earner B. Payer A, support 2597.19 (the absolute value of the total).

8. Low-income (FC 4055(b)(7), R1, R2): threshold:

    python3 -I -c "$P; x=F('21.00')*40*52/12; print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 3640 364000 3640.00

   Payer A NDI 12105.04, strictly less than the threshold (FC 4055(b)(7)):

    python3 -I -c "$P; print(F('12105.04')<F(3640))"
    -> False

   Not applicable. Maximum reduction 0.00; range (FC 4055(c)) 2597.19 to 2597.19.

### S5: allocation under FC 4055(b)(8)

- Amount for 1 child (FC 4055(b)(8), (b)(4) multiplier 1):

    python3 -I -c "$P; x=F('1')*F('38802069070051/34362075000'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 38802069070051/34362075000 112921.204758592139735449619966 1129.21

- Amount for 2 children (FC 4055(b)(8), (b)(4) multiplier 1.6):

    python3 -I -c "$P; x=F('1.6')*F('38802069070051/34362075000'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 38802069070051/21476296875 180673.927613747423576719391946 1806.74

- Amount for 3 children (FC 4055(b)(8), (b)(4) multiplier 2):

    python3 -I -c "$P; x=F('2')*F('38802069070051/34362075000'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 38802069070051/17181037500 225842.409517184279470899239932 2258.42

- Amount for 4 children (FC 4055(b)(8), (b)(4) multiplier 2.3):

    python3 -I -c "$P; x=F('2.3')*F('38802069070051/34362075000'); print(x, D(x*100), ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100))"
    -> 892447588611173/343620750000 259718.770944761921391534125922 2597.19

- Per-child amounts (FC 4055(b)(8)), youngest first, differences of the displayed amounts (R8, R9):

    python3 -I -c "from decimal import Decimal as Dm; print([Dm('1129.21')]+[Dm(y)-Dm(x) for x,y in zip(['1129.21', '1806.74', '2258.42'],['1806.74', '2258.42', '2597.19'])])"
    -> [Decimal('1129.21'), Decimal('677.53'), Decimal('451.68'), Decimal('338.77')]

- Sum against the shown support (FC 4055(b)(8)):

    python3 -I -c "from decimal import Decimal as Dm; print(sum([Dm('1129.21'), Dm('677.53'), Dm('451.68'), Dm('338.77')]))"
    -> 2597.19, equal to the shown 2597.19.

- S5 check (FC 4055(b)(8)): each exact per-child difference rounded on its own, with the sum of those cents:

    python3 -I -c "from fractions import Fraction as F; from decimal import Decimal as Dm, getcontext; getcontext().prec=30; D=lambda x: Dm(x.numerator)/Dm(x.denominator); x=[F('38802069070051/34362075000'), F('38802069070051/57270125000'), F('38802069070051/85905187500'), F('38802069070051/114540250000')]; print(['%d.%02d'%divmod((y*100+F(1,2))//1,100) for y in x]); print(sum((y*100+F(1,2))//1 for y in x))"
    -> ['1129.21', '677.53', '451.68', '338.76'] | 259718

  Those four amounts add to 2597.18, NOT to the shown total 2597.19. The R8 differences above DO add to 2597.19. This is why R8 differences the displayed amounts.

Rounding guard: 12 rounded money values in this case; the closest to a half-cent is 0.01809656 of a cent-times-100 unit away (limit 0.01).
