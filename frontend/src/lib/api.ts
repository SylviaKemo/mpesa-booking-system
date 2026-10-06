/**
 * The booking API.
 *
 * Shapes mirror the FastAPI schemas, snake_case included, so a field rename on
 * either side shows up here as a type error rather than as undefined at runtime.
 */

/**
 * In the browser: same origin, because next.config rewrites /api/* to the API.
 * Nothing about the API host reaches the bundle, so one build runs anywhere.
 *
 * On the server: an absolute URL, since fetch has no origin to be relative to.
 * Read at request time, so a deployment can repoint it without rebuilding.
 */
const BASE_URL =
  typeof window === "undefined"
    ? (process.env.API_URL ?? "http://localhost:8000")
    : "";

export type Tier = {
  id: string;
  label: string;
  /** Whole Kenyan shillings. */
  amount_kes: number;
  minutes: number;
  note: string | null;
};

export type LashSet = {
  id: string;
  name: string;
  blurb: string;
  image_url: string;
  image_alt: string;
  tiers: Tier[];
};

export type Addition = {
  id: string;
  label: string;
  amount_kes: number;
  minutes: number;
};

export type AdditionsCard = {
  name: string;
  blurb: string;
  image_url: string;
  image_alt: string;
};

export type Catalogue = {
  sets: LashSet[];
  additions: Addition[];
  additions_card: AdditionsCard;
};

export type Slot = {
  key: string;
  label: string;
  available: boolean;
};

export type Availability = {
  date: string;
  slots: Slot[];
};

export type PaymentMethod = "mpesa" | "studio";

export type BookingStatus =
  | "pending_payment"
  | "confirmed"
  | "expired"
  | "cancelled";

export type Payment = {
  status: "pending" | "succeeded" | "failed" | "orphaned";
  amount_kes: number;
  mpesa_receipt: string | null;
  result_desc: string | null;
};

/** What the lookup returns — no personal data, by design. */
export type BookingStatusResponse = {
  reference: string;
  booking_date: string;
  slot_key: string;
  status: BookingStatus;
  payment_method: PaymentMethod;
  amount_kes: number;
  deposit_kes: number;
  minutes: number;
  hold_expires_at: string | null;
  payments: Payment[];
};

export type Booking = BookingStatusResponse & {
  customer_name: string;
  customer_phone: string;
  notes: string | null;
};

export type BookingRequest = {
  tier_id: string;
  addition_ids: string[];
  booking_date: string;
  slot_key: string;
  name: string;
  phone: string;
  notes: string | null;
  payment_method: PaymentMethod;
};

/**
 * An API call that failed in a way worth showing someone.
 *
 * `reference` is set when the booking was made but its M-Pesa prompt was not:
 * the slot is held, and the client needs that reference to carry on.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly reference?: string;

  constructor(message: string, status: number, reference?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.reference = reference;
  }
}

type StructuredDetail = { message?: string; reference?: string; reason?: string };
/** FastAPI returns a list of these when a request fails schema validation. */
type ValidationItem = { loc?: unknown[]; msg?: string };
type Detail = string | StructuredDetail | ValidationItem[];

function readDetail(body: unknown, fallback: string): Detail {
  if (body && typeof body === "object" && "detail" in body) {
    return (body as { detail: Detail }).detail;
  }
  return fallback;
}

/**
 * Turn FastAPI's validation list into something a person can act on.
 *
 * Without this every schema failure — a field too long, a malformed date, an
 * unknown payment method — reads as a generic error on the one screen where
 * the client could have fixed it.
 */
function describeValidation(items: ValidationItem[]): string {
  const messages = items
    .map((item) => {
      // loc is ["body", "phone"]; the field name is the part worth showing.
      const field = Array.isArray(item.loc) ? item.loc.at(-1) : undefined;
      const msg = item.msg ?? "is not valid";
      return typeof field === "string" && field !== "body"
        ? `${field}: ${msg}`
        : msg;
    })
    .filter(Boolean);

  return messages.length ? messages.join("; ") : "Please check the details.";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      // The catalogue and availability change independently of any build.
      cache: "no-store",
      ...init,
    });
  } catch {
    // A network failure reads as "server down" to anyone looking at it.
    throw new ApiError("Could not reach the booking service.", 0);
  }

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    const detail = readDetail(body, response.statusText);

    if (typeof detail === "string") {
      throw new ApiError(detail, response.status);
    }
    if (Array.isArray(detail)) {
      throw new ApiError(describeValidation(detail), response.status);
    }
    throw new ApiError(
      detail.message ?? "Something went wrong.",
      response.status,
      detail.reference,
    );
  }

  return body as T;
}

export function getCatalogue(): Promise<Catalogue> {
  return request<Catalogue>("/api/catalogue");
}

export function getAvailability(isoDate: string): Promise<Availability> {
  return request<Availability>(`/api/availability?date=${isoDate}`);
}

export function createBooking(payload: BookingRequest): Promise<Booking> {
  return request<Booking>("/api/bookings", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getBooking(reference: string): Promise<BookingStatusResponse> {
  return request<BookingStatusResponse>(`/api/bookings/${reference}`);
}
