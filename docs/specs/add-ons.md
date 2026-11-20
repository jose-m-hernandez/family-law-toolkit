# Add-ons: behaviour spec

Date: 2026-11-19.

Written from requirements only: what a parent preparing California family-law paperwork needs when a child-support figure has to be split between two parents with extra costs on top. "Add-ons" is this feature's internal name; the printed lines say "additional child support (FC 4062)". Every person, number and example is invented.

## 1. Purpose and the user's problem

A parent has worked out guideline child support (the `support` command) and now has a monthly cost for the children that the guideline figure does not cover, such as childcare while a parent works. They want to see, in dollars, how that one monthly cost divides between the two parents under the sections quoted in section 2, so they can check a figure they were handed or see the arithmetic behind one they expect to be asked for. They type the costs and some income figures themselves. The tool does arithmetic on those figures and prints the working. It never says which costs the person should claim, or what any court will order.

## 2. The legal sentences

Every sentence in this spec that states what the law means is only a quotation of the filed source in `docs/sources/`, never a paraphrase. A quotation is exactly the text of `fc4061.txt` or `fc4062.txt` between the quotation marks, with the subdivision labels (the spacing after "(a)" and so on) as those files print them.

- FC 4062(a): "The court shall order the following as additional child support:" followed by (a)(1) and (a)(2) below.
- FC 4062(a)(1): "Childcare costs, if those expenses are actually incurred, related to employment or to reasonably necessary education or training for employment skills, as described in Section 4063, unless those costs are specifically included in the guideline calculation itself."
- FC 4062(a)(2): "The reasonable uninsured health care costs for the children as provided in Section 4063."
- FC 4062(b): "The court may order the following as additional child support:" followed by "Costs related to the educational or other special needs of the children." and "Travel expenses for visitation."
- FC 4061, first sentence: "The amounts in Section 4062 shall be considered additional support for the children and shall be computed in accordance with the following:"
- FC 4061(a), first clause: "If there needs to be an apportionment of expenses pursuant to Section 4062, the expenses shall be divided in proportion to the parents’ net incomes as adjusted pursuant to subdivisions (c) and (d)"
- FC 4061(a), last clause: "unless a party requests or the court finds on its own motion that expenses should be divided in a different manner."
- FC 4061(b)(1): "The basic child support obligation shall first be computed using the formula set forth in subdivision (a) of Section 4055, as adjusted for any appropriate rebuttal factors in subdivision (b) of Section 4057."
- FC 4061(b)(2): "Any additional child support required for expenses pursuant to Section 4062 shall thereafter be ordered to be paid by the parents in proportion to their net disposable incomes as adjusted pursuant to subdivisions (c) and (d)."
- FC 4061(c): "In cases when spousal support is or has been ordered to be paid by one parent to the other, for purposes of allocating additional expenses pursuant to Section 4062, the gross income of the parent paying spousal support shall be decreased by the amount of the spousal support paid and the gross income of the parent receiving the spousal support shall be increased by the amount of the spousal support received for as long as the spousal support order is in effect and is paid."
- FC 4061(d): "For purposes of computing the adjusted net disposable income of the parent paying child support for allocating any additional expenses pursuant to Section 4062, the net disposable income of the parent paying child support shall be reduced by the amount of any basic child support ordered to be paid under subdivision (a) of Section 4055. However, the net disposable income of the parent receiving child support shall not be increased by any amount of child support received."

Where the spec below cites a section, it relies on the quotation in section 2 and adds no statement about the law of its own. Nothing in this spec says which costs are childcare, health care or uninsured, or what "reasonable" means: the filed sources do not define them here (they point to FC 4063, which is not filed), and the printed report says so (section 5, line N3).

## 3. Scope and non-goals

In:
- Two monthly dollar amounts the person types, matching FC 4062(a)(1) and (a)(2) as the statute names them, added to the `support` command as optional inputs.
- The person's own typed figures for each parent's net disposable income as adjusted for spousal support (the FC 4061(c) adjustment, see 3.2), typed because the tool never adjusts income.
- The reduction of the paying parent's typed figure by the basic support amount the report has just computed (FC 4061(d)), after that amount is computed (FC 4061(b)(1), (b)(2)).
- Each parent's share of the total in proportion to those adjusted figures (FC 4061(a), (b)(2)), or, only when the person types it, a split the person chooses (FC 4061(a)).

