"use client";

import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  encodeScenario,
  modelMonthly,
  NO_OPT,
  type ModelPrice,
  type Optimization,
  type Workload,
} from "@/lib/cost";

const usd = (n: number) =>
  n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

function NumberField(props: {
  label: string;
  value: number;
  onChange: (n: number) => void;
}) {
  return (
    <label style={{ display: "block", marginBottom: ".6rem" }}>
      <span style={{ fontSize: 13, color: "#555" }}>{props.label}</span>
      <input
        type="number"
        min={0}
        value={props.value}
        onChange={(e) => props.onChange(Math.max(0, Number(e.target.value)))}
        style={{ display: "block", width: "100%", padding: ".4rem", marginTop: 2 }}
      />
    </label>
  );
}

function Slider(props: {
  label: string;
  value: number;
  max: number;
  onChange: (n: number) => void;
}) {
  return (
    <label style={{ display: "block", marginBottom: ".6rem" }}>
      <span style={{ fontSize: 13, color: "#555" }}>
        {props.label}: {Math.round(props.value * 100)}%
      </span>
      <input
        type="range"
        min={0}
        max={props.max}
        step={0.05}
        value={props.value}
        onChange={(e) => props.onChange(Number(e.target.value))}
        style={{ display: "block", width: "100%" }}
      />
    </label>
  );
}

function Card(props: { label: string; value: string; color?: string }) {
  return (
    <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: ".8rem 1.1rem", minWidth: 160 }}>
      <div style={{ fontSize: 12, color: "#666" }}>{props.label}</div>
      <div style={{ fontSize: 26, fontWeight: 600, color: props.color ?? "#1a1a1a" }}>
        {props.value}
      </div>
    </div>
  );
}

export default function Calculator({
  models,
  asOf,
}: {
  models: ModelPrice[];
  asOf: string;
}) {
  const [tokensIn, setTokensIn] = useState(2000);
  const [tokensOut, setTokensOut] = useState(500);
  const [requests, setRequests] = useState(1_000_000);
  const [modelId, setModelId] = useState(models[0].id);
  const [cacheHit, setCacheHit] = useState(0.3);
  const [inputReduction, setInputReduction] = useState(0.2);
  const [shared, setShared] = useState("");

  const wl: Workload = {
    tokens_in: tokensIn,
    tokens_out: tokensOut,
    requests_per_month: requests,
  };
  const opt: Optimization = {
    cache_hit_rate: cacheHit,
    cache_read_multiplier: 0.1,
    input_reduction: inputReduction,
  };

  const model = models.find((m) => m.id === modelId) ?? models[0];

  const { baseline, optimized, comparison } = useMemo(() => {
    const baseline = modelMonthly(model, wl, NO_OPT);
    const optimized = modelMonthly(model, wl, opt);
    const comparison = models
      .map((m) => ({ name: m.display_name, monthly: Math.round(modelMonthly(m, wl, opt)) }))
      .sort((a, b) => a.monthly - b.monthly);
    return { baseline, optimized, comparison };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [model, tokensIn, tokensOut, requests, cacheHit, inputReduction]);

  const savingsPct = baseline ? Math.round((1 - optimized / baseline) * 100) : 0;

  function share() {
    const token = encodeScenario({ model_id: modelId, workload: wl, optimization: opt });
    setShared(`?s=${token}`);
  }

  return (
    <div>
      <div style={{ display: "flex", gap: "2rem", flexWrap: "wrap" }}>
        <div style={{ flex: "1 1 280px" }}>
          <h3>Workload</h3>
          <NumberField label="Input tokens / request" value={tokensIn} onChange={setTokensIn} />
          <NumberField label="Output tokens / request" value={tokensOut} onChange={setTokensOut} />
          <NumberField label="Requests / month" value={requests} onChange={setRequests} />
          <label style={{ display: "block", marginBottom: ".6rem" }}>
            <span style={{ fontSize: 13, color: "#555" }}>Primary model</span>
            <select
              value={modelId}
              onChange={(e) => setModelId(e.target.value)}
              style={{ display: "block", width: "100%", padding: ".4rem", marginTop: 2 }}
            >
              {models.map((m) => (
                <option key={m.id} value={m.id}>{m.display_name}</option>
              ))}
            </select>
          </label>
        </div>

        <div style={{ flex: "1 1 280px" }}>
          <h3>Optimizations</h3>
          <Slider label="Semantic cache hit rate" value={cacheHit} max={1} onChange={setCacheHit} />
          <Slider label="Prompt compression" value={inputReduction} max={0.8} onChange={setInputReduction} />
          <button onClick={share} style={{ padding: ".5rem 1rem", marginTop: ".5rem", cursor: "pointer" }}>
            Share scenario
          </button>
          {shared && (
            <p style={{ fontSize: 12, wordBreak: "break-all", color: "#555" }}>{shared}</p>
          )}
        </div>
      </div>

      <section style={{ display: "flex", gap: "1rem", flexWrap: "wrap", margin: "1.5rem 0" }}>
        <Card label="Baseline / month" value={usd(baseline)} />
        <Card label="Optimized / month" value={usd(optimized)} color="#2563eb" />
        <Card
          label="Savings"
          value={`${savingsPct}%`}
          color={savingsPct > 0 ? "#0a7d28" : "#666"}
        />
      </section>

      <h3>Optimized monthly cost by model (as of {asOf})</h3>
      <ResponsiveContainer width="100%" height={340}>
        <BarChart data={comparison} layout="vertical" margin={{ left: 40, right: 24 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" tickFormatter={(v) => usd(Number(v))} />
          <YAxis type="category" dataKey="name" width={140} />
          <Tooltip formatter={(v) => usd(Number(v))} />
          <Bar dataKey="monthly" fill="#2563eb" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
