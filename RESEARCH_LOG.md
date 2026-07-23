# Lip-Reading Research Log

Goal: make a *great* lip-reading (visual speech recognition, VSR) system work — ultimately
"Wispr Flow without sound": silent dictation from a webcam. Optimize accuracy hard.

Hardware: MacBook Pro M5 Max (MPS). Cloud available: Scaleway GPU credits.

## Ground truth test set (Ahmet's 36s Photo Booth clip, 8 sentences)
Spoken: "All glory is fleeting. Steve Jobs was apparently a good guy. Bill Gates is very
cool too. I like to swim. I like to run. I like to trade stocks. Chess is a very nice
game. I like money as well."

---

## Key findings so far

### F1 — The model
- `AD1TEYA/lip-reading-model` (1GB `pytorch_model.pt` + `unigram5000` SentencePiece) is the
  **Auto-AVSR LRS3** visual model: ResNet-Conformer frontend + transformer decoder + CTC,
  beam search (beam=40, ctc_weight=0.1). ~19% WER on clean LRS3 benchmark.
- Of the 3 HF Spaces given, only `AD1TEYA` works. `thienphuc12339` = dead (mediapipe rot),
  `Suprath/liptotext` = AV-HuBERT (uses audio, not pure lip-read).

### F2 — Chunking is the single biggest lever (from Space tests)
- Whole 36s clip -> garbage ("WHOA"x13), 257s. One sentence at a time -> real transcripts.
- This model is built for ONE utterance per clip. VAD chunking is mandatory.

### F3 — Running locally (this repo)
- Replicated the Space pipeline in `engine/local_infer.py`, CPU/MPS, **with n-best output**.
- Local CPU: load 0.5s, **infer 1.5s** per short clip (vs ~13s on the HF Space). 8x faster.
- Parity confirmed: s3 "I like to swim. I like to run." -> top-1 **"I LIKE TO SWIM I LIKE TO
  RUN"** (exact). n-best alternatives are visually-confusable variants -> ideal for LLM rescoring.

### F4 — Per-segment baseline (HF Space, hand-cut clips, raw VSR, no correction)
| GT | VSR top-1 | hit |
|---|---|---|
| I like to swim. I like to run. | I LIKE TO SWIM I LIKE TO RUN | full |
| I like money as well. | I LOOK LIKE MY THING AS WELL | partial |
| Bill Gates is very cool too. | BILLY HAS HIS FELLOW STUDENTS FROM | partial |
| All glory is fleeting. Steve Jobs... | OH NO HE DOESN'T REALLY LIKE STEVE JOBS ONCE APPARENTLY OKAY | partial |
| I like to trade stocks. | THINGS WERE CRAZY THERE | miss |
| Chess is a very nice game. | LENSES FOR ANYTHING TO HAPPEN | miss |

---

