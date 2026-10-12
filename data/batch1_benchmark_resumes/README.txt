Batch 1 (001-020) + extras A/B/C (8 resumes). All fictional.
batch1_resumes_001_020.txt : 20 resumes in the delimiter format (=== RESUME START: ... ===)
extras_ABC_resumes.txt     : A1-A3 gold, B1-B3 buzzword, C1-C2 structural anomalies
individual_resumes/        : the same 28 as separate .txt files (what the parser ingests)
batch1_manifest.csv        : ground truth per resume
batch_gen.py, validate_batch.py : regenerate and check parsing/ranking (validate: python validate_batch.py <dir> <project_root>)
