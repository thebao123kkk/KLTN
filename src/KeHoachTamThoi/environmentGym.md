# Kế Hoạch Giai Đoạn Tiếp Theo (Bước kế tiếp sau Module 2)

> **Thời điểm lập kế hoạch**: 2026-10-23 00:55 +07:00
> **Trạng thái hiện tại**: Module 1 (Fault Injection) + Module 2 (Telemetry Collector) đã hoàn thiện.
> **Giai đoạn tiếp theo**: Module 3 (Custom SDN Gym Environment) + Module 4 (PPO RL Agent).
> **Tham chiếu thiết kế**: Model_Research_and_Implementation_Plan.md (Mục 4, 6, 7, 8) và cau_truc_tu_phuc_hoi_sdwan.md.

---

## Trạng Thái Đã Hoàn Thành

| Module | Trạng thái | File chính |
| :--- | :---: | :--- |
| M1: Fault Injection Framework (F01-F12) | XONG | fault_injection/fault_injector.py, scenarios/*.py |
| M2: Telemetry Collector & State-Vector Synthesizer | XONG | ai_engine/telemetry/collector.py, prometheus_client.py, vector_assembler.py, fault_log_reader.py, context_metadata_parser.py |
| M2: Exporter & Cau hinh | XONG | controller/sdn/telemetry_exporter.py, config/prometheus.yml, config/telemetry_config.yaml, telemetry_collector.py |
| M2: Kiem thu | XONG | tests/test_telemetry.py (11/11 pass), tests/check_telemetry_pipeline.py |

**Dau ra san co**: data/sdn_telemetry_dataset.csv -- Dataset 15 cot, chu ky 10s

---

## Giai Doan Tiep Theo: Module 3 + Module 4

### Cau Truc File Can Tao Moi

    src/
    ai_engine/
        telemetry/              [XONG]
        environment/            [MOI - MODULE 3]
            __init__.py
            sdn_gym_env.py      Custom Gymnasium Environment
            reward_calculator.py  Severity-Weighted Reward Function
            dataset_loader.py   Doc & tien xu ly CSV Dataset
        ppo_agent/              [MOI - MODULE 4]
            __init__.py
            train.py            Huan luyen PPO + TensorBoard
            evaluate.py         Danh gia & so sanh baseline
            transfer_learning.py  Transfer Learning sang topology lon hon
    tests/
        test_telemetry.py       [XONG]
        test_gym_env.py         [MOI] Unit test sdn_gym_env.py
        test_reward.py          [MOI] Unit test reward_calculator.py
    data/
        sdn_telemetry_dataset.csv  [Dau vao M3/M4]
        models/                    [MOI] Luu model weights PPO

---

## MODULE 3: dataset_loader.py

- Doc CSV bang pandas, anh xa 8 cot so lieu thanh np.ndarray float32.
- Cot fault_label -> encode phi_t: NONE=0, SOFT_WARNING=1, TEMP_WARNING=2,
  FLOW_ERROR=3, PORT_FAULT=4, LINK_FAULT=5, FAUCET_RELOAD=6
- Ho tro che do sequential va random_episode.
- Chuan hoa (normalize) cac cot counter bang MinMax hoac Z-score.

## MODULE 3: reward_calculator.py

Bang tham so Severity-Weighted Reward:

| phi_t | rho (phat) | beta (thuong) |
| :--- | :---: | :---: |
| LINK_FAULT | -10 | +12 |
| PORT_FAULT | -7 | +10 |
| FLOW_ERROR | -5 | +8 |
| SOFT_WARNING | -2 | +2 |
| TEMP_WARNING | -1 | +1 |
| NONE | 0 | no-op +2, can thiep thua -1 |
| FAUCET_RELOAD | N/A | +20 co dinh |

Cong thuc:
  r_t = +20                             neu phi==FAUCET_RELOAD va a_t in {1,2,3}
      = -2*pdown - ferr - rho - duration  cong:
        + beta               neu a_t in {1,2,3}
        + 2                  neu phi==NONE va a_t==0
        - 1                  neu phi==NONE va a_t in {1,2,3}

## MODULE 3: sdn_gym_env.py

API Gymnasium:
  observation_space: Box(shape=(8,), dtype=float32)
  action_space:      Discrete(4)  -- {0, 1, 2, 3}
  reset(seed=None) -> (obs, info)
  step(action)     -> (obs, reward, terminated, truncated, info)

---

## MODULE 4: train.py

Cau hinh PPO (stable-baselines3):
  policy="MlpPolicy"
  learning_rate=2.5e-4
  clip_range=0.35      (eps=0.35 trong L^CLIP)
  n_steps=2048
  batch_size=64
  n_epochs=10
  total_timesteps=10_000

KPI nghiem thu:
  Episode Reward trung binh >= 1550
  Episode Length trung binh >= 2200 buoc
  Do thi TensorBoard hoi tu on dinh

## MODULE 4: evaluate.py

3 phuong phap duoc so sanh qua 50 su co loi:
  1. No-Healing Baseline: khong co agent
  2. Rule-Based Reactive: if pdown>0 -> a=1; if ferr>0 -> a=3; if fdisc>0 -> a=2; else a=0
  3. PPO_FH2: mo hinh de xuat

KPIs do dac:
  T_recovery    <= 26 giay (2.6 buoc * 10s)
  PL_proxy      <= 3.2%
  OF_error_rate <= 0.38 loi/buoc
  SRR           >= 85%

## MODULE 4: transfer_learning.py

  Linear 8 switches: fine-tune 5000 steps, Episode Reward >= 1442
  Fat-tree 16 switches: fine-tune 5000 steps, Episode Reward >= 1386

---

## Thu Tu Thuc Hien Khuyen Nghi

  Buoc 1:  ai_engine/environment/dataset_loader.py
  Buoc 2:  ai_engine/environment/reward_calculator.py
  Buoc 3:  ai_engine/environment/sdn_gym_env.py
  Buoc 4:  tests/test_gym_env.py + tests/test_reward.py
  Buoc 5:  ai_engine/ppo_agent/train.py
  Buoc 6:  ai_engine/ppo_agent/evaluate.py
  Buoc 7:  ai_engine/ppo_agent/transfer_learning.py

---

## Luu Y Quan Trong

  Phu thuoc du lieu: Can dam bao data/sdn_telemetry_dataset.csv da co
  du mau da dang nhan fault_label (7 loai) truoc khi huan luyen.

  Moi truong chay: PPO Training yeu cau Linux hoac WSL2, Python 3.8+,
  stable-baselines3, gymnasium, torch.

  Dependencies: Kiem tra requirements.txt da co stable-baselines3[extra],
  gymnasium, tensorboard.
