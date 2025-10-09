let date = require("moment")().format("YYYYMMDD");
let commit;

try {
  commit = require("child_process")
    .execSync("git rev-parse HEAD", {
      stdio: ["pipe", "pipe", "ignore"]
    })
    .toString()
    .slice(0, 5);
} catch (e) {
  commit = "dev";
}

let version = `"${date}-${commit}"`; // 双引号包裹版本号

console.log(`current version is ${version}`);

module.exports = {
  NODE_ENV: '"development"', // 关键：用双引号包裹，且外层用单引号
  VERSION: version,
  USE_SENTRY: '"0"' // 数值也用双引号包裹为字符串
};
