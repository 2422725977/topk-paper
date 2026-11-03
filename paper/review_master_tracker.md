# Review master tracker (INTERNAL/EDITOR-FACING — not reviewer-facing)

Decision type: not supplied (simulated review package; posture = Major Revision per Reviewer 1 and 2 recommendations). Task mode: revise + revision-package.

| ID | Concern (paraphrase) | Severity/Blocking | Action | Status | Manuscript location |
|---|---|---|---|---|---|
| R1-M1 | Lemma 3.2 false intermediate inequality + wrong constant | Major/Yes | chi-square proof; C_B redefined; constants propagated | VERIFIED_DONE | Lemma 3.2, Thm 4.1 |
| R1-M2 | Thm 4.1(b) false extremal-entry claim | Major/No | Popoviciu range argument; constant adjusted | VERIFIED_DONE | proof of Thm 4.1(b) |
| R1-M3 | Prop 5.2 sketch inconsistent with kappa bound | Major/No | full proof, kappa-corrected data-independent screen, budget restated, screen remark | VERIFIED_DONE | Prop 5.2 + Remark 5.3 |
| R1-M4 | Thm 5.1 proof by citation; "regularized" ambiguous | Major/Yes | guarantee stated verbatim in theorem as explicit assumption; honest conditionality; renamed constrained MLE | VERIFIED_DONE | Thm 5.1 |
| R1-M5 | Remark 4.3 path illustration quantitatively wrong | Major/No | rewritten via concentration ratio; path covered; dumbbell illustrative | VERIFIED_DONE | Remark 4.3 |
| R1-m1..m11 | notation collisions; BH constant; boundary band; exactly-under; T* def; kappa^2 parenthetical; 8A + cross-ref + round-dependence; E2c labels; E4 B=3000; reps bookkeeping; abstract capitalization | Minor/No | all fixed | VERIFIED_DONE | various |
| R2-M1 | n-scaling validation attributed to wrong algorithm | Major/No | abstract reword + new E2d n-sweep (e2d.json) | VERIFIED_DONE | abstract; 6.1; Appendix |
| R2-M2 | E2b five-point falsification without uncertainty | Major/No | downgraded to indicative; limitations stated; instability example cited | VERIFIED_DONE | 6.3; 6.7(ii) |
| R2-M3 | raw-space R^2 undisclosed; large-Delta mispredictions; floor regime; b/a=5.45 | Major/No | fit space disclosed (raw+log); mispredictions quoted; floor regime discussed; b/a contextualized | VERIFIED_DONE | 6.2; 6.7(iii) |
| R2-M4 | "prove/provably/proved" overstatement | Major/No | derive language + premises stated at all three locations | VERIFIED_DONE | abstract; 6.2; 6.7(iii) |
| R2-M5 | generator/seeds/code/parameter drift undocumented | Major/No | appendix parameters paragraph + table + code statement | VERIFIED_DONE | 6 preamble; Appendix |
| R2-m1..m12 | E2c labels; E4 B=3000; intro 1.00; symbols; seed policy; rounds_median JSON defect + cap semantics; binomial SE; CI method; parameter table; E3-UE disclosure; both fits; R^2=0.999 | Minor/No | all fixed; e4/e5 JSON regenerated (same seeds, identical headline numbers, corrected rounds) | VERIFIED_DONE | various; results/e4.json, e5.json |
| R3-M1 | "matching up to log factors" contradicts displayed bounds (factor n) | Major/Yes | abstract + contribution 2 corrected; side condition stated; Prop 5.3 re-checked | VERIFIED_DONE | abstract; contrib 2; 7 |
| R3-M2 | significance delta over cited literature small | Major/No | delta isolated in one sentence in Section 2; Theorem 5.1 assumption explicit; worked application consequence NOT added (future work) | PARTIAL_DONE (claim moderation applied; application example declined) | Section 2; Thm 5.1 |
| R3-M3 | "validate the n-scaling" attribution | Major/No | abstract reword + E2d n-sweep | VERIFIED_DONE | abstract; 6.1 |
| R3-M4 | "proved" overstatement | Major/No | derive language + premises | VERIFIED_DONE | abstract; 6.2; 6.7(iii) |
| R3-m1..m13 | abstract capitalization; bound gloss; symbols; Thm 4.1 consistency; Prop 5.2 status; E4; E5; E2; preamble reps; subsection order; E2c display; reproducibility statement; li2026low | Minor/No | all fixed except E2c display (declined for 12-page budget; numbers in prose + e2c.json) | 12 VERIFIED_DONE, 1 declined | various |
| AUD-01..13 | forensic audit findings | editorial | all confirmed findings resolved by the actions above; AUD-09/10 resolved by disclosure; AUD-11/12 resolved by appendix + regeneration | VERIFIED_DONE | various |

Cross-reviewer consensus handled internally: matching claim (R3 blocking, audit-corroborated); derive-language (R2+R3); n-scaling attribution (R2+R3); Thm 4.1(b) justification (R1+R3); Prop 5.2 status (R1+R3); E4/E5/E2c prose slips (R1+R2+R3); symbol collisions (R1+R2+R3); reps bookkeeping (R1+R3). Each reviewer-facing letter contains only that reviewer's items.