Out:
- FC 4062(b) items, the "may" items: no input, no line that treats any amount as owed. The report prints that they are not computed (line N2).
- deciding which costs count, whether a cost is "actually incurred", "reasonable" or included in the guideline figure, or whether a figure is right for the person's case.
- computing any income, any deduction, or any tax; adjusting gross income for spousal support (3.2); applying FC 4057 rebuttal factors (FC 4061(b)(1)); proposing any split other than the proportional one.
- reading, writing or sending anything, the network, or a file.

### 3.1 Inputs

These are options of `python3 -m family_law_toolkit.support`, in addition to its six. Amounts are plain numbers with at most two decimals, monthly dollars, no commas or dollar sign, as the existing options are.

| Option | In the person's words | Notes |
|---|---|---|
| `--childcare-monthly AMOUNT` | Monthly childcare cost, with the help text of 3.1.1 | Optional. 0 or more. The label printed is the statute's own words from FC 4062(a)(1), quoted in the report as the heading of the line. The help quotes FC 4062(a)(1) in full. |
| `--uninsured-health-monthly AMOUNT` | Monthly uninsured health care cost for the children, with the help text of 3.1.1 | Optional. 0 or more. Label from FC 4062(a)(2). The help quotes FC 4062(a)(2). |
| `--a-adjusted-ndi AMOUNT` | Parent A's net disposable income, after any spousal-support adjustment and not reduced for child support | Required with any cost above unless `--a-cost-share-percent` is given. 0 or more, and see 3.2. Help text in 3.1.1. |
| `--b-adjusted-ndi AMOUNT` | Parent B's, likewise | As above. |
| `--a-cost-share-percent PERCENT` | Parent A's share of the additional child support costs, as you choose it | Optional. 0 to 100. A split the person chose, never one the tool offers (FC 4061(a)). Named "cost share" so it is not read as the time-share option `--a-time-percent`. |

The `support` command's existing six options keep their meaning. "A" and "B" are the same labels as everywhere else in the command.

### 3.1.1 Help text that quotes the statute

The `--help` text of the new options carries these sentences, and nothing else about the law. No help or printed line uses the word "add-on": "Add-ons" is the internal name, in this spec's title and section names only.

- `--childcare-monthly`: the statute's words, "Childcare costs, if those expenses are actually incurred, related to employment or to reasonably necessary education or training for employment skills, as described in Section 4063, unless those costs are specifically included in the guideline calculation itself." (FC 4062(a)(1), in full including the employment limit.)
- `--uninsured-health-monthly`: the statute's words, "The reasonable uninsured health care costs for the children as provided in Section 4063." (FC 4062(a)(2).)
- `--a-adjusted-ndi` and `--b-adjusted-ndi`: "Not reduced for child support: this report makes the FC 4061(d) reduction itself." The help also carries the same-figures sentence of 3.3.

### 3.2 What the person types for income, and what the tool does not do

FC 4061(c) speaks of gross income, and FC 4061(b)(2) speaks of net disposable incomes as adjusted. The tool has only net income that the person types, so it cannot make the gross-income adjustment. The person works out their own two figures with a lawyer, the court's self-help center or the family law facilitator, and types them; the tool states that it did not adjust them (line N1) and makes no approximation. When no spousal support is or was ordered, the person types the same figures they typed for `--a-ndi` and `--b-ndi`; the tool does not assume that, and does not fill it in. This keeps the rule of the repository that the tool never computes income.

### 3.3 Refusals

A run that cannot proceed prints one line to standard error and exits 2, as the `support` command does. It prints nothing to standard output. The messages name the option in the person's words and end with the existing pointer to `--help`.

| # | Condition | Refused |
|---|---|---|
| 1 | an amount that is not a plain number with at most two decimals, or is negative | yes |
| 2 | a cost option given and neither `--a-cost-share-percent` nor both adjusted-income options given | yes: says which are missing, then carries the same-figures sentence below |
| 3 | exactly one of the two adjusted-income options given | yes: carries the same-figures sentence below |
| 4 | an adjusted-income option given with no cost option | yes: an unused figure is refused rather than ignored |
| 5 | `--a-cost-share-percent` together with either adjusted-income option | yes: the split used would be unclear |
| 6 | `--a-cost-share-percent` outside 0 to 100, or an option repeated | yes |
| 7 | after the reduction in 4.2, the two adjusted figures do not add to more than zero, or either is below zero | yes: the proportion is not defined; the message gives both figures |
| 8 | both costs given as 0 | not refused: reported as 0.00 each |

