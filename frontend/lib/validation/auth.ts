import { z } from "zod";

// Mirrors app/auth/schemas.py (RegisterRequest: password min_length=8,
// max_length=72) - client-side validation is just UX, the backend is
// authoritative and re-validates regardless.
export const registerSchema = z.object({
  email: z.email("Enter a valid email address"),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters")
    .max(72, "Password must be at most 72 characters"),
});

export const loginSchema = z.object({
  email: z.email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

export type RegisterFormValues = z.infer<typeof registerSchema>;
export type LoginFormValues = z.infer<typeof loginSchema>;
