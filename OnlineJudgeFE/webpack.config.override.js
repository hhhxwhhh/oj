const path = require('path');

module.exports = {
  resolve: {
    modules: [
      path.resolve(__dirname, "node_modules"),
      path.resolve(__dirname, "."),
      "node_modules"
    ],
    alias: {
      "simple-module": path.resolve(__dirname, "simple-module"),
      "simple-hotkeys": path.resolve(__dirname, "simple-hotkeys"),
      "simple-uploader": path.resolve(__dirname, "simple-uploader")
    }
  }
};
