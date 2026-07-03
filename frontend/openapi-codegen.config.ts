import type { ClientOptions } from "openapi-typescript";

export interface CodegenConfig extends ClientOptions {
  schema: string;
  output: string;
}

const config: CodegenConfig = {
  schema: "http://localhost:8000/openapi.json",
  output: "src/types/index.ts",
  exportType: "type",
  propertiesRequired: true,
  emptyObjectsUnknown: true,
};

export default config;
