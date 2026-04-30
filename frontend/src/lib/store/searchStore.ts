import { create } from "zustand";

interface SearchState {
  origin: string;
  destination: string;
  departureDate: string;
  returnDate: string;
  cabinClass: string;
  nonstopOnly: boolean;
  setOrigin: (v: string) => void;
  setDestination: (v: string) => void;
  setDepartureDate: (v: string) => void;
  setReturnDate: (v: string) => void;
  setCabinClass: (v: string) => void;
  setNonstopOnly: (v: boolean) => void;
}

export const useSearchStore = create<SearchState>((set) => ({
  origin:        "",
  destination:   "",
  departureDate: "",
  returnDate:    "",
  cabinClass:    "ECONOMY",
  nonstopOnly:   false,
  setOrigin:        (v) => set({ origin: v }),
  setDestination:   (v) => set({ destination: v }),
  setDepartureDate: (v) => set({ departureDate: v }),
  setReturnDate:    (v) => set({ returnDate: v }),
  setCabinClass:    (v) => set({ cabinClass: v }),
  setNonstopOnly:   (v) => set({ nonstopOnly: v }),
}));
