"use client";

import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";

gsap.registerPlugin(useGSAP, ScrollTrigger);

export { gsap, ScrollTrigger, useGSAP };

/** Full-motion media query; reduced-motion users get the final state with no tweens. */
export const MM_FULL = "(prefers-reduced-motion: no-preference)";
