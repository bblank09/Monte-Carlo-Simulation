# Monte Carlo Portfolio Simulation (Webull TH × SEC Open Data) — Design Spec

> **Archived / superseded:** this notebook-era design describes the former mixed
> Webull/yfinance/US-ticker scope. The shipped webapp contract is SEC-only and is
> documented in `README.md`, `CLAUDE.md`, and the 2026-08-04 implementation reference.

**Date:** 2026-07-26
**Course context:** ต่อยอดจาก CQF Module 1-2 (ดู `learn.cqf/CQF Module 1-2 Master Overview.md`)
**Goal:** สร้าง 3 Jupyter Notebook ที่ลอกโครงสร้าง input/output ของ 3 เครื่องมือใน [Portfolio Visualizer](https://www.portfoliovisualizer.com/analysis) หมวด "Monte Carlo Simulation" มาทั้งหมด แต่ implement ด้วยสมการที่มาจาก CQF Module 1-2 เอง ทีละขั้น พร้อมอธิบายที่มา และ benchmark ผลลัพธ์กับ Portfolio Visualizer จริง

---

## 1. เหตุผล/บริบท

อาจารย์มอบหมายให้ทำโปรเจกต์ Monte Carlo Simulation โดยอ้างอิง 4 แหล่ง: Portfolio Visualizer, SEC Open Data (Thailand), Webull TH, riskfolio-lib เงื่อนไขสำคัญคือ **ผู้เรียนต้องเข้าใจและอธิบายที่มาของทุกสมการได้เอง** ไม่ใช่ให้ AI ทำให้แล้วอธิบายไม่ได้ ดังนั้นทุก notebook ต้องมี markdown อธิบายที่มาสมการก่อน แล้วค่อย implement ทันทีหลังจากนั้น

## 2. ขอบเขต (locked จากบทสนทนา)

- **3 notebook แยกไฟล์อิสระ** แต่ละไฟล์ต้องอ่านจบได้ในตัวเอง (stand-alone) — ไม่ import โค้ดร่วมกันข้ามไฟล์ แม้จะมีเนื้อหาซ้ำกันบ้าง (ตั้งใจ เพื่อทวนความเข้าใจทุกครั้ง)
  1. `01_monte_carlo_simulation.ipynb`
  2. `02_financial_goals.ipynb`
  3. `03_asset_liability_modeling.ipynb`
- **สินทรัพย์ (ยืนยันแล้ว 5 ตัว)**: **หุ้นสหรัฐฯ** — SPY (S&P 500 ETF), QQQ (Nasdaq 100 ETF), TLT (20+Y Treasury Bond ETF) + **กองทุนไทยผ่าน SEC Open Data** — K หุ้นทุน (`M0027_2535`), K SET50 (`M0209_2548`)
  - **แก้ไขจากรอบก่อน (ครั้งที่ 1)**: ตอนแรกวางแผนใช้หุ้นไทย (SET) จาก Webull TH แต่เปลี่ยนเป็นหุ้นสหรัฐฯ แทน เพราะ Webull TH เทรดหุ้นสหรัฐฯ ได้ด้วย และ ticker สหรัฐฯ ใส่ Portfolio Visualizer ได้ตรงๆ (เทียบ asset-to-asset ได้จริงสำหรับฝั่งหุ้น) — ส่วนฝั่งกองทุนยังคงเป็นกองทุนไทยเพราะ SEC Open Data มีแต่ข้อมูลกองทุนไทยเท่านั้น ไม่มีทางเทียบตรงกับ PV ได้ไม่ว่าจะเลือกกองทุนไหน (ดู section 7 วิธีเทียบฝั่งกองทุน)
  - **แก้ไขจากรอบก่อน (ครั้งที่ 2)**: ทดสอบดึงราคา SPY/QQQ/TLT ผ่าน **Webull TH OpenAPI จริง** สำเร็จครั้งแรก (ยืนยัน region `"th"` + `Category.US_ETF` + `Timespan.D`) แต่เมื่อเรียกซ้ำเพื่อยืนยันความเสถียร token verification ค้างที่ `PENDING` แล้ว `EXPIRED` 3 จาก 4 ครั้งที่ลอง (`ERROR_CHECK_TOKEN`) — เปลี่ยนมาใช้ **`yfinance`** แทนเป็นแหล่งข้อมูลราคาหุ้นสหรัฐฯ ที่เสถียรกว่า (ยืนยันราคาตรงกับที่ Webull เคยส่งกลับมาจริง: SPY ปิด 2026-07-24 = 738.93 ตรงกันทั้งสองแหล่ง) — Webull App Key/Secret ยังเก็บไว้ใน `.env` เผื่อกลับมาแก้ปัญหา authentication ในอนาคต
- **Input ทุก field ต้องตั้งค่าได้เหมือน Portfolio Visualizer ทุกตัว ไม่ตัดออก** รวมถึง 4 Simulation Model (Historical / Forecasted / Statistical / Parameterized Returns) ต้อง implement คณิตศาสตร์เต็มรูปแบบครบทั้ง 4 แบบ ไม่ใช่แค่ Statistical
- **แก้ไขจากรอบก่อนหน้า**: ตอนแรกตกลง scope ไว้แค่ "GBM+Markowitz+VaR พื้นฐาน" ไม่รวม GARCH — แต่จากการสำรวจ DOM จริงพบว่า PV มี **Time Series Model = GARCH Model** เป็นตัวเลือกในหน้าเดียวกับ Simulation Model และ **Distribution = Fat-Tailed** ในหน้า Parameterized ดังนั้นเพื่อให้ตรงกับคำสั่ง "เอาเหมือนกันเลย (เหมือน PV ทุก field)" ต้อง **implement GARCH(1,1) time-series model ด้วย** (ตรงกับ JA252.5 ที่มีอยู่แล้วใน `learn.cqf/`) ไม่ใช่แค่ Normal Returns
- **Benchmark**: กรอก input ชุดเดียวกันในเว็บ Portfolio Visualizer จริง เก็บ screenshot/ตัวเลขไว้ใน `benchmarks/` แล้วเทียบกับผลจาก engine ของเราในทุก notebook
- แต่ละ notebook เขียนเป็น**รายงานมืออาชีพ**: คืออะไร → ที่มา/ความสำคัญ → การดำเนินงาน → ผล → สรุป
- Financial Goals และ Asset Liability Modeling มีคณิตศาสตร์ที่**เกินเนื้อหา CQF Module 1-2 โดยตรง** (glide path, PV of liability, funding ratio) — ยอมรับได้ตามที่ผู้ใช้ระบุว่า "เกิน scope ก็ไม่เป็นไร เอาไว้เรียนรู้" ต้องระบุชัดเจนใน notebook ว่าส่วนไหนต่อยอดนอกเหนือจากที่เรียนมา

## 3. โครงสร้างไฟล์โปรเจกต์

```
Monte Carlo Simulation Webull:SEC OPENAI/
├── data/
│   ├── raw/                          # ราคาหุ้น Webull TH + NAV กองทุน SEC Open Data ดิบ
│   └── processed/                    # log-return, μ, Σ ที่คำนวณแล้ว (cache)
├── notebooks/
│   ├── 01_monte_carlo_simulation.ipynb
│   ├── 02_financial_goals.ipynb
│   └── 03_asset_liability_modeling.ipynb
├── benchmarks/
│   ├── monte_carlo/                  # screenshot + export จาก PV จริง (tool 1)
│   ├── financial_goals/              # (tool 2)
│   └── asset_liability/              # (tool 3)
├── docs/superpowers/specs/           # ไฟล์นี้ + plan implementation
└── README.md                         # สารบัญ เชื่อม 3 รายงาน + assumption ร่วม
```

## 4. Template โครงสร้าง Notebook (ใช้ร่วมกันทั้ง 3 ไฟล์)

```
Title + Executive Summary
1. Introduction                  — คืออะไร ใช้ทำอะไรจริง ทำไมสำคัญ
2. Theoretical Background        — ที่มาสมการจาก CQF Module 1-2 ไล่ทีละขั้น (markdown+LaTeX)
3. Methodology
   3.1 Data Source & Acquisition       (Webull TH / SEC Open Data)
   3.2 Parameter Estimation            (μ, Σ จากข้อมูลจริง)
   3.3 Portfolio Construction          (Markowitz weight)
   3.4 Simulation Model Configuration  ← ตาราง "PV input field → ค่าที่ใช้" ครบทุก field
   3.5 Algorithm Summary               (pseudocode ก่อนลงโค้ด)
4. Implementation                — code cell ตาม 3.1-3.4 ทีละสมการ
5. Results
   5.1 Output ตรงกับ PV: percentile fan chart, ending-balance histogram, success rate
   5.2 Benchmark comparison: PV จริง (screenshot) vs engine เรา + ตาราง diff
6. Discussion                    — ต่างกันตรงไหน ทำไม
7. Conclusion & Limitations
Appendix                          — glossary สูตรทั้งหมด + reference
```

## 5. รายละเอียดเฉพาะแต่ละ notebook

### 5.1 `01_monte_carlo_simulation.ipynb`

**PV tool ต้นแบบ**: [Monte Carlo Simulation](https://www.portfoliovisualizer.com/monte-carlo-simulation) — จำลองพอร์ตเดียว growth/survival

**ยืนยันจากการทดสอบจริงบนเว็บ (ตั้งค่า + กด Run Simulation โดยไม่ login)**: ทุก field ด้านล่างใช้งานได้เต็มรูปแบบไม่มี paywall — ทดสอบจริงกับ SPY 100%, $1,000,000, Historical Returns model ได้ผลลัพธ์ครบ (percentile table, portfolio balance chart, end-balance histogram) เฉพาะ **Save/PDF/Excel export** เท่านั้นที่ login-gated (`enableExport=false`, `saveSimulation()` เรียก `showLoginPrompt(true)`) — ไม่กระทบเรา เพราะเราแค่ต้องการตัวเลข/กราฟไปเทียบ ไม่ต้อง export จากเว็บ

**Full input config (ต้องมีครบ — ยืนยันจาก DOM จริง):**
Portfolio Type (Asset Classes/Tickers) · Initial Amount · Cashflows (No cashflow / Contribute fixed / Withdraw fixed / Withdraw % / Rolling avg spending rule / Geometric spending rule / Life-expectancy withdrawal / Import custom sequence) · Withdrawal Amount · Inflation Adjusted · Withdrawal Frequency · Life Expectancy Model + Current Age (เมื่อเลือก life-expectancy withdrawal) · Simulation Period (Years) · Tax Treatment (Pre/After-tax) · **Investment Horizon (Simulated Period / Perpetual)** · Federal/Capital Gains/Dividend/ACA/State Income Tax (ใช้เมื่อ After-tax) · **Simulation Model (Historical / Forecasted / Statistical / Parameterized Returns — implement ทั้ง 4)** · **Time Series Model (Normal Returns / GARCH Model)** ← ใช้ตอน Forecasted หรือ Statistical · Risk-Free Rate · **Use Historical Volatility (Yes/No)** · **Use Historical Correlations (Yes/No) + import Correlation Matrix เอง** · Use Full History · Start Year / End Year · Bootstrap Model (Single Month/Year/Block of Years) · Block Min./Max. Years + **Circular Bootstrapping (Yes/No)** (เมื่อ Block of Years) · **Distribution (Normal / Fat-Tailed) + Degrees of Freedom** (เมื่อ Parameterized) · Expected Return/Volatility ต่อสินทรัพย์ (เมื่อ Forecasted) · Sequence of Returns Risk (No adj / Worst 1-10 Years First) · Inflation Model (Historical/Parameterized) + Inflation Mean/Volatility · Rebalancing (None/Annual/Semi/Quarterly/Monthly) · Intervals (Defaults/Custom) + Percentile/Return Intervals · Asset Allocation (ticker + weight% สูงสุด 10 ตัว)

**Insight สำคัญ**: Time Series Model มีตัวเลือก **GARCH Model** และ Distribution มีตัวเลือก **Fat-Tailed** อยู่ในตัวเว็บอยู่แล้ว — แปลว่าส่วนที่เคยคิดว่า "เกิน scope CQF" (JA252.4-5 stylized facts/GARCH) จริงๆ แล้ว**อยู่ในสิ่งที่ PV รองรับ** ถ้าจะ "ลอก PV มาทั้งหมด" ตามที่ตกลงกัน ต้อง implement ทั้ง Normal และ GARCH time-series model ด้วย ไม่ใช่แค่ Normal

**คณิตศาสตร์ CQF ที่ใช้:**
- JA251.1 (Random walk → GBM, √δt scaling)
- JA251.4-5 (Itô's Lemma, analytic GBM solution, Euler method, correlated random walk ผ่าน Cholesky ของ Σ)
- JA252.1 (μ_π=w'μ, σ_π²=w'Σw, Sharpe ratio, efficient frontier)
- JA252.2 (Lagrange derivation ของ tangency/min-variance portfolio, เทียบกับ `riskfolio-lib`)
- JA252.3 (VaR/ES ทั้ง parametric formula และจาก simulated distribution)

**4 Simulation Model ต้อง implement เป็น:**
1. **Historical Returns** — bootstrap resampling ปีจริงจากข้อมูล Webull/SEC ย้อนหลัง (สุ่มเลือกปีใส่แทน) — Bootstrap Model ย่อย (Single Month/Year/Block of Years) + Circular Bootstrapping ตามที่พบจริงใน DOM
2. **Forecasted Returns** — ใช้ μ, σ ที่กำหนดเอง (ไม่ estimate จากข้อมูล) จำลองด้วย **Time Series Model = Normal Returns หรือ GARCH Model** (เลือกได้ทั้งคู่)
3. **Statistical Returns** — multivariate Normal จาก μ,Σ ที่ประมาณจากข้อมูลจริง (= GBM/correlated random walk ตาม CQF ตรงๆ) เช่นกันเลือก **Time Series Model = Normal หรือ GARCH** ← core ที่ derive ละเอียดสุด, GARCH(1,1) ใช้สมการจาก JA252.5 ตรงๆ
4. **Parameterized Returns** — เลือก **Distribution = Normal หรือ Fat-Tailed (Student-t พร้อม Degrees of Freedom)** ใส่ parameter เอง ไม่ estimate จากข้อมูล

### 5.2 `02_financial_goals.ipynb`

**PV tool ต้นแบบ**: [Financial Goals](https://www.portfoliovisualizer.com/financial-goals)
**ยืนยันจากการทดสอบจริง**: ทุก field ใช้งานได้เต็มรูปแบบไม่มี paywall (เช็ค DOM: `disabledSelects: []`, `disabledInputs: []`, ปุ่ม Run Simulation ไม่ disabled)

**Input เพิ่มจาก 01 (ยืนยันจาก DOM จริง)**:
- Planning Type (Single stage/Multistage) · Years to Retirement · Glide Path Years
- พอร์ตมี **2 ชุด allocation แยกกัน**: Start Portfolio + Ending Portfolio (แต่ละชุดมี asset 1-10 ครบเหมือน 01)
- **Financial Goals — สูงสุด 3 Goal block (Goal #1/#2/#3)** แต่ละ goal มี field ของตัวเองครบชุด: Cashflow type · Amount/Percentage · Inflation Adjusted · Rolling average periods · Smoothing rate · Annual change · Starts (ปีเริ่ม) · Years till start · Frequency · Repeat Type · Times
- **Worst Years At Retirement** (sequence-of-returns stress test เฉพาะช่วงเกษียณ — เพิ่มจาก Sequence of Returns Risk ปกติของ 01)
- field พื้นฐานอื่นๆ (Simulation Model, Time Series Model/GARCH, Tax, Rebalancing ฯลฯ) เหมือน 01 ทุกตัว

**คณิตศาสตร์เพิ่ม (นอกเหนือ CQF โดยตรง — ต้องระบุในรายงาน):**
- Glide path: `w(t) = w_start + (t/glide_years)·(w_end − w_start)`
- Multi-goal cashflow: แต่ละ goal ฉีด/ถอนเงินตาม Repeat Type/Times ที่ปีต่างๆ เข้า Euler loop เดียวกับ 01

### 5.3 `03_asset_liability_modeling.ipynb`

**PV tool ต้นแบบ**: [Asset Liability Modeling](https://www.portfoliovisualizer.com/asset-liability-modeling)
**ยืนยันจากการทดสอบจริง**: ทุก field ใช้งานได้เต็มรูปแบบไม่มี paywall (เช็ค DOM เหมือนกัน — ไม่มี field ไหน disabled)

**Input เพิ่มจาก 01 (ยืนยันจาก DOM จริง)**:
- Current Assets · **Contributions** (None/Fixed periodic/Import) + Contribution Amount/Frequency/**Contributions Start**/**Repeat Contributions**/**Contribution Repeats** · Inflation Indexed (ฝั่ง contribution)
- **Liabilities** (Fixed periodic/Import) + Liability Amount/Frequency/**Liabilities Start**/**Repeat Liabilities**/**Liability Cashflow Repeats** · Inflation Indexed (ฝั่ง liability แยกจากฝั่ง contribution)
- Discount Rate % · Target Funding Ratio %
- field พื้นฐานอื่นๆ (Simulation Model, Time Series Model/GARCH, Tax, Rebalancing ฯลฯ) เหมือน 01 ทุกตัว

**คณิตศาสตร์เพิ่ม (นอกเหนือ CQF โดยตรง — ต้องระบุในรายงาน):**
- Present Value ของ liability: `PV = Σ Lₜ/(1+r)ᵗ`
- Funding Ratio: `Assets/PV(Liabilities)` — asset ฝั่งใช้ GBM engine เดิม (stochastic), liability ฝั่ง deterministic discounted cashflow
- Output หลัก = distribution ของ funding ratio ข้ามเวลา (ความน่าจะเป็นที่ funding ratio > target)

## 6. Data Pipeline (ร่วมทั้ง 3 notebook)

1. **Webull TH**: ต้องมี auth/login (พบว่า `webull.co.th/center` ต้อง sign-in) — ผู้ใช้ต้อง export ราคาย้อนหลังเอง หรือใช้ API key ที่มีอยู่แล้วใน `webull/apikey/`
2. **SEC Open Data** (ยืนยันจากการสำรวจ `secopendata.sec.or.th` จริง): endpoint ที่ต้องใช้คือ **`GET /v2/fund/daily-info/nav`** (product = "Fund", พบผ่าน `/api/apis-products-ms` catalog) — คืนค่า `nav_date`, `last_val` (NAV ต่อหน่วย), `net_asset`, `sell_price`, `buy_price` รายวัน รองรับ query param `proj_id` (เลือกกองทุนเดียว), `start_nav_date`/`end_nav_date` (ช่วงวันที่), `page_size`/`next_cursor` (pagination)
   - การเรียก API ต้องมี **`Authorization: Bearer <token>`** header — session ตอนเปิดหน้า docs ใช้ token ชั่วคราวที่ออกอัตโนมัติ (หมดอายุใน ~1 ชม.) สำหรับใช้งานจริงต้อง**สมัครบัญชีนักพัฒนา**ผ่านปุ่ม "เข้าสู่ระบบ"/"สมัครบัญชีสมาชิก" บนเว็บก่อน เพื่อขอ subscription key ถาวร — ยังไม่ได้ทดสอบขั้นตอนสมัครจริง (อยู่ใน open item ข้อ 9)
   - ต้องหา `proj_id` ของกองทุนที่จะใช้ก่อน (ค้นได้จาก endpoint `/v2/fund/general-info/profiles` ในชุด product เดียวกัน)
3. Cache ผลลัพธ์ (log-return, μ, Σ) ไว้ที่ `data/processed/` ให้ทั้ง 3 notebook อ่านค่าเดียวกัน (แต่โค้ด load ยังคง copy ในแต่ละไฟล์ ไม่ import ร่วม)

## 7. Benchmark Protocol

**แก้ไขจากรอบก่อนหน้า**: PV ไม่รองรับ ticker หุ้นไทยหรือ `proj_id` กองทุนไทย ดังนั้นเทียบ "สินทรัพย์เดียวกัน" ไม่ได้ — วิธีที่ถูกต้องคือเทียบที่ **เครื่องยนต์คำนวณ (engine)** ไม่ใช่ตัวสินทรัพย์:

1. คำนวณ μ, σ, correlation matrix จากข้อมูลหุ้น/กองทุนไทยจริงของเรา (output ของ Task 5)
2. กรอกตัวเลข μ/σ/correlation **ชุดเดียวกันเป๊ะ** เข้า PV เอง โดยใช้ **Simulation Model = Forecasted Returns** (มี field "Expected Return"/"Expected Volatility" ต่อสินทรัพย์ให้ใส่เอง) + **Use Historical Correlations = No + Correlation Matrix (import ไฟล์เอง)** — ไม่ใช้ Historical Returns ของ PV เพราะนั่นจะดึงข้อมูลราคาจริงของ ticker ที่เลือก ซึ่งเป็นคนละตลาดกับของเรา
3. รัน Monte Carlo ทั้งสองฝั่งด้วย initial amount, horizon, weight เดียวกัน → เก็บ screenshot + ตัวเลข summary ไว้ที่ `benchmarks/<tool>/`
4. ถ้าคณิตศาสตร์ของเราถูกต้อง ผลลัพธ์ (percentile table, fan chart) ควรใกล้เคียงกับของ PV มาก เพราะทั้งคู่จำลอง GBM ด้วยพารามิเตอร์เดียวกัน — ต่างกันแค่ engine ที่คำนวณ ไม่ใช่ต่างกันเพราะ "หุ้นไทยกับหุ้นอเมริกาให้ผลต่างกัน" (ซึ่งไม่เกี่ยวข้องกับสิ่งที่กำลังตรวจสอบ)
5. ใน notebook section 5.2 แสดงภาพ/ตัวเลขคู่กัน + อภิปรายส่วนต่างที่เหลือ (ถ้ามี) ว่ามาจากความแตกต่างของ random seed/sampling implementation ไม่ใช่มาจากสมมติฐานทางการเงินที่ต่างกัน

## 8. Out of scope (ชัดเจน)

- **GARCH implement เต็มรูปแบบแล้ว** (แก้จากรอบก่อน — ดู section 2/5.1) แต่**จำกัดแค่ GARCH(1,1)/GJR(1,1) ตาม JA252.5** ไม่ทำ volatility model ตระกูลอื่น (EGARCH, FIGARCH ฯลฯ) ที่ PV ก็ไม่รองรับอยู่แล้ว
- ไม่ทำ tax-treatment calculation จริงจัง (After-tax Returns เป็นแค่ toggle ลด return คร่าวๆ ไม่ implement ภาษีไทยจริง)
- ไม่ต้องทำ production deployment ใดๆ — เป็น notebook เพื่อการเรียนรู้/ส่งอาจารย์เท่านั้น

## 9. Open items ก่อนเริ่ม implementation

- ต้องยืนยัน: จำนวนหุ้น/กองทุนที่จะใช้จริง (กี่ตัว, ชื่ออะไร), initial amount, simulation period default, ช่วงเวลาข้อมูลย้อนหลัง — จะกำหนดเป็นค่า default ที่ปรับได้ใน config cell ของแต่ละ notebook
- **ต้องสมัครบัญชี SEC Open Data ก่อน** เพื่อขอ subscription key ถาวรสำหรับเรียก `/v2/fund/daily-info/nav` (token ที่เจอตอนสำรวจเป็นแค่ session ชั่วคราวของหน้า docs ใช้จริงไม่ได้) — ถ้าสมัครไม่ทัน ให้ fallback ไปดาวน์โหลด NAV เป็น CSV/Excel จากหน้าเว็บแทน (มีตัวเลือกนี้ให้ใช้แน่นอนตามที่เห็นในหน้า "ชุดข้อมูล")
- ต้องเช็คว่า Webull TH API key ที่อยู่ใน `webull/apikey/` ใช้ดึงราคาย้อนหลังได้จริงหรือไม่
- ต้องหา `proj_id` ของกองทุนที่จะใช้จริงผ่าน `/v2/fund/general-info/profiles` ก่อนเรียก NAV API

## 10. Implementation Mode (สำคัญ — วิธีทำงานตอน implement)

ผู้ใช้ระบุชัดเจนว่า**ต้องสอนไปทีละขั้นตอนพร้อมกับทำ ไม่ใช่สร้าง notebook เสร็จสมบูรณ์แล้วส่งให้ทีเดียว** ดังนั้น implementation plan และการ execute ต้องยึดหลัก:

- ทำทีละ section ตาม template ใน section 4 (เช่น derive GBM ก่อน → หยุดอธิบาย/เช็คความเข้าใจ → ค่อย implement เป็นโค้ด → หยุดอีกครั้งก่อนไป section ถัดไป)
- ทุกสมการต้องมี markdown อธิบายที่มา**ก่อน**เขียนโค้ด ไม่ implement สมการที่ยังไม่ได้อธิบาย
- ห้ามใช้วิธี "spawn subagent ทำทั้ง notebook ให้เสร็จในทีเดียว" เพราะขัดกับเป้าหมายที่ต้องเข้าใจไปพร้อมกัน — งาน implementation ต้องทำใน conversation หลักแบบ interactive เป็นหลัก
- เริ่มจาก `01_monte_carlo_simulation.ipynb` ก่อนเสมอ (เป็น base engine ที่ 02-03 ต่อยอด) ทำให้เสร็จและเข้าใจครบก่อนค่อยไปไฟล์ถัดไป
