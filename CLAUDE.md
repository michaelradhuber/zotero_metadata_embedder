<!-- The same rule as ~/.claude/CLAUDE.md on Michael's server, kept here so it travels with the repository. -->

# Fixing problems: fix the class, not the case

Michael Radhuber, 2026-10-15: "Focus on abstract solutions covering multiple possible problems!!!"
(and 2026-08-04: "I want no concrete corrections, I want abstract ones that work for more than 1 scenario").

When something is wrong (a bug, a bad record, a wrong prompt, a failed job, a wrong answer):

1. Name the class. Ask which general rule was broken and what else can break the same way. The case
   that was reported is one example of the class.
2. Fix the class where it starts: one shared rule or function that every path goes through, not a
   patch for the one path that failed. If a rule already exists and was broken, widen it where it
   lives instead of adding a second one beside it.
3. Guard the class: a test or check that fails for any instance of it. Prove the guard by breaking
   the code and watching it fail.
4. Repair every existing instance: sweep the store, the code or the logs for all of them, not only
   the ones that were seen. Dry run first and read what it would change.
5. When reporting, name the class and what the fix covers, beside the case that started it.
