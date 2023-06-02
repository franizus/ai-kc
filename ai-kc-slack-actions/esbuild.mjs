import * as esbuild from "esbuild";

await esbuild.build({
    entryPoints: [
        "./src/Handler/Handler.ts",
        "./src/Handler/SlackResponse.ts",
    ],
    entryNames: "[dir]/[name]/[name]",
    bundle: true,
    minify: true,
    sourcemap: false,
    target: "node16",
    platform: "node",
    outdir: "bin",
    external: ["aws-sdk"]
});