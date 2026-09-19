---
name: creating-financial-models
description: 高级财务建模套件，包含DCF估值、敏感性分析、蒙特卡洛模拟和场景规划。当用户需要对企业、项目或并购交易进行投资分析、股权估值、IRR/MOIC计算、WACC建模，或要求建立DCF模型、运行概率模拟、制作敏感性表格时，请主动使用此技能。
compatibility: 可选依赖 Python 3.9+（pandas、numpy、openpyxl）用于脚本输出；核心功能无需额外依赖
---

# Financial Modeling Suite

A comprehensive financial modeling toolkit for investment analysis, valuation, and risk assessment using industry-standard methodologies.

## Core Capabilities

### 1. Discounted Cash Flow (DCF) Analysis
- Build complete DCF models with multiple growth scenarios
- Calculate terminal values using perpetuity growth and exit multiple methods
- Determine weighted average cost of capital (WACC)
- Generate enterprise and equity valuations

### 2. Sensitivity Analysis
- Test key assumptions impact on valuation
- Create data tables for multiple variables
- Generate tornado charts for sensitivity ranking
- Identify critical value drivers

### 3. Monte Carlo Simulation
- Run thousands of scenarios with probability distributions
- Model uncertainty in key inputs
- Generate confidence intervals for valuations
- Calculate probability of achieving targets

### 4. Scenario Planning
- Build best/base/worst case scenarios
- Model different economic environments
- Test strategic alternatives
- Compare outcome probabilities

## Input Requirements

### For DCF Analysis
- Historical financial statements (3-5 years)
- Revenue growth assumptions
- Operating margin projections
- Capital expenditure forecasts
- Working capital requirements
- Terminal growth rate or exit multiple
- Discount rate components (risk-free rate, beta, market premium)

### For Sensitivity Analysis
- Base case model
- Variable ranges to test
- Key metrics to track

### For Monte Carlo Simulation
- Probability distributions for uncertain variables
- Correlation assumptions between variables
- Number of iterations (typically 1,000-10,000)

### For Scenario Planning
- Scenario definitions and assumptions
- Probability weights for scenarios
- Key performance indicators to track

## Output Formats

### DCF Model Output
- Complete financial projections
- Free cash flow calculations
- Terminal value computation
- Enterprise and equity value summary
- Valuation multiples implied
- Excel workbook with full model

### Sensitivity Analysis Output
- Sensitivity tables showing value ranges
- Tornado chart of key drivers
- Break-even analysis
- Charts showing relationships

### Monte Carlo Output
- Probability distribution of valuations
- Confidence intervals (e.g., 90%, 95%)
- Statistical summary (mean, median, std dev)
- Risk metrics (VaR, probability of loss)

### Scenario Planning Output
- Scenario comparison table
- Probability-weighted expected values
- Decision tree visualization
- Risk-return profiles

## Model Types Supported

1. **Corporate Valuation**
   - Mature companies with stable cash flows
   - Growth companies with J-curve projections
   - Turnaround situations

2. **Project Finance**
   - Infrastructure projects
   - Real estate developments
   - Energy projects

3. **M&A Analysis**
   - Acquisition valuations
   - Synergy modeling
   - Accretion/dilution analysis

4. **LBO Models**
   - Leveraged buyout analysis
   - Returns analysis (IRR, MOIC)
   - Debt capacity assessment

## Best Practices Applied

### Modeling Standards
- Consistent formatting and structure
- Clear assumption documentation
- Separation of inputs, calculations, outputs
- Error checking and validation
- Version control and change tracking

### Valuation Principles
- Use multiple valuation methods for triangulation
- Apply appropriate risk adjustments
- Consider market comparables
- Validate against trading multiples
- Document key assumptions clearly

### Risk Management
- Identify and quantify key risks
- Use probability-weighted scenarios
- Stress test extreme cases
- Consider correlation effects
- Provide confidence intervals

## Example Usage

"Build a DCF model for this technology company using the attached financials"

"Run a Monte Carlo simulation on this acquisition model with 5,000 iterations"

"Create sensitivity analysis showing impact of growth rate and WACC on valuation"

"Develop three scenarios for this expansion project with probability weights"

**示例输出格式（DCF 汇总）：**
| 指标 | 数值 |
|------|------|
| 企业价值（EV） | $450M |
| 净债务 | $80M |
| 股权价值 | $370M |
| 隐含 EV/EBITDA | 12.5x |

## Scripts Included

暂无可执行脚本。DCF 计算和敏感性分析由 Claude 直接以表格/代码块形式输出。
如需 Python 脚本版本，请在请求中注明，Claude 将即时生成。

## 注意事项

所有模型输出均基于用户提供的假设，不构成投资建议。重大决策前请结合专业判断。

## Quality Checks

The model automatically performs:
1. Balance sheet balancing checks
2. Cash flow reconciliation
3. Circular reference resolution
4. Sensitivity bound checking
5. Statistical validation of Monte Carlo results
