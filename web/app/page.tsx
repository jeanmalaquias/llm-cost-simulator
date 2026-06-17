import catalog from "@/data/catalog.json";
import Calculator from "./Calculator";
import type { ModelPrice } from "@/lib/cost";

export default function Page() {
  const models = catalog.models as ModelPrice[];
  return (
    <main style={{ maxWidth: 960, margin: "0 auto" }}>
      <h1>LLM Cost Simulator</h1>
      <p style={{ color: "#555" }}>
        Estimate and optimize inference cost. Prices as of{" "}
        <strong>{catalog.as_of}</strong> — indicative list prices; verify against
        each provider before deciding.
      </p>
      <Calculator models={models} asOf={catalog.as_of} />
      <p style={{ color: "#888", fontSize: 13, marginTop: "2rem" }}>
        {catalog.disclaimer}
      </p>
    </main>
  );
}
