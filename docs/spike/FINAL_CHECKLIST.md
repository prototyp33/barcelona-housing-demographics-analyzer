# Final Checklist - Spike Ready?

Run this checklist **Sunday evening** before Monday kickoff.

---

## ✅ GitHub Project Setup

- [ ] All issues (#194-#209) visible in project
- [ ] Custom fields configured (13 new issues)
- [ ] Roadmap view created and functional
- [ ] Sprint board view created (optional)
- [ ] Epic dashboard view created (optional)

**Verify:**
```bash
gh project item-list 1 --owner prototyp33 --format json | jq '.items | length'
# Should show 13+ items
```

---

## ✅ Repository Setup

- [ ] Repository cloned locally
- [ ] Virtual environment created (`.venv-spike`)
- [ ] Dependencies installed (`pip install -r spike-data-validation/requirements.txt`)
- [ ] Jupyter kernel registered
- [ ] Directories created (`data/raw`, `data/processed`, `outputs/`)

**Verify:**
```bash
cd spike-data-validation
python -c "import pandas, statsmodels, geopandas; print('✅ All packages installed')"
```

---

## ✅ Notebooks Ready

- [ ] `01-gracia-hedonic-model.ipynb` exists (base template)
- [ ] `02-hedonic-model-gracia.ipynb` exists (Equipo B - #208)
- [ ] `03-did-viability-assessment.ipynb` exists (Equipo B - #209)
- [ ] All notebooks open and runnable

**Verify:**
```bash
ls -la spike-data-validation/notebooks/*.ipynb
# Should show 3 notebooks
```

---

## ✅ Documentation

- [ ] `docs/spike/KICKOFF_AGENDA.md` created
- [ ] `docs/spike/DAILY_STANDUP_TEMPLATE.md` created
- [ ] `docs/spike/FINAL_CHECKLIST.md` created (this file)
- [ ] `docs/ISSUE_RELATIONSHIPS_MAP.md` reviewed
- [ ] `docs/CUSTOM_FIELDS_SUMMARY.md` available

---

## ✅ Team Access

- [ ] Equipo A has GitHub access
- [ ] Equipo B has GitHub access
- [ ] Slack channel created (#spike-validation-dec16-20)
- [ ] Shared drive access granted (if applicable)
- [ ] All team members have repo access

---

## ✅ Data Sources Access

- [ ] Portal de Dades API access verified
- [ ] INE API access verified (or alternative)
- [ ] Catastro access verified (or alternative)
- [ ] API keys/tokens available (if needed)

---

## ✅ Communication Channels

- [ ] Slack channel: #spike-validation-dec16-20
- [ ] Daily standup time confirmed (10:00 AM)
- [ ] Sync points scheduled:
  - [ ] Tuesday 5:00 PM (data delivery)
  - [ ] Thursday 3:00 PM (joint presentation)
  - [ ] Friday 3:00 PM (GO/NO-GO decision)

---

## ✅ Issues Assigned

- [ ] Equipo A issues assigned (#199, #200, #201, #204, #205, #206, #207)
- [ ] Equipo B issues assigned (#208, #209)
- [ ] Epic #198 assigned to Tech Lead/PM

---

## ✅ Success Criteria Clear

- [ ] R² ≥ 0.55 target understood
- [ ] Match rate ≥ 70% target understood
- [ ] Data quality thresholds clear (>95% completeness, >98% validity)
- [ ] GO/NO-GO criteria documented

---

## 🚨 Red Flags (Check Before Starting)

- [ ] No blockers identified
- [ ] All dependencies available
- [ ] Team members available all week
- [ ] No conflicting priorities

---

## 📋 Quick Reference

**Project URL:** https://github.com/prototyp33/barcelona-housing-demographics-analyzer/projects/1

**Spike Epic:** #198

**Total Issues:** 13 (3 epics + 10 spike issues)

**Total Effort:** 74h (54h Equipo A + 20h Equipo B)

**Duration:** Dec 16-20, 2025 (5 days)

---

## ✅ Final Sign-Off

- [ ] Tech Lead: Ready to start
- [ ] Product Manager: Ready to start
- [ ] Equipo A Lead: Ready to start
- [ ] Equipo B Lead: Ready to start

---

**If all items checked, you're ready for Monday kickoff! 🚀**

**Last updated:** Sunday Dec 15, 2025

