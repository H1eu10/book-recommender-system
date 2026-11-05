# Collaborative book recommendation experiments

The algorithm layer supports Popularity, Item-CF, NCF and LightGCN. Frontend and
API integration are intentionally separate. The bundled 1,000-user interaction
dataset is synthetic; these experiments do not establish real-reader quality.

## Setup and commands

Use Python 3.11 and install the single dependency list from `backend`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

LightGCN uses the existing PyTorch, NumPy and SciPy dependencies; PyTorch Geometric
is not required. Run the following commands from `backend` in PowerShell:

```powershell
$env:PYTHONUTF8 = '1'
.\.venv\Scripts\python.exe scripts/benchmark_collaborative.py
```

Default: three seeds (42, 43, 44), embedding dimension 32, two LightGCN layers,
at most 100 epochs, early stopping after 10 non-improving validation epochs.
All eligible users are evaluated, rather than only the first 30/100.

```powershell
# Small integration run; its scores are not final experimental results.
.\.venv\Scripts\python.exe scripts/benchmark_collaborative.py --seeds 42 --epochs 3 --output artifacts/smoke

# Select dimension and propagation depth using validation only.
.\.venv\Scripts\python.exe scripts/benchmark_collaborative.py --embedding-dims 32 64 --layers 1 2 3 --output artifacts/grid

# Independently train one model, with the same evaluation protocol.
.\.venv\Scripts\python.exe scripts/benchmark_collaborative.py --models lightgcn --output artifacts/lightgcn
.\.venv\Scripts\python.exe scripts/benchmark_collaborative.py --models ncf --output artifacts/ncf

# Proper disjoint test folds; the next fold is validation.
.\.venv\Scripts\python.exe scripts/benchmark_collaborative.py --folds 5 --seeds 42 --output artifacts/kfold

# Inference from a selected checkpoint, without training.
.\.venv\Scripts\python.exe scripts/recommend_collaborative.py artifacts/collaborative/seed-42/fold-0/lightgcn.pt user_001 --limit 10

# Unit and API tests.
.\.venv\Scripts\python.exe -m pytest tests -q
```

`benchmark_collaborative.py` is the single training/comparison entry point;
use `--models` for one model and `--folds` for cross-validation.
Reports and checkpoints are written under `backend/artifacts/` (Git-ignored).
Use different `--output` directories to retain separate experiments.

The scripts directory contains five entry points:

| Script | Purpose |
| --- | --- |
| `benchmark_collaborative.py` | Train, compare and cross-validate collaborative models |
| `recommend_collaborative.py` | Load a checkpoint and recommend without training |
| `evaluate_cbf.py` | Check content matching using the shared ranking metrics |
| `tune_hybrid_alpha.py` | Validate the optional content/Item-CF hybrid |
| `generate_mock_users.py` | Generate synthetic profiles, replacing the interaction JSON |

The optional `tune_hybrid_alpha.py` experiment uses an average TF-IDF profile of
training-liked books plus Item-CF scores. It selects alpha on validation and
evaluates the selected alpha on test once. It is separate from the four-model
collaborative comparison. `evaluate_cbf.py` remains a metadata-matching sanity
check, not an independent held-out behavior benchmark.

## Evaluation protocol

1. Validate IDs against the book catalog, deduplicate likes and sort IDs.
2. Shuffle once with a local seeded RNG. For users with at least three likes,
   reserve approximately 20% each for validation and test, at least one each;
   keep at least one training interaction. Users with fewer likes are train-only.
3. Build **every** model and the LightGCN graph from the same training data.
   No validation/test edges are inserted into the graph. Negative samples use
   only training information and are resampled each epoch.
4. Rank against the complete warm-item catalog (items observed in training),
   without sampled evaluation negatives. Every model masks training positives.
   At final test time every model additionally masks validation positives.
   Equal scores are ordered by book ID. Short lists are not padded.
5. Use validation NDCG@K to select the epoch and requested dimension/layer grid.
   Evaluate test only after this selection. The selected model stays fitted to
   training edges; it is not retrained on validation for this experiment.
6. Report macro Precision@K, Recall@K, NDCG@K, evaluated-user counts, cold target
   counts, histories, selected configuration, runtime, dataset/split SHA-256 and
   runtime versions. Precision divides by K even when fewer items are available.
   Cold-item targets are excluded from warm metrics and counted explicitly;
   users with no remaining warm targets are also counted and excluded.
7. Report mean and sample standard deviation across seeds. For K-fold runs,
   average fold metrics within each seed first. This SD is descriptive, not a
   confidence interval or significance test.

For K-fold evaluation, users need at least K likes; other users stay train-only.
Their eligible likes are shuffled once and partitioned into K disjoint test
folds. The following fold is validation, and all remaining folds are training.
Each eligible interaction occurs in the test set exactly once per seed.

The absence of timestamps makes these random interaction splits, not temporal
forecasts. Missing interactions are unobserved, not verified dislikes. Synthetic
genre preferences and random popularity weights can favor particular models.
Do not select configurations using test scores or claim that LightGCN must win.

## Model definitions

- **Popularity:** number of training users liking each book.
- **Item-CF:** binary CSR user-item matrix; sparse item-item cosine similarities
  with zero diagonal; sum similarities to the user's training likes. Fit once.
  Zero-score candidates remain eligible under the shared ranking protocol.
- **NCF:** existing GMF + MLP architecture, trained with stable BPR softplus loss;
  Adam weight decay regularizes all parameters. A one-example batch preserves
  its batch dimension.
- **LightGCN:** symmetric normalized bipartite adjacency
  `D^(-1/2) A D^(-1/2)` stored as a sparse tensor; no added self-loops or activation
  functions; equally average layer-zero embeddings and all propagated layers.
  Score by user-item dot product. Train with BPR plus explicit L2 regularization
  on the sampled layer-zero embeddings. Zero-degree nodes use inverse degree 0.

The implementation runs deterministically on CPU. CPU thread count defaults to
one to avoid excessive overhead on this small graph. NCF and LightGCN use the
same splits, negative-sampling procedure, ranking rules and validation metric;
their regularization mechanisms differ as described above.

## Checkpoints and cold start

Each neural checkpoint stores model weights, training interactions, sorted ID
mappings, hyperparameters and experiment metadata. Loading reconstructs the
training graph and verifies the mappings. The graph is not stored in weights.
Inference scores are uncalibrated ranking scores, not probabilities or values
restricted to [0, 1]. Do not pass them directly into the current API's bounded
`RecommendationResult.score` without an explicit integration decision.

Unknown users and users with no training likes fall back to training popularity.
Books without training interactions are not scored by these collaborative
models. TF-IDF remains available for new users and books via content metadata.
For a known user, pass additional known likes through `--exclude` at inference;
an evaluation checkpoint knows only its training likes by default.

## Source

He et al. (2020), *LightGCN: Simplifying and Powering Graph Convolution Network
for Recommendation*, SIGIR. <https://arxiv.org/abs/2002.02126>
Implementation reference: <https://github.com/gusye1234/LightGCN-PyTorch>.
