---
name: support-calculator
description: Run the family-law-toolkit guideline child-support calculator on figures the person enters, report only what it printed, and never advise.
---

# Support calculator

Use this when a person wants the guideline child-support calculator in this
repository run on their figures, or wants to see how the calculator splits
costs for the children between two parents. Use invented numbers for any
example.

## What to run

From the repository root:

    python3 -m family_law_toolkit.support --a-ndi AMOUNT --b-ndi AMOUNT --a-time-percent PERCENT --children COUNT --minimum-wage-hourly AMOUNT

`--a-ndi` and `--b-ndi` are each parent's monthly net disposable income, which
the person works out and types; the calculator does not work it out.
`--a-time-percent` is Parent A's share of time (repeat it once per child to give
a share for each child). `--children` is the number of children, 1 to 10.
`--minimum-wage-hourly` is the hourly state minimum wage the person uses.

Optional flags:

- `--same-time-sharing-arrangement yes` or `no`: whether all the children share
  one time-sharing arrangement. It has an effect only with two or more children.
- `--childcare-monthly AMOUNT` and `--uninsured-health-monthly AMOUNT`: monthly
  costs for the children, to be split between the parents.
- `--a-adjusted-ndi AMOUNT` and `--b-adjusted-ndi AMOUNT`: each parent's net
  disposable income as the person worked it out after any spousal-support
  adjustment. Give both, or neither. If no spousal support is or has been
  ordered, the person gives the same figures as `--a-ndi` and `--b-ndi`.
- `--a-cost-share-percent PERCENT`: Parent A's share of the costs, if the person
  chooses the split instead of giving the two adjusted figures.

A cost needs either both adjusted figures or `--a-cost-share-percent`. Run with
`--help` to see every flag. Exit status 0 means a report was printed; 2 means
the run could not proceed, with one line on standard error saying why.

## How to answer

1. Explain what the calculator computes and what each input means. Never say
   what figure to claim, which costs count, which split to use, what to file or
   argue, or what outcome to expect. For those questions, point the person to
   a lawyer, the court's self-help center, or the family law facilitator.
2. Report what the command printed, and the exit status it returned. Quote its
   lines; do not restate them as findings of your own.
3. Claim only what the command did. Never call its output "filing-ready",
   "certified" or "validated".
4. If a check or run could not happen, say it was not run, and why. Never report
   it as passed.
5. Never file, send or post anything for the person.
6. What the person shares stays theirs: do not copy their documents, names or
   figures into issues, commits or anything public.
