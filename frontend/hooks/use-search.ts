"use client";

import { useMutation } from "@tanstack/react-query";

import { searchApi } from "@/lib/api/search";

export function useSearch() {
  return useMutation({ mutationFn: searchApi.search });
}
