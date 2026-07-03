import { createClient } from "openapi-typescript";
import { writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import config from "../openapi-codegen.config.ts";

const schemaUrl = config.schema ?? "http://localhost:8000/openapi.json";
const outputPath = resolve(import.meta.dirname!, "..", config.output ?? "src/types/index.ts");

const { data } = await createClient(schemaUrl, {
  exportType: config.exportType,
  propertiesRequired: config.propertiesRequired,
  emptyObjectsUnknown: config.emptyObjectsUnknown,
});

await writeFile(outputPath, data, "utf-8");
console.log(`Types generated: ${outputPath}`);
