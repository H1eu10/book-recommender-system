# Initial collaborative recommendation results

Run on 2026-11-05 using the bundled synthetic data: 1,000 users, 200 books,
11,667 deduplicated interactions. Random per-user train/validation/test splits,
seeds 42/43/44, K=10. This is an initial configuration, not an exhaustive tuning
study or evidence of real-reader performance.

| Model | Precision@10 | Recall@10 | NDCG@10 |
| --- | --- | --- | --- |
| Popularity | 0.0433 ± 0.0016 | 0.2191 ± 0.0073 | 0.1263 ± 0.0041 |
| Item-CF | 0.0596 ± 0.0012 | 0.3091 ± 0.0106 | 0.1767 ± 0.0027 |
| NCF | 0.0414 ± 0.0013 | 0.2066 ± 0.0037 | 0.1163 ± 0.0078 |
| LightGCN | 0.0527 ± 0.0055 | 0.2752 ± 0.0338 | 0.1604 ± 0.0209 |

Values are mean ± sample standard deviation across three seeds. Every seed
evaluated 997 users; three users with fewer than three likes remained train-only.
Seed 43 had one test interaction for an item not present in training; that cold
target was excluded from the warm metrics. Seeds 42 and 44 had none.

Both neural models used 32-dimensional embeddings, learning rate 0.001,
regularization coefficient 0.0001, batch size 2,048, at most 100 epochs, and
patience 10. LightGCN used two propagation layers. Validation NDCG@10 selected
epochs 24/99/100 for LightGCN and 39/53/56 for NCF. The initial LightGCN run
therefore reached its epoch budget on two seeds; these are budget-limited
results, not a convergence claim. NCF and LightGCN regularization differ as
documented in the protocol.

Item-CF performed best in this experiment. LightGCN exceeded NCF in all three
test splits but did not exceed Item-CF. These observations do not establish a
general ordering of the algorithms. Do future tuning on validation, not these
reported test scores.

The generated full report, per-seed splits and checkpoints are in
`backend/artifacts/collaborative/`. They are local, Git-ignored training outputs.
The report contains split/data hashes, training histories and exact settings.

Validation performed:

- 25 algorithm tests passed: splitting, disjoint folds, normalized graph,
  negative sampling, ranking metrics, seen-item masking, BPR learning,
  checkpoint round trips, content filtering/cache invalidation and hybrid masking.
- Three-fold integration smoke run completed, including validation selection
  over dimensions 4/8 and depths 1/2. Its two-epoch scores are not research results.
- Saved LightGCN checkpoint loaded successfully and produced recommendations
  without training.
- During the initial algorithm run, API tests were not completed because the
  synchronous TestClient stalled in the sandbox. The later application integration
  identified a loopback socket restriction: running outside that sandbox completed
  all 48 backend tests. Frontend build/lint and browser flows were also verified.
  These application changes do not alter the benchmark results above.

See [commands and evaluation protocol](collaborative_algorithms.md) to reproduce.
