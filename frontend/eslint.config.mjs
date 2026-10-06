import nextCoreWebVitals from "eslint-config-next/core-web-vitals";
import nextTypeScript from "eslint-config-next/typescript";

/**
 * eslint-config-next 16 ships native flat configs, so these are spread directly
 * rather than wrapped in FlatCompat as they were under 15.
 */
const config = [
  ...nextCoreWebVitals,
  ...nextTypeScript,
  { ignores: [".next/**", "node_modules/**"] },
];

export default config;
