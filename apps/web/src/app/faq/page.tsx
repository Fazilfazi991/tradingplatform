import type { Metadata } from "next";
import { PublicDoc } from "@/components/public-doc";
export const metadata: Metadata = { title: "FAQ", description: "Answers about Verified Edge demo data, predictions, abstention, evidence, and validation.", alternates: { canonical: "/faq" } };
const questions=[
  ["Is this live market data?","No. Public market and forecast values are synthetic unless explicitly marked otherwise."],
  ["Does Verified Edge tell me what to buy or sell?","No. It does not provide BUY/SELL calls, target prices, execution, or personalized advice."],
  ["Why are there seven engines?","Different evidence classes have different failure modes. Separation makes agreement and contradiction easier to inspect."],
  ["What does abstain mean?","The system does not have enough reliable, relevant, and sufficiently independent evidence to form a view."],
  ["Has the prediction engine been validated?","It passed a sealed historical holdout under a preregistered method. Prospective forward validation is still required."],
] as const;
export default function Faq(){return <PublicDoc path="/faq" title="Frequently asked questions" summary="Direct answers about the product’s current boundaries."><div className="faq-list">{questions.map(([question,answer])=><section key={question}><h2>{question}</h2><p>{answer}</p></section>)}</div></PublicDoc>}
