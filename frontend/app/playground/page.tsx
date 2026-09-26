import { redirect } from "next/navigation";

export default function PlaygroundRoute() {
  redirect("/models?tab=playground");
}