**The same-figures sentence**: "If no spousal support is or has been ordered, enter the same figures you gave for `--a-ndi` and `--b-ndi`." It comes before the pointer to `--help` in the refusal-2 and refusal-3 messages, and it is in the `--help` text of `--a-adjusted-ndi` and `--b-adjusted-ndi`. It restates the condition of FC 4061(c) and 3.2's rule, and it is the only line a person sees at the moment it matters.

Exit status: 0 the report was printed, 2 the run could not proceed. The `compare` command's 0, 1 and 2 are a different command's.

## 4. What the tool computes

### 4.1 Order

The basic support amount and any range are computed first, exactly as today (FC 4061(b)(1), (b)(2)); nothing added here changes them. Only then is anything below computed. The tool carries exact fractions, as `docs/derivations/` does, and rounds only a displayed amount, to the cent, half up.

### 4.2 The paying parent's figure

The paying parent is the parent the report already names under "Paying parent". Their typed adjusted figure is reduced by the support amount the report prints (FC 4061(d)); the other parent's typed figure is not increased by anything. When the report prints a range because of the low-income adjustment, the reduction is computed twice, once at each end of the printed range, and both results are printed, as the per-child allocation does. No point in the range is chosen, and neither end is called the one ordered. When the support amount prints 0.00, the reduction is 0.00 and both figures stay as typed (see FC 4061(d)).

The reduction uses the support amount as printed (to the cent), not the exact value behind it, so a person can repeat it by hand from the report. (See O3, section 9.)

### 4.3 The shares

Default (FC 4061(a), (b)(2)): the paying parent's share is their reduced figure divided by the sum of both figures, and the other parent's share is the rest. Each parent's dollar amount is that share times the total of the typed costs, with Parent A's amount rounded to the cent and Parent B's amount taken as the total less Parent A's, so the two always add to the total shown. The split is shown for the total only, not for each cost line, because rounding each line separately can disagree with the total by a cent.

If the person typed `--a-cost-share-percent` (FC 4061(a)), Parent A's share is that percentage and Parent B's is the rest, and the adjusted-income options are not used or required.

## 5. Output

The existing report stays as it is, through its low-income section. A new section follows it, before the existing closing notes. Its text (every number is for the invented fixtures in section 7):

With no cost option (the rest state, so silence is not read as zero):

```text
Additional child support (FC 4062)
  No additional child support costs were entered. This report does not say that none apply.
```

With costs and the default split (fixture AO1):

```text
Additional child support (FC 4062), split under FC 4061
  Costs you entered, monthly:
    Childcare costs related to employment or to reasonably necessary education or training for employment skills (FC 4062(a)(1)): 600.00
    The reasonable uninsured health care costs for the children (FC 4062(a)(2)): 120.00
    Total: 720.00
  Net disposable income figures used (you entered them; this report did not adjust them):
    Parent A, as you entered it: 5000.00
    Parent B, as you entered it: 3000.00
  Basic support is taken first (FC 4061(b)(1)); then the paying parent's figure is reduced by it (FC 4061(d)):
    Parent A, the paying parent in this report: 5000.00 - 1020.00 = 3980.00
    Parent B is not increased by support received: 3000.00
  Split in proportion to those figures (FC 4061(a), (b)(2)):
    Parent A: 3980.00 / 6980.00 = 57.02%: 410.54
    Parent B: 3000.00 / 6980.00 = 42.98%: 309.46
```

The line "Parent A, the paying parent in this report: 5000.00 - 1020.00 = 3980.00" is the line built: the report does not say "pays", because FC 4061(d) reduces by the basic support "ordered to be paid", which this report cannot know.

With `--a-cost-share-percent` the proportional lines are replaced by `Split you entered: Parent A 50%, Parent B 50%` and the two amounts; the report prints no comparison with the proportional split. With a range, the three lines under "Basic support is taken first" and the split are printed once per end, headed with the end's support amount.

Closing notes, always printed with this section (after the existing two):

- **N1:** "You enter each parent's adjusted net disposable income yourself. This report does not adjust income for spousal support (FC 4061(c))." Printed only when the adjusted-income options were used.
- **N2:** "Costs the court may order (FC 4062(b)) are not computed here, and nothing in this report shows them as owed."
- **N3:** "This report does not decide which costs count, whether a cost is actually incurred or reasonable, or whether a cost is already included in the guideline figure. For those questions you can ask a lawyer, your court's self-help center, or its family law facilitator."
- **N4:** "The basic support amount above is this report's own arithmetic. It does not apply the rebuttal factors of FC 4057 (see FC 4061(b)(1)), and FC 4061(d) reduces by the basic support "ordered to be paid", which can differ from this figure."
- The existing last line, "This report is arithmetic on the figures you entered. It is not legal advice.", stays last.

