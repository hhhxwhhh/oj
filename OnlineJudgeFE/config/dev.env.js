let date = require("moment")().format("YYYYMMDD");
let commit;

// 尝试执行 git 命令，失败时使用默认值
try {
  commit = require("child_process")
    .execSync("git rev-parse HEAD", {
      stdio: ["pipe", "pipe", "ignore"],
    })
    .toString()
    .slice(0, 5);
} catch (e) {
  commit = "dev";
}

let version = `'${date}-${commit}'`;

console.log(`current version is ${version}`);

module.exports = {
  NODE_ENV: "development",
  VERSION: version,
  USE_SENTRY: "0",
};