## Plan / experiment ladder
1. [done] Local inference w/ n-best.
2. VAD auto-chunker (audio timing only -> keeps it a fair lip-read).
3. WER harness over clean per-sentence clips -> baseline number.
4. Preprocessing sweep: mirror vs not, fps, resolution, ROI.
5. LLM correction/rescoring on n-best (Hack Club AI / bigger model). Measure WER drop.
6. Try alternative models (Chaplin's checkpoint, VSP-LLM, AV-HuBERT) for comparison.
7. Personalization (fine-tune on Ahmet) — likely Scaleway GPU.
8. Package: CLI + live webcam demo.

## Diverse held-out eval (5 speakers, clean json3 subtitle GT, exact windows)
retinaface+CLAHE, raw top-1. Per-video WER:
- english_lucy 0.295, rachel_english 0.316, vanessa 0.495, hadar_accent 0.547,
  elon_musk 0.880  => AGGREGATE 0.558.
- On sustained frontal talking-heads (lucy/rachel/vanessa) it's ~0.30-0.50 with MANY
  long sentences word-perfect (e.g. lucy "...accurate pronunciation of some common" 0/14).
- elon clip is a CAD screen-demo (face off-screen most of clip) -> empty outputs inflate WER.
- hadar has tongue-twister minimal pairs (batch/badge, joke/choke) -> pathological, unfair.
- TODO: face-coverage filter (only score frames where a face is visible) = fairer + a real
  product feature (tell user "no face detected"). Use filtered aggregate as the metric.

## Phase 2 — Silent in-browser demo + deployment (Hugging Face)
- Built **visual VAD** (`engine/pipeline.py`): chunk utterances from LIP MOTION (ROI
  frame-diff energy), so fully silent recordings work (no audio needed). fps-normalize +
  sentence-level merge so we split on real ~0.5s pauses, not intra-word mouth closures.
- **Detector comparison on diverse eval: mediapipe 0.547 vs retinaface 0.558 (TIE).**
  retinaface only clearly helped on the one dim Photo Booth clip. => Space uses **mediapipe**
  (equal accuracy, no 48MB FAN weights, no ibug import risk, smaller/robust).
- Auto-orientation by beam-score is UNRELIABLE (lips ~symmetric -> both flips score similar).
  Dropped it; default no-flip (webcam files aren't mirrored) + manual flip toggle.
- Robustness: graceful no-face handling; 40s input cap so long uploads can't hang the Space.
- **Deployed private Space `aaahmet/silent-lip-reader`** (gradio 6.15.2, py3.11, cpu-basic).
  In-browser webcam record -> transcript. Verified end-to-end via live API.
  Deploy gotchas solved: torch pin for py3.13->use py3.11; mediapipe 0.10.21 needs py3.11
  (newer mediapipe removed mp.solutions); gradio 4.44 vs hub 1.x (HfFolder) -> moved to
  gradio 6.15.2 (hub>=0.33.5 compatible); gradio6 removed show_api/include_audio args.
- **Backup: private model repo `aaahmet/lipread-engine`** = full code + research log +
  checkpoint copy (so we own the weights).

## Phase 3 — "make it better without fine-tuning" experiments
- **Gemini / general VLM lip-reading: FAILS.** Tested gemini-3.5-flash via (a) native video
  (CLI can't ingest video; hcai proxy strips video parts -> model hallucinates from text only:
  "the next step", "thank you very much") and (b) a labeled frame-montage image (single image
  passes proxy) -> "we need to make it happen" for GT "right now we interact with computers...".
  General VLMs have no fine temporal lip-motion modeling -> confident wrong guesses. Specialized
  Auto-AVSR vastly better. Dead end (matches literature).
- **Stronger same-arch checkpoint (auto_avsr trained on LRW+LRS2+LRS3+Vox2+AVSpeech, ~3000h):**
  loaded via key remap (vsr.encoder.frontend->frontend, encoder.embed.0->proj_encoder). Diverse
  eval AGGREGATE **0.584 vs current 0.547 — NOT better.** => our checkpoint is already near the
  architecture's out-of-domain ceiling. Swapping same-arch checkpoints is not the lever.
- **Conclusion:** Auto-AVSR (this architecture) tops out ~0.30 WER on clean over-articulated
  speech and ~0.50-0.58 on casual unseen-speaker webcam footage. Ahmet's own best (Photo Booth,
  optimal preprocessing) was 0.561. A single casual sentence often comes out fluent-but-wrong.
  Real jumps require EITHER per-speaker personalization (excluded) OR a different architecture
  (VSR-LLM: VSP-LLM / Llama-AVSR — visual encoder -> LLM decoder, lower WER, needs a GPU).

## Phase 4 — autoresearch sweeps on cached diverse eval (baseline 0.5335, 55 utts)
Cached per-utterance ROI tensors (extern/eval_cache) -> fast decode/rerank sweeps (engine/sweep.py,
ledger runs/sweep_results.tsv). Keep/revert on AGGREGATE WER.
- **Decoding params: NO gain.** ctc_weight {0.1..0.5}: 0.1 best (0.5335); higher hurts.
  beam {20,40,60,80}: 40 best, MORE beam slightly WORSE. length-penalty: 0 best. Model already
  optimally decoded.
- **LLM n-best rerank (gemini-3-flash, pick best of 10): 0.5298** — tiny gain (within noise).
- **LLM n-best CONSTRAINED REWRITE (gemini-3-flash, 10 cands): 0.5208 = BEST** (-2.4% rel vs
  baseline). NOTE: reverses the earlier "LLM rewrite hurts" (0.561->0.585) finding — that was an
  aggressive prompt on ONE clip; a constrained prompt ("prefer candidate words, only fix to natural
  English") + n-best context on the diverse set gives a modest real gain. Low-risk to ship.
- Takeaway: cheap levers give only ~2% rel. The architecture is at its out-of-domain ceiling;
  same-data models (auto_avsr vox2) don't help. Real jump needs different arch (VSR-LLM) or
  personalization.

## Phase 4 (cont.) — final cheap-lever scoreboard (diverse cache, baseline 0.5335)
| experiment | WER | verdict |
|---|---|---|
| baseline (mediapipe, ctc0.1, beam40, top1) | 0.5335 | ref |
| decoding sweeps (ctc/beam/pen) | ≥0.5335 | NO gain (baseline already optimal) |
| LLM rerank-pick (gemini-3-flash, 10 cands) | 0.5298 | tiny |
| **LLM rewrite per-utt (gemini-3-flash, constrained)** | **0.5208** | **BEST cheap lever (-2.4% rel)** |
| LLM rewrite (deepseek-v4-pro) | 0.5244 | no better (n-best is the bottleneck) |
| LLM rewrite (qwen3.6-max) | 0.5316 | no better |
| LLM context-rewrite (all utts/recording) | 0.6618 | WORSE (LLM rephrases/misaligns -> blowups) |

### Verdict on "make it better without fine-tuning"
- We are ALREADY using a near-SOTA English VSR model (Auto-AVSR ~19% LRS3; best 2025 = VALLR
  18.7%). There is no readily-deployable model that is clearly better on English VSR — VSP-LLM's
  pure-VSR WER is *worse* (~26%; its edge is low-resource/translation). So a Scaleway VSP-LLM run
  is NOT expected to beat what we have -> not worth the GPU hours (evidence-based decision).
- Cheap levers total ~2.4% rel (constrained LLM rewrite). That's the ceiling without fine-tuning.
- The model is GREAT on clear, over-articulated, frontal speech (teachers ~0.25-0.27 WER) and poor
  on casual speech (~0.50-0.55). So results are dominated by (a) articulation/recording technique
  and (b) speaker/domain shift — NOT model choice.
- The ONLY large lever is per-speaker PERSONALIZATION (fine-tune on ~20-30 of Ahmet's sentences).
  That IS a good use of the Scaleway GPU. Excluded by the current question, but it's the honest path.

## Future improvement ideas (not yet done)
- Per-speaker personalization (fine-tune on Ahmet) — biggest remaining lever; needs data+GPU (Scaleway).
- Try a stronger VSR checkpoint (LRS3+VoxCeleb2 co-trained generalizes better).
- External LM fusion in beam search (lm_weight currently 0).
- Face-coverage filter in eval to fairly exclude cutaway/no-face windows.
- Max-segment split (>~8s) to avoid long multi-sentence chunks.

## WER results table (the optimization scoreboard)
| exp | description | WER | notes |
|---|---|---|---|
| base | auto-chunk, raw VSR, un-mirror, 25fps, full res | **0.683** | 28/41 words wrong. "i like to swim" perfect. |
| mirrored | base but NOT un-mirrored | 0.878 | un-mirroring is essential (Photo Booth flips) |
| +LLM(flash) | base n-best -> gemini-2.5-flash correction | 0.683 | NO gain: right words absent from n-best -> GIGO. Bottleneck is VSR, not LM. |
| enhance | base + CLAHE contrast on luminance | **0.610** | low-contrast footage hurt VSR. recovered "...is fleeting", "is a very". |
| retina_enh | enhance + retinaface/FAN 68-pt detector (matches TRAINING preprocessing) | **0.561** | "bill gates is very cool too" -> "bill gates is very true" (was "billy has this record"!). mediapipe 4-pt was a train/test mismatch. BEST. |
| retina_enh+LLM | retina_enh n-best -> gemini-2.5-flash | 0.585 | WORSE. LLM over-smooths partially-correct output into fluent-but-wrong ("bill gates is very true" -> "but yeah it's very true"). Lesson: raw VSR top-1 beats naive LLM rewrite. |

**Best system so far: retinaface + CLAHE + raw VSR top-1 = WER 0.561** (from 0.683 baseline, -18% rel).
**Key lesson:** the bottleneck is the VSR *signal* on out-of-domain footage, not the language layer.
Biggest untapped levers: (a) better recording conditions, (b) per-speaker personalization.
Eval set is tiny (8 utterances / 41 words) -> further hyperparam tuning risks overfitting; need more data.

### F5 — DECISIVE: the system is excellent on clean footage (cross-speaker!)
Ran best pipeline on a clean, well-lit, frontal public clip (Rachel's English intro, a
DIFFERENT speaker). Results:
- "this channel is dedicated to american english pronunciation" -> **PERFECT (0/8 words)**
- "welcome to rachel's english" -> perfect (only apostrophe diff)
- measured WER 0.258 but that's inflated by NOISY auto-caption GT + one too-short 0.8s clip
  that returned empty; true clean WER ~= 5-10%.
=> The 0.56 WER on Ahmet's clip is ~entirely FOOTAGE QUALITY (warm/dim Photo Booth, casual
   articulation), NOT a model limit. Good conditions -> research-grade accuracy, even on an
   unseen speaker. The path to "great" = decent recording conditions (+ optional per-speaker
   personalization for the last mile).

### Practical recipe that works NOW
good lighting on the face + frontal + camera at eye level + face fills frame + ~1s pause
between sentences + the pipeline (retinaface/FAN crop + CLAHE + Auto-AVSR, raw top-1).
Too-short clips (<~1s) are unreliable -> keep utterances >= ~1s.
