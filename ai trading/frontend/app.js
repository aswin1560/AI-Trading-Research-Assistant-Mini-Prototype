/**
 * app.js - State Machine and Workflow Controller for AI Trading Research Assistant
 * Manages Step 1 (Ask) -> Step 2 (Clarify) -> Step 3 (Define) -> Step 4 (Test)
 */

document.addEventListener("DOMContentLoaded", () => {
  // Global State
  let currentExperiment = null;
  let currentClarifications = {};
  let backtestResults = null;

  // DOM Elements - Stepper Navigation
  const stepNavs = {
    1: document.getElementById("step-nav-1"),
    2: document.getElementById("step-nav-2"),
    3: document.getElementById("step-nav-3"),
    4: document.getElementById("step-nav-4")
  };

  const stepViews = {
    1: document.getElementById("step-view-1"),
    2: document.getElementById("step-view-2"),
    3: document.getElementById("step-view-3"),
    4: document.getElementById("step-view-4")
  };

  // Step 1 Elements
  const queryInput = document.getElementById("query-input");
  const btnParseQuery = document.getElementById("btn-parse-query");
  const sampleChipsContainer = document.getElementById("sample-chips-container");

  // Step 2 Elements
  const gapsList = document.getElementById("gaps-list");
  const assumptionsList = document.getElementById("assumptions-list");
  const gapsCountBadge = document.getElementById("gaps-count-badge");
  const btnBackStep1 = document.getElementById("btn-back-step-1");
  const btnApplyClarifications = document.getElementById("btn-apply-clarifications");

  // Step 3 Elements
  const expInstrumentVal = document.getElementById("exp-instrument-val");
  const expTimeframeVal = document.getElementById("exp-timeframe-val");
  const expHypothesisVal = document.getElementById("exp-hypothesis-val");
  const expEntryVal = document.getElementById("exp-entry-val");
  const expEntryType = document.getElementById("exp-entry-type");
  const expFilterVal = document.getElementById("exp-filter-val");
  const expExitVal = document.getElementById("exp-exit-val");
  const expExitType = document.getElementById("exp-exit-type");
  const expHoldingVal = document.getElementById("exp-holding-val");
  const expRawQuery = document.getElementById("exp-raw-query");
  const expResolvedTags = document.getElementById("exp-resolved-tags");
  const btnEditClarifications = document.getElementById("btn-edit-clarifications");
  const btnRunTest = document.getElementById("btn-run-test");

  // Step 4 Elements
  const resTrades = document.getElementById("res-trades");
  const resWinRate = document.getElementById("res-win-rate");
  const resWinCount = document.getElementById("res-win-count");
  const resAvgReturn = document.getElementById("res-avg-return");
  const resDrawdown = document.getElementById("res-drawdown");
  const resSharpe = document.getElementById("res-sharpe");
  const resProfitFactor = document.getElementById("res-profit-factor");
  const equitySvg = document.getElementById("equity-svg");
  const epistemicDataList = document.getElementById("epistemic-data-list");
  const epistemicConclusionList = document.getElementById("epistemic-conclusion-list");
  const sensitivityTbody = document.getElementById("sensitivity-tbody");
  const biasGrid = document.getElementById("bias-grid");
  const btnExportJson = document.getElementById("btn-export-json");
  const btnNewTest = document.getElementById("btn-new-test");

  // ==================== WORKFLOW NAVIGATION ====================
  function setStep(stepNumber) {
    // Update navigation circles
    for (let i = 1; i <= 4; i++) {
      if (i < stepNumber) {
        stepNavs[i].className = "step-item completed";
      } else if (i === stepNumber) {
        stepNavs[i].className = "step-item active";
      } else {
        stepNavs[i].className = "step-item";
      }
      
      if (i === stepNumber) {
        stepViews[i].classList.remove("hidden");
        stepViews[i].classList.add("active-card");
      } else {
        stepViews[i].classList.add("hidden");
        stepViews[i].classList.remove("active-card");
      }
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // ==================== STEP 1: ASK ====================
  async function loadTemplates() {
    try {
      const resp = await fetch("/api/templates");
      if (resp.ok) {
        const templates = await resp.json();
        sampleChipsContainer.innerHTML = "";
        templates.forEach(t => {
          const chip = document.createElement("button");
          chip.className = "sample-chip";
          chip.textContent = t.title;
          chip.title = t.highlight;
          chip.addEventListener("click", () => {
            queryInput.value = t.query;
            btnParseQuery.click();
          });
          sampleChipsContainer.appendChild(chip);
        });
      }
    } catch (err) {
      console.warn("Could not load templates:", err);
    }
  }

  btnParseQuery.addEventListener("click", async () => {
    const question = queryInput.value.trim();
    if (!question) {
      alert("Please enter a research hypothesis or click one of the sample queries.");
      return;
    }

    btnParseQuery.disabled = true;
    btnParseQuery.innerHTML = `<span>Analyzing Gaps...</span>`;

    try {
      const resp = await fetch("/api/parse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question })
      });

      if (!resp.ok) {
        const errData = await resp.json();
        throw new Error(errData.detail || "Failed to parse question");
      }

      currentExperiment = await resp.json();
      currentClarifications = {};
      renderClarificationStep(currentExperiment);
      setStep(2);
    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      btnParseQuery.disabled = false;
      btnParseQuery.innerHTML = `
        <span>Extract & Detect Gaps</span>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
      `;
    }
  });

  // ==================== STEP 2: CLARIFY ====================
  function renderClarificationStep(exp) {
    gapsList.innerHTML = "";
    assumptionsList.innerHTML = "";

    const gaps = exp.gaps || [];
    gapsCountBadge.textContent = `${gaps.length} Gaps to Resolve`;

    gaps.forEach((gap, index) => {
      const card = document.createElement("div");
      card.className = "gap-card";

      const severityBadgeClass = gap.severity === "required" 
        ? "badge-danger" 
        : (gap.severity === "clarification" ? "badge-warning" : "badge-neutral");

      card.innerHTML = `
        <div class="gap-header">
          <span class="gap-field-name">${gap.field}</span>
          <span class="badge ${severityBadgeClass}">${gap.severity.toUpperCase()}</span>
        </div>
        <div class="gap-question">${gap.question}</div>
        <div class="gap-options-grid" id="options-grid-${index}"></div>
      `;

      const optionsGrid = card.querySelector(`#options-grid-${index}`);

      gap.suggested_options.forEach((opt, optIdx) => {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "option-chip";
        // Auto-select first option for quick testing if required
        if (optIdx === 0 && !currentClarifications[gap.field]) {
          chip.classList.add("selected");
          currentClarifications[gap.field] = opt;
        } else if (currentClarifications[gap.field] === opt) {
          chip.classList.add("selected");
        }

        chip.innerHTML = `<span>${opt}</span>`;
        chip.addEventListener("click", () => {
          // Remove selected from siblings
          optionsGrid.querySelectorAll(".option-chip").forEach(c => c.classList.remove("selected"));
          chip.classList.add("selected");
          currentClarifications[gap.field] = opt;
        });

        optionsGrid.appendChild(chip);
      });

      gapsList.appendChild(card);
    });

    // Render Conservative Assumptions
    (exp.assumptions || []).forEach(a => {
      const li = document.createElement("li");
      li.className = "assumption-item";
      li.innerHTML = `
        <span class="assumption-field">${a.field.replace("_", " ")}</span>
        <span class="assumption-val">${a.assumed_value}</span>
        <span class="assumption-reason">${a.reason}</span>
      `;
      assumptionsList.appendChild(li);
    });
  }

  btnBackStep1.addEventListener("click", () => setStep(1));

  btnApplyClarifications.addEventListener("click", async () => {
    btnApplyClarifications.disabled = true;
    btnApplyClarifications.textContent = "Confirming & Standardizing...";

    try {
      const resp = await fetch("/api/clarify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          experiment: currentExperiment,
          clarifications: currentClarifications
        })
      });

      if (!resp.ok) {
        throw new Error("Failed to apply clarifications");
      }

      currentExperiment = await resp.json();
      renderExperimentCard(currentExperiment);
      setStep(3);
    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      btnApplyClarifications.disabled = false;
      btnApplyClarifications.textContent = "Confirm & Build Experiment Card →";
    }
  });

  // ==================== STEP 3: DEFINE ====================
  function renderExperimentCard(exp) {
    expInstrumentVal.textContent = exp.instrument || "NIFTY";
    expTimeframeVal.textContent = (exp.timeframe || "Daily").toUpperCase();
    expHypothesisVal.textContent = exp.hypothesis || "Synthesizing research hypothesis...";

    expEntryVal.textContent = exp.entry.condition || "Not Specified";
    expEntryType.textContent = `Type: ${exp.entry.type || "price_drop"}`;

    const filterStrings = (exp.filters || []).map(f => `${f.name}: ${f.condition}`).join(" | ");
    expFilterVal.textContent = filterStrings || "None (Unfiltered)";

    expExitVal.textContent = exp.exit.condition || "Not Specified";
    expExitType.textContent = `Type: ${exp.exit.type || "time"}`;

    if (exp.holding_period && exp.holding_period.value) {
      expHoldingVal.textContent = `${exp.holding_period.value} ${exp.holding_period.unit || "days"}`;
    } else {
      expHoldingVal.textContent = "5 days (Default)";
    }

    expRawQuery.textContent = `"${exp.raw_question}"`;

    expResolvedTags.innerHTML = "";
    (exp.ambiguous_terms || []).forEach(term => {
      const tag = document.createElement("span");
      tag.className = "badge badge-glow";
      tag.textContent = `Resolved: "${term}"`;
      expResolvedTags.appendChild(tag);
    });
  }

  btnEditClarifications.addEventListener("click", () => setStep(2));

  btnRunTest.addEventListener("click", async () => {
    btnRunTest.disabled = true;
    btnRunTest.innerHTML = `<span>Simulating 10-Year Regimes...</span>`;

    try {
      const resp = await fetch("/api/backtest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          experiment: currentExperiment,
          sample_period_years: 10,
          transaction_cost_pct: 0.05,
          slippage_pct: 0.02
        })
      });

      if (!resp.ok) {
        throw new Error("Simulation failed");
      }

      backtestResults = await resp.json();
      renderTestResults(backtestResults);
      setStep(4);
    } catch (err) {
      alert("Error during backtest: " + err.message);
    } finally {
      btnRunTest.disabled = false;
      btnRunTest.innerHTML = `
        <span>Execute 10-Year Backtest (2015–2024)</span>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
      `;
    }
  });

  // ==================== STEP 4: TEST & ANALYZE ====================
  function renderTestResults(data) {
    const summary = data.summary;

    resTrades.textContent = summary.total_trades;
    resWinRate.textContent = `${summary.win_rate}%`;
    resWinCount.textContent = `${summary.winning_trades} wins / ${summary.losing_trades} losses`;
    
    const sign = summary.avg_return_pct >= 0 ? "+" : "";
    resAvgReturn.textContent = `${sign}${summary.avg_return_pct}%`;
    resAvgReturn.className = summary.avg_return_pct >= 0 ? "metric-value text-emerald" : "metric-value text-rose";

    resDrawdown.textContent = `-${summary.max_drawdown_pct}%`;
    resSharpe.textContent = summary.sharpe_ratio;
    resProfitFactor.textContent = `Profit Factor: ${summary.profit_factor}`;

    // Render SVG Equity Curve
    drawEquityCurve(data.equity_curve);

    // Render Epistemic Analysis: What Data Shows vs What We Conclude
    epistemicDataList.innerHTML = "";
    (data.epistemic_analysis.what_data_shows || []).forEach(item => {
      const li = document.createElement("li");
      li.textContent = item;
      epistemicDataList.appendChild(li);
    });

    epistemicConclusionList.innerHTML = "";
    (data.epistemic_analysis.what_we_conclude || []).forEach(item => {
      const li = document.createElement("li");
      li.textContent = item;
      epistemicConclusionList.appendChild(li);
    });

    // Render Recommended Next Steps (Page 9 Requirement)
    const recommendedNextContainer = document.getElementById("recommended-next-container");
    if (recommendedNextContainer) {
      recommendedNextContainer.innerHTML = "";
      (data.epistemic_analysis.recommended_next_steps || []).forEach(stepText => {
        const chip = document.createElement("button");
        chip.className = "sample-chip";
        chip.style.borderColor = "rgba(56, 189, 248, 0.4)";
        chip.textContent = stepText;
        chip.addEventListener("click", () => {
          queryInput.value = stepText;
          setStep(1);
          btnParseQuery.click();
        });
        recommendedNextContainer.appendChild(chip);
      });
    }

    // Render Parameter Sensitivity Table
    sensitivityTbody.innerHTML = "";
    (data.sensitivity || []).forEach(s => {
      const tr = document.createElement("tr");
      const isProfitable = s.avg_return > 0;
      const robustLabel = s.trades >= 25 && isProfitable ? "Stable Sample" : (s.trades < 15 ? "Insufficient Sample" : "Marginal");
      const badgeClass = robustLabel === "Stable Sample" ? "badge-success" : (robustLabel === "Marginal" ? "badge-warning" : "badge-danger");

      tr.innerHTML = `
        <td><strong>${s.drop_threshold}</strong></td>
        <td>${s.trades} trades</td>
        <td>${s.win_rate}%</td>
        <td class="${isProfitable ? 'text-emerald' : 'text-rose'} font-bold">${s.avg_return >= 0 ? '+' : ''}${s.avg_return}%</td>
        <td><span class="badge ${badgeClass}">${robustLabel}</span></td>
      `;
      sensitivityTbody.appendChild(tr);
    });

    // Render Pre-Mortem Bias Warnings
    biasGrid.innerHTML = "";
    (data.bias_warnings || []).forEach(b => {
      const div = document.createElement("div");
      div.className = "bias-card";
      div.innerHTML = `
        <span class="bias-type">${b.type}</span>
        <p class="bias-desc">${b.description}</p>
        <div class="bias-mitigation"><strong>Mitigation:</strong> ${b.mitigation}</div>
      `;
      biasGrid.appendChild(div);
    });
  }

  // ==================== RESEARCH MEMORY (PAGE 1 & 9) ====================
  const btnToggleMemory = document.getElementById("btn-toggle-memory");
  const memoryModal = document.getElementById("memory-modal");
  const btnCloseMemory = document.getElementById("btn-close-memory");
  const memoryEntriesList = document.getElementById("memory-entries-list");
  const memoryCounterText = document.getElementById("memory-counter-text");
  const btnSaveMemory = document.getElementById("btn-save-memory");

  function getSavedMemory() {
    try {
      return JSON.parse(localStorage.getItem("ai_trading_memory") || "[]");
    } catch {
      return [];
    }
  }

  function updateMemoryCounter() {
    const memory = getSavedMemory();
    if (memoryCounterText) {
      memoryCounterText.textContent = `Research Memory (${memory.length})`;
    }
  }

  function renderMemoryModal() {
    const memory = getSavedMemory();
    memoryEntriesList.innerHTML = "";
    if (memory.length === 0) {
      memoryEntriesList.innerHTML = `<p style="color: var(--text-muted); text-align: center; padding: 24px;">No experiments saved yet. Run a backtest in Step 4 and click 'Save to Research Memory'.</p>`;
      return;
    }

    memory.forEach((item, idx) => {
      const card = document.createElement("div");
      card.style.background = "var(--bg-input)";
      card.style.border = "1px solid var(--border-subtle)";
      card.style.borderRadius = "var(--radius-md)";
      card.style.padding = "16px";
      card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
          <span style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--accent-cyan);">${item.date}</span>
          <span class="badge badge-success">${item.win_rate}% Win Rate (${item.trades} Trades)</span>
        </div>
        <div style="font-weight: 700; color: #fff; margin-bottom: 6px; font-size: 0.95rem;">${item.hypothesis}</div>
        <div style="font-size: 0.82rem; color: var(--text-secondary); margin-bottom: 8px;"><strong>Takeaway:</strong> ${item.takeaway}</div>
        <div style="font-size: 0.78rem; color: var(--text-muted);"><strong>Parameters:</strong> ${item.parameters}</div>
      `;
      memoryEntriesList.appendChild(card);
    });
  }

  function openMemoryModal() {
    renderMemoryModal();
    if (memoryModal) {
      memoryModal.classList.remove("hidden");
      memoryModal.style.display = "flex";
    }
  }

  function closeMemoryModal() {
    if (memoryModal) {
      memoryModal.classList.add("hidden");
      memoryModal.style.display = "none";
    }
  }

  if (btnToggleMemory) {
    btnToggleMemory.addEventListener("click", openMemoryModal);
  }

  if (btnCloseMemory) {
    btnCloseMemory.addEventListener("click", closeMemoryModal);
  }

  // Close when clicking on backdrop outside the modal dialog
  if (memoryModal) {
    memoryModal.addEventListener("click", (e) => {
      if (e.target === memoryModal) {
        closeMemoryModal();
      }
    });
  }

  // Close when pressing the Escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && memoryModal && !memoryModal.classList.contains("hidden")) {
      closeMemoryModal();
    }
  });

  if (btnSaveMemory) {
    btnSaveMemory.addEventListener("click", () => {
      if (!currentExperiment || !backtestResults) return;
      const memory = getSavedMemory();
      const newEntry = {
        id: Date.now(),
        date: new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" }),
        hypothesis: currentExperiment.hypothesis || "Tested Trading Hypothesis",
        trades: backtestResults.summary.total_trades,
        win_rate: backtestResults.summary.win_rate,
        takeaway: backtestResults.epistemic_analysis.what_we_conclude[0] || "Tested under 10-year regime.",
        parameters: `${currentExperiment.instrument || 'NIFTY'} | ${currentExperiment.entry.condition || 'Drop'} | Hold ${currentExperiment.holding_period.value || 5} days`
      };
      memory.unshift(newEntry);
      localStorage.setItem("ai_trading_memory", JSON.stringify(memory));
      updateMemoryCounter();
      alert("✓ Experiment saved to Research Memory! Click 'Research Memory' in the top navigation to view.");
    });
  }

  updateMemoryCounter();

  function drawEquityCurve(points) {
    if (!points || points.length === 0) return;

    const width = 900;
    const height = 240;
    const padding = { top: 20, right: 30, bottom: 30, left: 60 };

    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    // Find min and max equity
    const allValues = [];
    points.forEach(p => {
      allValues.push(p.strategy_equity);
      allValues.push(p.benchmark_equity);
    });

    const minVal = Math.min(...allValues) * 0.95;
    const maxVal = Math.max(...allValues) * 1.05;

    function getX(i) {
      return padding.left + (i / (points.length - 1)) * chartW;
    }

    function getY(val) {
      return padding.top + chartH - ((val - minVal) / (maxVal - minVal)) * chartH;
    }

    // Build Strategy Path
    let stratPath = `M ${getX(0)} ${getY(points[0].strategy_equity)}`;
    let stratArea = `M ${getX(0)} ${getY(points[0].strategy_equity)}`;
    for (let i = 1; i < points.length; i++) {
      stratPath += ` L ${getX(i)} ${getY(points[i].strategy_equity)}`;
      stratArea += ` L ${getX(i)} ${getY(points[i].strategy_equity)}`;
    }
    stratArea += ` L ${getX(points.length - 1)} ${padding.top + chartH} L ${getX(0)} ${padding.top + chartH} Z`;

    // Build Benchmark Path
    let benchPath = `M ${getX(0)} ${getY(points[0].benchmark_equity)}`;
    for (let i = 1; i < points.length; i++) {
      benchPath += ` L ${getX(i)} ${getY(points[i].benchmark_equity)}`;
    }

    // Horizontal Grid Lines
    const gridLines = 4;
    let gridSvg = "";
    for (let g = 0; g <= gridLines; g++) {
      const gVal = minVal + (g / gridLines) * (maxVal - minVal);
      const gY = getY(gVal);
      gridSvg += `
        <line x1="${padding.left}" y1="${gY}" x2="${width - padding.right}" y2="${gY}" stroke="rgba(255,255,255,0.06)" stroke-dasharray="3,3" />
        <text x="${padding.left - 10}" y="${gY + 4}" fill="#64748b" font-size="10" font-family="JetBrains Mono" text-anchor="end">₹${Math.round(gVal).toLocaleString()}</text>
      `;
    }

    // Date Axis labels (Start, Mid, End)
    const startDate = points[0].date.split("-")[0];
    const midDate = points[Math.floor(points.length / 2)].date.split("-")[0];
    const endDate = points[points.length - 1].date.split("-")[0];

    const axisSvg = `
      <text x="${padding.left}" y="${height - 8}" fill="#64748b" font-size="11" font-family="JetBrains Mono">${startDate}</text>
      <text x="${width / 2}" y="${height - 8}" fill="#64748b" font-size="11" font-family="JetBrains Mono" text-anchor="middle">${midDate}</text>
      <text x="${width - padding.right}" y="${height - 8}" fill="#64748b" font-size="11" font-family="JetBrains Mono" text-anchor="end">${endDate}</text>
    `;

    equitySvg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    equitySvg.innerHTML = `
      <defs>
        <linearGradient id="stratGlow" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.35"/>
          <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.0"/>
        </linearGradient>
      </defs>
      ${gridSvg}
      <path d="${stratArea}" fill="url(#stratGlow)" />
      <path d="${benchPath}" fill="none" stroke="#64748b" stroke-width="1.8" stroke-dasharray="4,4" />
      <path d="${stratPath}" fill="none" stroke="#38bdf8" stroke-width="2.5" />
      ${axisSvg}
    `;
  }

  // Export JSON
  btnExportJson.addEventListener("click", () => {
    if (!currentExperiment) return;
    const exportData = {
      experiment: currentExperiment,
      simulation_results: backtestResults ? backtestResults.summary : null,
      exported_at: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `experiment_${currentExperiment.instrument || 'nifty'}_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  });

  btnNewTest.addEventListener("click", () => {
    queryInput.value = "";
    setStep(1);
  });

  // Load sample templates on launch
  loadTemplates();
});
