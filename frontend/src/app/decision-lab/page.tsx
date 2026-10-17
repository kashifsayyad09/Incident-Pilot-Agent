import { Suspense } from "react";
import DecisionLab from "./DecisionLab";
import { Loading } from "@/components/ui";

export default function Page() {
  return (
    <Suspense fallback={<Loading />}>
      <DecisionLab />
    </Suspense>
  );
}
