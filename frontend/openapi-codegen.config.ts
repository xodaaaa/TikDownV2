import { defineConfig } from "openapi-typescript";

export default defineConfig({
  schema: "http://localhost:8000/openapi.json",
  output: "src/types/index.ts",
  exportType: "type",
  propertiesRequired: true,
  emptyObjectsUnknown: true,
});