The report never uses "certified", "validated" or "court-ready", never says what to claim or file or what a court will order, and never says which split to use.

## 6. Exit and error behaviour

Section 3.3. A run with no cost option and no new option is not an error and prints the rest state above; every existing invocation keeps exit 0 and gains only those two lines, which changes every existing golden report (a build consequence, section 9).

## 7. Fixtures

All invented, hand-derived; each derivation is written out in `docs/derivations/add-ons.md`, one expression per step, never importing the tool. Parent A and Parent B, minimum wage 21.00, one child.

| Id | Case | Expected |
|---|---|---|
| AO1 | A 5000.00 and B 3000.00 typed for both purposes, A's time 20%; childcare 600.00, health 120.00 | basic support 1020.00 paid by A; A 410.54, B 309.46 of 720.00 |
| AO2 | A 6000.00, B 2000.00, A's time 10%; adjusted figures typed A 5400.00, B 2600.00 (an invented spousal-support case); childcare 450.00 | basic support 1430.00 paid by A; A 271.92, B 178.08 of 450.00 |
| AO3 | A 4000.00, B 8000.00, A's time 30%; childcare 500.00; adjusted figures typed equal to the NDIs | basic support 116.96 paid by A, who is not the high earner; A 163.39, B 336.61 |
| AO4 | A 3000.00, B 1000.00, A's time 0%; childcare 300.00; adjusted figures typed equal to the NDIs | low-income range 558.55 to 677.70; at 677.70 A 209.70, B 90.30; at 558.55 A 212.83, B 87.17 |
| AO5 | AO1's inputs, with `--a-cost-share-percent 50` and no adjusted figures | A 360.00, B 360.00; no proportional lines |
| AO6 | AO1's guideline inputs, no cost option | the rest state, section 5 |
| AO7 | each refusal in 3.3, rows 1 to 7 | exit 2, one stderr line, empty stdout |

## 8. Not measured

This tool does not decide which costs qualify, whether a figure typed is right, how spousal support changes anyone's income, or what a court will do. It has no accuracy statement beyond "hand-derived" for AO1 to AO5. No count of matches against any court printout is claimed.

## 9. Build consequences and decided points

Build consequences and decided points; not legal sentences.

- Every existing golden report gains the rest-state lines (section 6); `support --help` and its option count change (the parser has eleven options).
- `tests/test_sources.py` pins FC 4055's hashes only; pinning FC 4061's and 4062's four hashes is a build step.
- **User-facing files that go stale when the options land.** The build changes each of these in the same release, and none is changed by this spec:
  - the `AGENTS.md` Status paragraph, which now says "five required inputs … and one optional input" and is read by an agent talking to a person;
  - the README's calculator section;
  - the CHANGELOG entry.
- **`--help` example.** `support --help` gains an example that uses the new options, on invented numbers (AO1's would do), so a person learns them from the help and not only from this spec.
- **The calculator skill.** The release also carries one skill: run the `support` calculator, report what it printed, refuse advice, and point to a lawyer, the court's self-help center or the family law facilitator. With it, two checks: a drift test (every command and flag the skill names exists), and one recorded agent run from a fresh clone on invented numbers, which also serves as the stranger run. The skill's layout for Claude Code and Codex is stated in O7.
- **O1.** The tool uses only its own basic support figure and never a typed one; line N4 says so.
- **O3.** The reduction uses the printed (cent) support amount, not the exact value behind it, so a share can differ from the exact-value share by at most a cent.
- **O4.** Refusal 7 (a reduced figure below zero, or two figures that do not add to more than zero): the report refuses rather than printing a share, and applies no floor at zero (3.3, row 7).
- **O6.** In a low-income range the reduction and the split are computed at both ends of the printed range, and neither end is chosen (4.2).
- **O7.** The release carries one calculator skill with one source file in the repository. Each harness's discovery path is wired to that one file. No copy is kept by hand; a drift test fails if any copy differs or any named command or flag is missing, and it checks the wiring today. A recorded run in each harness from a fresh clone is still to come. The exact paths are measured at build, not assumed.
