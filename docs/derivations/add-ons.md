# Add-ons: hand derivations for the fixtures of `docs/specs/add-ons.md`

Sources: California Family Code sections 4055, 4061 and 4062, the versions added by Stats. 2023, ch. 213, sec. 3 (SB 343), operative September 1, 2024; `docs/sources/` holds the text. The basic support amounts follow `guideline-step-1.md`'s method and its readings R1 to R5; they are not argued again here.

Invented data only: Parent A, Parent B, one child, an invented hourly minimum wage of 21.00 (threshold 3640.00, as in step 1). Net disposable income and every add-on cost are inputs.

## Method

Every step below is a command run with `python3 -I -c`, using `fractions.Fraction` as a calculator and never importing the toolkit. Each command starts with the shell variable `P` (display helper only), and the line after it, starting `->`, is its exact output:

    P="from fractions import Fraction as F; from decimal import Decimal as Dm, getcontext; getcontext().prec=30; D=lambda x: Dm(x.numerator)/Dm(x.denominator); S=lambda x: ('-' if x<0 else '')+'%d.%02d'%divmod((abs(x)*100+F(1,2))//1,100)"

`S(x)` is the displayed amount: rounded half-up, to the cent, from the exact value (guideline-step-1.md R4). Where a result is money, the exact fraction, its value times 100 (so the cent boundary is visible) and the displayed amount are printed. Rounding guard: no displayed value below is within 0.01 of a half-cent, that is $0.0001, of its exact value times 100.

## Readings

- A1: each parent's share is that parent's adjusted figure over the sum of both, applied to the total of the typed costs (spec 4.3).
- A2: Parent A's amount is rounded from the exact value and Parent B's is the total less Parent A's displayed amount, so the two add to the total shown. In every fixture below that equals Parent B's own exact amount rounded; each fixture checks it.
- A3 (spec O3): the FC 4061(d) reduction uses the support amount as displayed, to the cent.
- A4 (spec 4.2, O6): when the support is a range, the reduction and the split are computed at each end of the displayed range.

## AO1

Inputs: A 5000.00, B 3000.00, A's time 20 percent, childcare 600.00, uninsured health 120.00; adjusted figures typed 5000.00 and 3000.00.

1. Basic support (FC 4055): TN 8000, row 3 (R3), K = (1 + 1/5) x 1/4, CS = K x (HN - H% x TN) with HN = A = 5000.00.

        python3 -I -c "$P; k=(1+F(20,100))*F(1,4); x=k*(F('5000.00')-F(20,100)*F('8000.00')); print(k, x, D(x*100), S(x))"
        -> 3/10 1020 102000 1020.00

   A is the high earner and the sign is positive, so A pays 1020.00 (FC 4055(b)(5)).
2. Total of costs: `F('600.00')+F('120.00')` -> 720.00.
3. Reduced figure (FC 4061(d)): A 5000.00 - 1020.00 = 3980.00; B stays 3000.00.
4. Shares and amounts (A1, A2):

        python3 -I -c "$P; a=F('720.00')*F('3980.00')/(F('3980.00')+F('3000.00')); b=F('720.00')-a; print(a, D(a*100), S(a), S(b), D(b*100), S(F('720.00')-F(S(a))))"
        -> 143280/349 41054.4412607449856733524355301 410.54 309.46 30945.5587392550143266475644699 309.46

   A 410.54, B 309.46; the two add to 720.00. Shares displayed: `D(F(3980)/F(6980)*100)` -> 57.02%, B 42.98%.

## AO2

Inputs: A 6000.00, B 2000.00, A's time 10 percent, childcare 450.00; adjusted figures typed A 5400.00, B 2600.00 (an invented spousal-support case; the tool does not adjust them).

1. Basic support: TN 8000, row 3, K = (1 + 1/10) x 1/4 = 11/40, HN = A = 6000.00.

        python3 -I -c "$P; k=(1+F(10,100))*F(1,4); x=k*(F('6000.00')-F(10,100)*F('8000.00')); print(k, x, D(x*100), S(x))"
        -> 11/40 1430 143000 1430.00

   A pays 1430.00. The paying parent is chosen by the guideline on the unadjusted NDIs, so the typed adjusted figures do not change who pays.
2. Reduced figure (FC 4061(d)): A 5400.00 - 1430.00 = 3970.00; B stays 2600.00.
3. Amounts:

        python3 -I -c "$P; a=F('450.00')*F('3970.00')/(F('3970.00')+F('2600.00')); print(a, D(a*100), S(a), S(F('450.00')-a), S(F('450.00')-F(S(a))))"
        -> 19850/73 27191.7808219178082191780821918 271.92 178.08 178.08

   A 271.92, B 178.08; they add to 450.00.

## AO3

Inputs: A 4000.00, B 8000.00, A's time 30 percent, childcare 500.00; adjusted figures typed 4000.00 and 8000.00. The payer is not the high earner.

1. TN 12000, row 4 (R3): row fraction `0.10 + 1499/12000`. B is the high earner, so H% is B's time, 70 percent; it is above 50, so K uses 2 - H%.

        python3 -I -c "$P; r=F('0.10')+F(1499)/F(12000); k=(2-F(70,100))*r; x=k*(F('8000.00')-F(70,100)*F('12000.00')); print(r, k, x, D(x*100), S(x))"
        -> 2699/12000 35087/120000 -35087/300 -11695.6666666666666666666666667 -116.96

   The sign is negative, so the other parent pays (FC 4055(b)(5)): A pays 116.96. A's NDI 4000.00 is not less than 3640.00, so no low-income adjustment.
2. Reduced figure (FC 4061(d), A3): A 4000.00 - 116.96 = 3883.04; B stays 8000.00.
3. Amounts:

        python3 -I -c "$P; a=F('500.00')*F('3883.04')/(F('3883.04')+F('8000.00')); print(a, D(a*100), S(a), S(F('500.00')-a), S(F('500.00')-F(S(a))))"
        -> 12134500/74269 16338.5800266598446188854030618 163.39 336.61 336.61

   A 163.39, B 336.61; they add to 500.00.

## AO4

Inputs: A 3000.00, B 1000.00, A's time 0 percent, childcare 300.00; adjusted figures typed 3000.00 and 1000.00.

1. Basic support: TN 4000, row 2, K = row fraction `0.131 + 4000/42149` (H% 0, so 1 + 0), HN = A = 3000.00.

        python3 -I -c "$P; k=F('0.131')+F(4000)/F(42149); x=k*F('3000.00'); print(k, x, D(x*100), S(x))"
        -> 9521519/42149000 28564557/42149 67770.4263446345109018007544663 677.70

2. Low-income (FC 4055(b)(7), (c); step 1 R1, R2, R5): payer A's NDI 3000.00 is less than 3640.00; maximum reduction `x * (3640 - 3000) / 3640`.

        python3 -I -c "$P; x=F(28564557,42149); m=x*(F(3640)-F(3000))/F(3640); print(m, D(m*100), S(m), S(x-m), D((x-m)*100))"
        -> 65290416/547937 11915.6793572983755431737590270 119.16 558.55 55854.7469873361353586269954393

   The range is 558.55 to 677.70, as the tool prints (verified against `support`).
3. Top of the range, 677.70 (A4): A 3000.00 - 677.70 = 2322.30; B stays 1000.00.

        python3 -I -c "$P; a=F('300.00')*F('2322.30')/(F('2322.30')+F('1000.00')); print(a, D(a*100), S(a), S(F('300.00')-a), S(F('300.00')-F(S(a))))"
        -> 6966900/33223 20970.1110676338681034223279054 209.70 90.30 90.30

4. Bottom of the range, 558.55: A 3000.00 - 558.55 = 2441.45; B stays 1000.00.

        python3 -I -c "$P; a=F('300.00')*F('2441.45')/(F('2441.45')+F('1000.00')); print(a, D(a*100), S(a), S(F('300.00')-a), S(F('300.00')-F(S(a))))"
        -> 4882900/22943 21282.7441921283180054918711590 212.83 87.17 87.17

## AO5

Inputs: AO1's inputs, with the person's split 50 percent for A and no adjusted figures. No FC 4061(d) reduction is used (spec 4.3).

    python3 -I -c "$P; a=F('720.00')*F(50,100); print(a, S(a), S(F('720.00')-a))"
    -> 360 360.00 360.00

## AO6

AO1's guideline inputs and no cost: no figure is computed; the report prints the rest state of spec section 5.

## AO7

Each refusal row of spec 3.3 is a run that exits 2 with one line on standard error; there is no arithmetic. The build supplies the exact messages.
